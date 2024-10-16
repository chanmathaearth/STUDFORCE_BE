from django.urls import path
from .views import ProductListView, ProductDetailView, CreatePromotionView, UsePromotionView

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('promotions/create/', CreatePromotionView.as_view(), name='create_promotion'),
    path('promotions/', UsePromotionView.as_view(), name='use_promotion'),
]
