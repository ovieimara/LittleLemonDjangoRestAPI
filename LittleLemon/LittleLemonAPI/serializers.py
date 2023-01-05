from rest_framework import serializers
from .models import MenuItem, Order, Cart, OrderItem, Category
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields ='__all__'

class MenuItemSerializer(serializers.ModelSerializer):
    # category = serializers.StringRelatedField(many=True)
    class Meta:
        model = MenuItem
        fields = ['title', 'price', 'featured', 'category']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['menuitem', 'quantity', 'unit_price', 'price']
