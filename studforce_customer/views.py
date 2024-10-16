import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from studforce_auth.serializers import CustomerSerializer
from studforce_customer.serializers import CustomerAddressSerializer, ProductOrderSerializer, OrderSerializer, EditOrderSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from .serializers import CartSerializer
import json
from django.http import JsonResponse, HttpResponse
from promptpay import qrcode
from io import BytesIO
from rest_framework.permissions import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from .models import Customer

stripe.api_key = settings.STRIPE_SECRET_KEY

class GeneratePromptPayQRView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            amount = float(amount)
        except ValueError:
            return Response({'error': 'Invalid amount format'}, status=status.HTTP_400_BAD_REQUEST)
        payload = qrcode.generate_payload('0841234567', amount)
        img = qrcode.to_image(payload)

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return HttpResponse(buffer, content_type="image/png")

class ChargeCustomerView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            token = data.get('token')
            amount = data.get('amount')
            if not token:
                return JsonResponse({'error': 'Token is required'}, status=400)
            amount_cal = int(float(amount) * 100)

            # ทำการ charge ลูกค้า
            charge = stripe.Charge.create(
                amount=amount_cal,
                currency='thb',
                description='Credited by Studforce Company, Inc',
                source=token,
            )
            return JsonResponse({'status': 'Payment successful'})

        except stripe.error.StripeError as e:
            return JsonResponse({'error': str(e)}, status=400)
    

class CustomerAddressList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = CustomerAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerAddressDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        customer_address = CustomerAddress.objects.filter(customer=pk)
        serializer = CustomerAddressSerializer(customer_address, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def put(self, request, pk):
        customer_address = get_object_or_404(CustomerAddress, pk=pk)
        serializer = CustomerAddressSerializer(customer_address, data=request.data, partial=True)  # ใช้ partial เพื่อให้สามารถอัปเดตข้อมูลบางส่วนได้
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        customer_address = get_object_or_404(CustomerAddress, pk=pk)
        customer_address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CustomerList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CustomerRegister(APIView):
    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            User.objects.create_user(
                username=request.data.get('username'),
                password=request.data.get('password'),
                email=request.data.get('email')
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CartDetail(APIView):
    def put(self, request, product_id):
        productPut = get_object_or_404(Cart, pk=product_id)
        serializer = CartSerializer(productPut, data=request.data, partial=True)  # เปิดใช้งาน partial update
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, product_id):
        productDelete = get_object_or_404(Cart, pk=product_id)
        productDelete.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CustomerCartList(APIView):
    def get(self, request, customer_id):
        carts = Cart.objects.filter(customer_id=customer_id)
        serializer = CartSerializer(carts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerOrderList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, customer_id):
        orders = Order.objects.filter(customer=customer_id)
        if not orders.exists():
            return Response({"message": "No orders found for this customer"}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CustomerOrderDetailList(APIView):
    authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAdminUser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        orders = Order.objects.all().order_by('id')
        if not orders.exists():
            return Response({"message": "No orders found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        
        customer_id = request.data.get('customer')
        cart_items = Cart.objects.filter(customer_id=customer_id)
        if not cart_items.exists():
            return Response({"error": "No items in cart"}, status=status.HTTP_400_BAD_REQUEST)

        order_serializer = OrderSerializer(data=request.data)
        if order_serializer.is_valid():
            order = order_serializer.save()  # บันทึกคำสั่งซื้อ

            # ลูปผ่านสินค้าทั้งหมดใน Cart และสร้าง ProductOrder
            for cart_item in cart_items:
                # อัปเดตจำนวนสินค้าในสต็อก
                product = cart_item.product
                if product.amount >= cart_item.amount:
                    product.amount -= cart_item.amount
                    product.save()

                    # สร้าง ProductOrder
                    ProductOrder.objects.create(
                        order=order,
                        product=product,
                        amount=cart_item.amount,
                        price=cart_item.product.price  # ใช้ราคาสินค้าจาก product โดยตรง หรือจะใช้จาก cart ก็ได้ถ้ามี
                    )
                else:
                    return Response({"error": f"Not enough stock for {product.name}"}, status=status.HTTP_400_BAD_REQUEST)

            # ลบสินค้าที่อยู่ใน Cart ของลูกค้าหลังจากสร้าง Order
            cart_items.delete()

            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditOrderList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    def put(self, request):
        self.check_permissions(request)
        if not request.user.is_staff:
            return Response({'detail': 'Permission denied. Admin only.'}, status=status.HTTP_403_FORBIDDEN)
        
        order_id = request.data.get('id')
        order_status = Order.objects.get(pk=order_id)
        serializer = EditOrderSerializer(order_status, data=request.data, partial=True)  # เปิดใช้งาน partial update
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)  # แก้ไขเป็น HTTP status
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)