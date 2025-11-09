from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import OrderItem
from ..serializers import OrderItemSerializer


class OrderItemManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing individual order items"""
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def toggle_return(self, request, pk=None):
        """Toggle return status of an order item"""
        try:
            order_item = self.get_object()
            is_return = request.data.get('is_return', False)
            
            # Log before update
            print(f"DEBUG: Before update - OrderItem {order_item.id}: is_return = {order_item.is_return}")
            
            # Update the return status
            old_value = order_item.is_return
            order_item.is_return = is_return
            order_item.save()
            
            # Verify the update by refreshing from database
            order_item.refresh_from_db()
            print(f"DEBUG: After update - OrderItem {order_item.id}: is_return = {order_item.is_return}")
            
            # Confirm the value changed
            if old_value != order_item.is_return:
                print(f"DEBUG: Successfully updated is_return from {old_value} to {order_item.is_return}")
            else:
                print(f"DEBUG: Warning - is_return value did not change: {order_item.is_return}")
            
            # If needed, you can add business logic here like:
            # - Update inventory when item is marked as returned
            # - Send notifications
            # - Update order totals, etc.
            
            return Response({
                'success': True,
                'message': f'Item marked as {"returned" if is_return else "active"}',
                'is_return': order_item.is_return,
                'old_value': old_value,  # Include old value for verification
                'confirmed_saved': order_item.is_return == is_return  # Confirm it was saved correctly
            })
            
        except OrderItem.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Order item not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            print(f"DEBUG: Error in toggle_return: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error updating return status: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)