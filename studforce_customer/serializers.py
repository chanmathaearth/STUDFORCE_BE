from rest_framework import serializers
from .models import CustomerAddress, Order, ProductOrder, Cart, Product
from studforce_auth.models import Customer
from studforce_product.serializers import ProductSerializer

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ['id', 'customer', 'street_address', 'province', 'district', 'subdistrict', 'postal_code', 'phone_number']

class CustomProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price'] 

class ProductOrderSerializer(serializers.ModelSerializer):
    product = CustomProductSerializer(read_only=True) 
    order = serializers.PrimaryKeyRelatedField(read_only=True) 
    class Meta:
        model = ProductOrder
        fields = ['order', 'product', 'amount', 'price']

class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    shipping_address = serializers.PrimaryKeyRelatedField(queryset=CustomerAddress.objects.all(), write_only=True)
    shipping_address_details = CustomerAddressSerializer(source='shipping_address', read_only=True)
    products = ProductOrderSerializer(source='productorder_set', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'products', 'total_price', 'order_status', 'payment_status', 'created_at', 'promotion', 'shipping_address', 'shipping_address_details']

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'customer', 'product', 'amount', 'type_size', 'size']

class EditOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_status', 'payment_status']