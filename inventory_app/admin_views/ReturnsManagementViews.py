from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, models
from decimal import Decimal
from ..models import Order, OrderItem, OrderReturn, ReturnItem, Inventory
from ..serializers import OrderReturnSerializer, ReturnItemSerializer


class ReturnsManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing returns and refunds"""
    queryset = OrderReturn.objects.all().select_related('original_order__customer', 'processed_by').order_by('-return_date')
    serializer_class = OrderReturnSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get list of all returns with filtering options"""
        returns = self.get_queryset()
        
        # Apply filters
        status_filter = request.GET.get('status')
        if status_filter:
            returns = returns.filter(status=status_filter)
            
        reason_filter = request.GET.get('reason')
        if reason_filter:
            returns = returns.filter(reason=reason_filter)
            
        search = request.GET.get('search')
        if search:
            returns = returns.filter(
                models.Q(id__icontains=search) |
                models.Q(original_order__id__icontains=search) |
                models.Q(original_order__customer__name__icontains=search)
            )
            
        serializer = self.get_serializer(returns, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_return(self, request):
        """Create a new return for an order"""
        try:
            with transaction.atomic():
                order_id = request.data.get('order_id')
                reason = request.data.get('reason')
                notes = request.data.get('notes', '')
                return_items_data = request.data.get('return_items', [])
                processing_fee = Decimal(str(request.data.get('processing_fee', '0.00')))
                
                # Validate order exists
                order = get_object_or_404(Order, id=order_id)
                
                # Create return order
                return_order = OrderReturn.objects.create(
                    original_order=order,
                    reason=reason,
                    notes=notes,
                    processing_fee=processing_fee,
                    status='pending'
                )
                
                total_return_amount = Decimal('0.00')
                
                # Create return items
                for item_data in return_items_data:
                    order_item_id = item_data.get('order_item_id')
                    return_quantity = int(item_data.get('return_quantity', 0))
                    condition = item_data.get('condition', 'good')
                    refund_per_unit = Decimal(str(item_data.get('refund_per_unit', '0.00')))
                    
                    # Validate order item
                    order_item = get_object_or_404(OrderItem, id=order_item_id, order=order)
                    
                    # Check return quantity doesn't exceed ordered quantity
                    already_returned = ReturnItem.objects.filter(
                        order_item=order_item,
                        return_order__status__in=['approved', 'completed']
                    ).aggregate(total=models.Sum('return_quantity'))['total'] or 0
                    
                    available_quantity = order_item.quantity - already_returned
                    if return_quantity > available_quantity:
                        return Response({
                            'error': f'Cannot return {return_quantity} items. Only {available_quantity} available for return.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create return item
                    return_item = ReturnItem.objects.create(
                        return_order=return_order,
                        order_item=order_item,
                        return_quantity=return_quantity,
                        condition=condition,
                        refund_per_unit=refund_per_unit
                    )
                    
                    # Update OrderItem.is_return field when return is created
                    # Mark as returned if any quantity is being returned
                    if return_quantity > 0:
                        order_item.is_return = True
                        order_item.save()
                        print(f"DEBUG: Updated OrderItem {order_item.id} is_return to True (return created)")
                    
                    total_return_amount += return_item.total_refund
                
                # Update return order totals
                return_order.total_return_amount = total_return_amount
                return_order.refund_amount = total_return_amount - processing_fee
                return_order.save()
                
                serializer = self.get_serializer(return_order)
                return Response({
                    'message': 'Return created successfully',
                    'return': serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': f'Failed to create return: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve_return(self, request, pk=None):
        """Approve a return and process refund"""
        try:
            with transaction.atomic():
                return_order = self.get_object()
                
                if return_order.status != 'pending':
                    return Response({
                        'error': 'Only pending returns can be approved'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update return status
                return_order.status = 'approved'
                return_order.processed_by = request.user
                return_order.processed_at = timezone.now()
                return_order.save()
                
                # Update inventory for returned items and sync return status
                for return_item in return_order.return_items.all():
                    if return_item.condition in ['good', 'unopened']:
                        # Add back to inventory only if item is in good condition
                        inventory, created = Inventory.objects.get_or_create(
                            variant=return_item.order_item.variant
                        )
                        inventory.quantity += return_item.return_quantity
                        inventory.save()
                    
                    # Sync OrderItem.is_return field based on actual return records
                    order_item = return_item.order_item
                    order_item.update_return_status()
                
                # Update order's return amount
                return_order.original_order.update_return_amount()
                
                serializer = self.get_serializer(return_order)
                return Response({
                    'message': 'Return approved successfully',
                    'return': serializer.data
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': f'Failed to approve return: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject_return(self, request, pk=None):
        """Reject a return request"""
        try:
            return_order = self.get_object()
            
            if return_order.status != 'pending':
                return Response({
                    'error': 'Only pending returns can be rejected'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            rejection_reason = request.data.get('rejection_reason', '')
            
            return_order.status = 'rejected'
            return_order.processed_by = request.user
            return_order.processed_at = timezone.now()
            return_order.notes = f"{return_order.notes}\n\nRejection Reason: {rejection_reason}".strip()
            return_order.save()
            
            # Sync OrderItem.is_return field when return is rejected
            for return_item in return_order.return_items.all():
                order_item = return_item.order_item
                # Use the new sync method to properly update based on actual return status
                order_item.update_return_status()
            
            serializer = self.get_serializer(return_order)
            return Response({
                'message': 'Return rejected successfully',
                'return': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to reject return: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete_return(self, request, pk=None):
        """Mark return as completed after refund processing"""
        try:
            return_order = self.get_object()
            
            if return_order.status != 'approved':
                return Response({
                    'error': 'Only approved returns can be marked as completed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return_order.status = 'completed'
            return_order.save()
            
            serializer = self.get_serializer(return_order)
            return Response({
                'message': 'Return marked as completed',
                'return': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to complete return: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def return_statistics(self, request):
        """Get return statistics for dashboard"""
        try:
            from django.db.models import Count, Sum
            
            stats = {
                'total_returns': OrderReturn.objects.count(),
                'pending_returns': OrderReturn.objects.filter(status='pending').count(),
                'approved_returns': OrderReturn.objects.filter(status='approved').count(),
                'completed_returns': OrderReturn.objects.filter(status='completed').count(),
                'rejected_returns': OrderReturn.objects.filter(status='rejected').count(),
                'total_refund_amount': OrderReturn.objects.filter(
                    status__in=['approved', 'completed']
                ).aggregate(total=Sum('refund_amount'))['total'] or 0,
                'returns_by_reason': list(
                    OrderReturn.objects.values('reason').annotate(
                        count=Count('id')
                    ).order_by('-count')
                )
            }
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to get statistics: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)