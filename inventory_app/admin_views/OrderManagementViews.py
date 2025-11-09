from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.db import transaction, models
from decimal import Decimal
from ..models import Order, OrderItem, OrderReturn, ReturnItem, Customer, Inventory, ProductVariant, Product
from ..serializers import OrderSerializer, OrderItemSerializer
from django.core.exceptions import ValidationError


class OrderManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order editing and modifications"""
    queryset = Order.objects.all().select_related('customer').order_by('-order_date')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get list of all orders with filtering options"""
        orders = self.get_queryset()
        
        # Apply filters
        status_filter = request.GET.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
            
        customer_filter = request.GET.get('customer')
        if customer_filter:
            orders = orders.filter(customer__name__icontains=customer_filter)
            
        search = request.GET.get('search')
        if search:
            orders = orders.filter(
                models.Q(id__icontains=search) |
                models.Q(customer__name__icontains=search)
            )
            
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def edit_order(self, request, pk=None):
        """Edit existing order - modify items, quantities, prices"""
        order = self.get_object()
        
        # Check if order can be edited (business rules)
        if hasattr(order, 'returns') and order.returns.filter(status__in=['pending', 'approved']).exists():
            return Response({
                'error': 'Cannot edit order with pending returns'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Handle item modifications
                items_data = request.data.get('items', [])
                
                # Track inventory changes
                inventory_adjustments = {}
                
                for item_data in items_data:
                    item_id = item_data.get('id')
                    action_type = item_data.get('action', 'update')  # update, delete, add
                    
                    if action_type == 'delete' and item_id:
                        # Delete item and restore inventory
                        order_item = get_object_or_404(OrderItem, id=item_id, order=order)
                        variant = order_item.variant
                        
                        # Restore inventory
                        inventory_item = Inventory.objects.get(variant=variant)
                        inventory_item.quantity += order_item.quantity
                        inventory_item.save()
                        
                        order_item.delete()
                        
                    elif action_type == 'update' and item_id:
                        # Update existing item
                        order_item = get_object_or_404(OrderItem, id=item_id, order=order)
                        old_quantity = order_item.quantity
                        
                        # Update fields
                        new_quantity = int(item_data.get('quantity', old_quantity))
                        order_item.quantity = new_quantity
                        order_item.price_at_sale = Decimal(str(item_data.get('price_at_sale', order_item.price_at_sale)))
                        order_item.item_discount = Decimal(str(item_data.get('item_discount', order_item.item_discount)))
                        order_item.gst = Decimal(str(item_data.get('gst', order_item.gst)))
                        order_item.is_percentage = item_data.get('is_percentage', order_item.is_percentage)
                        
                        # Adjust inventory with proper validation
                        inventory_item = Inventory.objects.get(variant=order_item.variant)
                        quantity_diff = old_quantity - new_quantity  # Positive means returning to inventory
                        
                        if quantity_diff < 0:  # Need more inventory
                            additional_needed = abs(quantity_diff)
                            if inventory_item.quantity < additional_needed:
                                return Response({
                                    'error': f'Insufficient stock for {order_item.variant.product.name} - {order_item.variant.size}. Available: {inventory_item.quantity}, Needed: {additional_needed}'
                                }, status=status.HTTP_400_BAD_REQUEST)
                        
                        inventory_item.quantity += quantity_diff
                        inventory_item.save()
                        order_item.save()
                        
                    elif action_type == 'add':
                        # Add new item
                        variant_id = item_data.get('variant_id')
                        quantity = int(item_data.get('quantity', 1))
                        
                        if not variant_id:
                            return Response({
                                'error': 'variant_id is required for new items'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        variant = get_object_or_404(ProductVariant, id=variant_id)
                        
                        # Check inventory availability
                        inventory_item = Inventory.objects.get(variant=variant)
                        if inventory_item.quantity < quantity:
                            return Response({
                                'error': f'Insufficient stock for {variant.product.name} - {variant.size}. Available: {inventory_item.quantity}, Requested: {quantity}'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Create new order item
                        OrderItem.objects.create(
                            order=order,
                            variant=variant,
                            quantity=quantity,
                            price_at_sale=Decimal(str(item_data.get('price_at_sale', variant.price))),
                            item_discount=Decimal(str(item_data.get('item_discount', 0))),
                            gst=Decimal(str(item_data.get('gst', variant.gst))),
                            is_percentage=item_data.get('is_percentage', True)
                        )
                        
                        # Deduct inventory
                        inventory_item.quantity -= quantity
                        inventory_item.save()
                
                # Recalculate order totals
                self._recalculate_order_totals(order, request.data)
                
                # Update order level fields if provided
                if 'order_discount' in request.data:
                    order.order_discount = Decimal(str(request.data['order_discount']))
                if 'is_percentage' in request.data:
                    order.is_percentage = request.data['is_percentage']
                if 'note' in request.data:
                    order.note = request.data['note']
                
                order.save()
                
                # Log the order update
                print(f"Order {order.id} updated successfully. New total: {order.total_amount}")
                
                # Return updated order data
                updated_order_data = OrderSerializer(order).data
                
                return Response({
                    'message': 'Order updated successfully',
                    'order': updated_order_data,
                    'changes_summary': {
                        'items_updated': len([item for item in items_data if item.get('action') == 'update']),
                        'items_added': len([item for item in items_data if item.get('action') == 'add']),
                        'items_deleted': len([item for item in items_data if item.get('action') == 'delete']),
                        'order_discount_updated': 'order_discount' in request.data,
                        'notes_updated': 'note' in request.data
                    }
                })
                
        except Exception as e:
            return Response({
                'error': f'Failed to update order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def create_return(self, request, pk=None):
        """Create a return request for an order"""
        order = self.get_object()
        
        return_data = {
            'original_order': order,  # Pass the order instance, not the ID
            'reason': request.data.get('reason'),
            'notes': request.data.get('notes', ''),
            'processing_fee': Decimal(str(request.data.get('processing_fee', 0)))
        }
        
        return_items_data = request.data.get('return_items', [])
        
        if not return_items_data:
            return Response({
                'error': 'No items specified for return'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Create return order
                return_order = OrderReturn.objects.create(**return_data)
                
                total_return_amount = Decimal('0')
                
                # Process return items
                for item_data in return_items_data:
                    order_item = get_object_or_404(OrderItem, id=item_data['order_item_id'])
                    return_quantity = int(item_data['return_quantity'])
                    condition = item_data.get('condition', 'good')
                    
                    # Validate return quantity
                    if return_quantity <= 0:
                        raise ValidationError(f'Return quantity must be greater than 0')
                    if return_quantity > order_item.quantity:
                        raise ValidationError(f'Return quantity cannot exceed ordered quantity for {order_item.variant}')
                    
                    # Calculate refund per unit using the order item's final price method
                    if hasattr(order_item, 'final_price'):
                        item_final_price = order_item.final_price()
                    else:
                        # Fallback calculation
                        item_total = order_item.price_at_sale * order_item.quantity
                        item_discount = order_item.discount_price() if hasattr(order_item, 'discount_price') else Decimal('0')
                        item_final_price = item_total - item_discount
                    
                    refund_per_unit = item_final_price / order_item.quantity
                    
                    # Create return item
                    return_item = ReturnItem.objects.create(
                        return_order=return_order,
                        order_item=order_item,
                        return_quantity=return_quantity,
                        condition=condition,
                        refund_per_unit=refund_per_unit,
                        total_refund=refund_per_unit * return_quantity
                    )
                    
                    # Add to total using the model's calculation method
                    total_return_amount += return_item.calculate_refund_amount()
                
                # Update return order totals
                return_order.total_return_amount = total_return_amount
                return_order.refund_amount = total_return_amount - return_order.processing_fee
                return_order.save()
                
                return Response({
                    'message': 'Return request created successfully',
                    'return_id': return_order.id,
                    'refund_amount': return_order.refund_amount
                })
                
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'Failed to create return: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def returns_list(self, request):
        """Get list of all returns"""
        returns = OrderReturn.objects.select_related('original_order__customer').order_by('-return_date')
        
        returns_data = []
        for return_order in returns:
            returns_data.append({
                'id': return_order.id,
                'order_id': return_order.original_order.id,
                'customer_name': return_order.original_order.customer.name if return_order.original_order.customer else 'N/A',
                'return_date': return_order.return_date,
                'status': return_order.status,
                'reason': return_order.get_reason_display(),
                'refund_amount': return_order.refund_amount,
                'total_return_amount': return_order.total_return_amount
            })
        
        return Response(returns_data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({
                'error': 'Status is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Define valid status transitions
        valid_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        
        if new_status not in valid_statuses:
            return Response({
                'error': f'Invalid status. Valid options are: {", ".join(valid_statuses)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Business logic for status transitions
        old_status = getattr(order, 'status', 'pending')
        
        # Check if transition is allowed
        if old_status == 'completed' and new_status != 'completed':
            return Response({
                'error': 'Cannot change status of a completed order'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if old_status == 'cancelled' and new_status not in ['pending', 'cancelled']:
            return Response({
                'error': 'Can only reopen cancelled orders to pending status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Update the order status
            order.status = new_status
            order.save()
            
            return Response({
                'message': f'Order status updated to {new_status}',
                'order_id': order.id,
                'new_status': new_status,
                'old_status': old_status
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to update order status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def process_return(self, request):
        """Process/approve a return request"""
        return_id = request.data.get('return_id')
        if not return_id:
            return Response({
                'error': 'return_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            return_order = OrderReturn.objects.get(id=return_id)
        except OrderReturn.DoesNotExist:
            return Response({
                'error': f'Return with ID {return_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error fetching return: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        action_type = request.data.get('action', 'approve')  # 'approve', 'reject'
        notes = request.data.get('notes', '')
        
        try:
            with transaction.atomic():
                if action_type == 'approve':
                    return_order.status = 'approved'
                    if hasattr(request, 'user'):
                        return_order.processed_by = request.user
                    return_order.processed_at = timezone.now()
                    
                    # Immediately complete the return - restore inventory and process refund
                    return_order.status = 'completed'
                    
                    inventory_updates = []
                    
                    # Restore inventory for returned items based on condition
                    for return_item in return_order.return_items.all():
                        try:
                            inventory_item = Inventory.objects.get(variant=return_item.order_item.variant)
                        except Inventory.DoesNotExist:
                            return Response({
                                'error': f'Inventory not found for variant {return_item.order_item.variant}'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Restore inventory based on condition
                        if return_item.condition in ['good', 'unopened']:
                            # Full restore
                            restore_quantity = return_item.return_quantity
                        elif return_item.condition == 'defective':
                            # Partial restore (75% of quantity as it can be refurbished)
                            restore_quantity = int(return_item.return_quantity * 0.75)
                        elif return_item.condition == 'damaged':
                            # Minimal restore (25% as salvage)
                            restore_quantity = int(return_item.return_quantity * 0.25)
                        else:
                            restore_quantity = 0
                        
                        if restore_quantity > 0:
                            inventory_item.quantity += restore_quantity
                            inventory_item.save()
                            
                            inventory_updates.append({
                                'product': return_item.order_item.variant.product.name,
                                'size': return_item.order_item.variant.size,
                                'returned_quantity': return_item.return_quantity,
                                'restored_quantity': restore_quantity,
                                'condition': return_item.condition,
                                'new_stock': inventory_item.quantity
                            })
                    
                    # Update customer balance (add refund as credit)
                    customer = return_order.original_order.customer
                    if customer:
                        customer.advance_payment += return_order.refund_amount
                        customer.save()
                    
                    return_order.notes = f"{return_order.notes}\n{notes}".strip()
                    
                elif action_type == 'reject':
                    return_order.status = 'rejected'
                    if hasattr(request, 'user'):
                        return_order.processed_by = request.user
                    return_order.processed_at = timezone.now()
                    return_order.notes = f"{return_order.notes}\nRejection reason: {notes}".strip()
                    inventory_updates = []
                
                return_order.save()
                
                return Response({
                    'message': f'Return {action_type}d successfully',
                    'return_status': return_order.status,
                    'inventory_updates': inventory_updates if action_type == 'approve' else [],
                    'refund_amount': return_order.refund_amount if action_type == 'approve' else 0,
                    'customer_credit_added': return_order.refund_amount if action_type == 'approve' else 0
                })
                
        except Exception as e:
            return Response({
                'error': f'Failed to process return: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _recalculate_order_totals(self, order, data):
        """Recalculate order totals after modifications"""
        items = order.items.all()
        
        subtotal = Decimal('0')
        total_item_discount = Decimal('0')
        total_gst = Decimal('0')
        
        for item in items:
            # Calculate item subtotal
            item_subtotal = item.price_at_sale * item.quantity
            subtotal += item_subtotal
            
            # Calculate item-level discount
            if item.is_percentage:
                item_discount_amount = (item_subtotal * item.item_discount) / Decimal('100')
            else:
                item_discount_amount = item.item_discount
            
            total_item_discount += item_discount_amount
            
            # Calculate GST on discounted amount
            discounted_amount = item_subtotal - item_discount_amount
            item_gst_amount = (discounted_amount * item.gst) / Decimal('100')
            total_gst += item_gst_amount
        
        # Calculate order-level discount
        order_discount_amount = Decimal('0')
        if 'order_discount' in data:
            order_discount = Decimal(str(data['order_discount']))
            is_percentage = data.get('is_percentage', order.is_percentage)
            
            # Apply order discount on subtotal after item discounts
            discounted_subtotal = subtotal - total_item_discount
            
            if is_percentage:
                order_discount_amount = (discounted_subtotal * order_discount) / Decimal('100')
            else:
                order_discount_amount = order_discount
        else:
            # Use existing order discount if not provided in data
            if order.is_percentage:
                discounted_subtotal = subtotal - total_item_discount
                order_discount_amount = (discounted_subtotal * order.order_discount) / Decimal('100')
            else:
                order_discount_amount = order.order_discount or Decimal('0')
        
        total_discount = total_item_discount + order_discount_amount
        total_amount = subtotal - total_discount + total_gst
        
        # Validate totals match frontend calculations if provided
        if 'total_amount' in data:
            frontend_total = Decimal(str(data['total_amount']))
            if abs(total_amount - frontend_total) > Decimal('0.01'):  # Allow 1 cent difference for rounding
                print(f"Warning: Total amount mismatch. Backend: {total_amount}, Frontend: {frontend_total}")
        
        # Update order fields
        order.subtotal = subtotal
        order.total_item_discount = total_item_discount
        order.total_discount = total_discount
        order.total_gst = total_gst
        order.total_amount = total_amount
        
        print(f"Order {order.id} totals recalculated:")
        print(f"  Subtotal: {subtotal}")
        print(f"  Item Discount: {total_item_discount}")
        print(f"  Order Discount: {order_discount_amount}")
        print(f"  Total Discount: {total_discount}")
        print(f"  GST: {total_gst}")
        print(f"  Total Amount: {total_amount}")
    
    @action(detail=False, methods=['get'])
    def available_products(self, request):
        """Get available products with variants for adding to orders"""
        try:
            # Get products that have inventory available
            products_data = []
            
            # Get all product variants with inventory
            variants = ProductVariant.objects.select_related('product').filter(
                inventory__quantity__gt=0
            ).distinct()
            
            for variant in variants:
                inventory = Inventory.objects.get(variant=variant)
                product_info = {
                    'variant_id': variant.id,
                    'product_name': variant.product.name,
                    'variant_name': variant.size if variant.size else variant.product.name,
                    'display_name': f"{variant.product.name} - {variant.size}" if variant.size else variant.product.name,
                    'price': float(variant.price),
                    'available_quantity': inventory.quantity,
                    'gst_rate': float(variant.gst) if variant.gst else 0.0
                }
                products_data.append(product_info)
            
            # Sort by product name
            products_data.sort(key=lambda x: x['display_name'])
            
            return Response({
                'products': products_data
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to fetch available products: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_order_consistency(self, order):
        """Validate that order totals are consistent"""
        items = order.items.all()
        
        if not items.exists():
            return False, "Order must have at least one item"
        
        # Recalculate totals
        calculated_subtotal = sum(item.price_at_sale * item.quantity for item in items)
        
        if abs(calculated_subtotal - order.subtotal) > Decimal('0.01'):
            return False, f"Subtotal mismatch: calculated {calculated_subtotal}, stored {order.subtotal}"
        
        return True, "Order is consistent"


