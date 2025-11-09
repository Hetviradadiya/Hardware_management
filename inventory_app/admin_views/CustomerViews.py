from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions,filters
from ..models import *
from rest_framework.decorators import action
from rest_framework import status
from inventory_app.pagination import ListPagination 
from django.db import IntegrityError 

class CustomerView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    queryset=Customer.objects.all().order_by('-id')
    serializer_class=CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name','email','phone','address'      
    ]
    
    def create(self, request, *args, **kwargs):
        """Override create method to handle phone number uniqueness"""
        try:
            # Check if phone number already exists (only if phone is provided and not empty)
            phone = request.data.get('phone')
            phone = phone.strip() if phone else ''
            
            if phone and Customer.objects.filter(phone=phone).exists():
                return Response(
                    {
                        "status": False,
                        "message": f"A customer with phone number '{phone}' already exists.",
                        "field": "phone"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # If phone is empty, set it to None to avoid unique constraint issues
            if not phone:
                request.data['phone'] = None
            
            return super().create(request, *args, **kwargs)
            
        except IntegrityError as e:
            if 'phone' in str(e):
                return Response(
                    {
                        "status": False,
                        "message": "This phone number is already registered with another customer.",
                        "field": "phone"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "status": False,
                    "message": "A customer with this information already exists.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": f"An error occurred: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def update(self, request, *args, **kwargs):
        """Override update method to handle phone number uniqueness"""
        try:
            instance = self.get_object()
            phone = request.data.get('phone')
            phone = phone.strip() if phone else ''
            
            # Check if phone number already exists (only if phone is provided and not empty, excluding current customer)
            if phone and Customer.objects.filter(phone=phone).exclude(id=instance.id).exists():
                return Response(
                    {
                        "status": False,
                        "message": f"A customer with phone number '{phone}' already exists.",
                        "field": "phone"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # If phone is empty, set it to None to avoid unique constraint issues
            if not phone:
                request.data['phone'] = None
            
            return super().update(request, *args, **kwargs)
            
        except IntegrityError as e:
            if 'phone' in str(e):
                return Response(
                    {
                        "status": False,
                        "message": "This phone number is already registered with another customer.",
                        "field": "phone"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "status": False,
                    "message": "A customer with this information already exists.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": f"An error occurred: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['post'], url_path='payment')
    def add_payment(self, request, pk=None):
        try:
            customer = self.get_object()
            payment_str = request.data.get("payment_amount", "0")

            # Convert safely to Decimal
            try:
                payment_amount = Decimal(payment_str)
            except:
                return Response(
                    {"status": False, "message": "Invalid payment amount format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if payment_amount <= 0:
                return Response(
                    {"status": False, "message": "Payment amount must be greater than 0."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ✅ Adjust logic using Decimal
            if customer.pending_amount > 0:
                if payment_amount >= customer.pending_amount:
                    extra = payment_amount - customer.pending_amount
                    customer.advance_payment += extra
                    customer.pending_amount = Decimal('0.00')
                else:
                    customer.pending_amount -= payment_amount
            else:
                # No pending, add as advance
                customer.advance_payment += payment_amount

            customer.save()

            return Response(
                {
                    "status": True,
                    "message": "Payment updated successfully.",
                    "pending_amount": str(customer.pending_amount),
                    "advance_payment": str(customer.advance_payment),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )