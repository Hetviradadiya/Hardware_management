from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions,filters
from ..models import *
from rest_framework.decorators import action
from rest_framework import status

class CustomerView(viewsets.ModelViewSet):
    queryset=Customer.objects.all().order_by('-id')
    serializer_class=CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name','email','phone','address'      
    ]
    
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