from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Product, ProductCategory, ProductSize, ProductImage, Promotion
from .serializers import ProductSerializer, PromotionSerializer
from rest_framework.permissions import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from decimal import Decimal
from .permissions import IsAdminUserOrReadOnly

class ProductListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        products = Product.objects.all().order_by('name')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        self.check_permissions(request)
        if not request.user.is_staff:
            return Response({'detail': 'Permission denied. Admin only.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product_data = serializer.validated_data

            sizes_data = request.data.get('sizes', [])
            images_data = request.data.get('images', [])
            categories_data = request.data.get('categories', [])

            product = Product.objects.create(
                name=product_data['name'],
                description=product_data['description'],
                brand=product_data['brand'],
                price=product_data['price'],
                color=product_data['color'],
                image=product_data['image'],
                amount=product_data['amount']
            )

            for category_name in categories_data:
                category_instance = ProductCategory.objects.get(name=category_name)
                product.categories.add(category_instance)

            for size_data in sizes_data:
                ProductSize.objects.create(product=product, **size_data)

            for image_data in images_data:
                ProductImage.objects.create(product=product, **image_data)

            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

##DOGGY
class ProductDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUserOrReadOnly]

    def get(self, request, pk=None):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk=None):
        self.check_permissions(request)
        print(request.data.get('categories'))
        if not request.user.is_staff:
            return Response({'detail': 'Permission denied. Admin only.'}, status=status.HTTP_403_FORBIDDEN)

        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            product_data = serializer.validated_data
            product.name = product_data.get('name', product.name)
            product.description = product_data.get('description', product.description)
            product.brand = product_data.get('brand', product.brand)
            product.price = product_data.get('price', product.price)
            product.color = product_data.get('color', product.color)
            product.image = product_data.get('image', product.image)
            product.amount = product_data.get('amount', product.amount)
            product.save()

            categories_data = request.data.get('categories', [])
            if categories_data:
                product.categories.clear()
                for category_name in categories_data:
                    try:
                        category_instance = ProductCategory.objects.get(name=category_name)
                        product.categories.add(category_instance)
                    except ProductCategory.DoesNotExist:
                        print(f"Category '{category_name}' does not exist")


            sizes_data = request.data.get('sizes', [])
            if sizes_data:
                product.size.all().delete()
                for size_data in sizes_data:
                    ProductSize.objects.create(product=product, **size_data)

            images_data = request.data.get('images', [])
            if images_data:
                product.images.all().delete()
                for image_data in images_data:
                    ProductImage.objects.create(product=product, **image_data)

            return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        self.check_permissions(request)
        if not request.user.is_staff:
            return Response({'detail': 'Permission denied. Admin only.'}, status=status.HTTP_403_FORBIDDEN)

        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 


class CreatePromotionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    def post(self, request):
        code = request.data.get('code')
        discount_percentage = request.data.get('discount_percentage')
        description = request.data.get('description')
        usage_limit = request.data.get('usage_limit', 1)  # ค่าเริ่มต้นถ้าไม่กำหนด = 1

        if Promotion.objects.filter(code=code).exists():
            return Response({'error': 'Promotion code already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        promotion = Promotion.objects.create(
            code=code,
            discount_percentage=discount_percentage,
            description=description,
            usage_limit=usage_limit
        )

        serializer = PromotionSerializer(promotion)
        return Response({'message': 'Promotion created successfully', 'promotion': serializer.data}, status=status.HTTP_201_CREATED)


class UsePromotionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        code = request.data.get('code')
        summary_price = request.data.get('summary_price')

        try:
            promotion = Promotion.objects.get(code=code)
        except Promotion.DoesNotExist:
            return Response({'error': 'Invalid discount code.'}, status=status.HTTP_400_BAD_REQUEST)

        if promotion.used_count >= promotion.usage_limit:
            promotion.delete()
            return Response({'error': 'Promotion code usage limit exceeded.'}, status=status.HTTP_400_BAD_REQUEST)

        discount = int(promotion.discount_percentage)
        final_price = Decimal(summary_price) * (Decimal(100) - discount) / Decimal(100)

        promotion.used_count += 1
        promotion.save()

        return Response({'final_price': final_price, 'discount_percentage': discount}, status=status.HTTP_200_OK)

    
    def get(self, request):
        codeDiscount = Promotion.objects.all()
        serializer = PromotionSerializer(codeDiscount, many=True) 
        return Response({'promotion': serializer.data}, status=status.HTTP_200_OK)
