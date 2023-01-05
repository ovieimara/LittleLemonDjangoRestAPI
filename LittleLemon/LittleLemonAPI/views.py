from django.shortcuts import render, get_object_or_404
from rest_framework import generics,exceptions, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import MenuItem, OrderItem, Cart, Order, Category
from .serializers import MenuItemSerializer, UserSerializer, OrderItemSerializer, CartSerializer, OrderSerializer, CategorySerializer
from .permissions import ManagerAndCustomerPermission, IsOnlyManagerPermission, IsOwnerPermission, IsOwnerAndManagerCustomerPermission
from django.contrib.auth.models import User, Group
from django.http import Http404
from django.db import transaction,models


# Create your views here.
class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ManagerAndCustomerPermission]

class UpdateCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ManagerAndCustomerPermission]    

class MenuItemsView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [ManagerAndCustomerPermission]

    # def perform_create(self, serializer):
    #     if not self.request.user.groups.filter(name='Manager').exists():
    #         raise exceptions.PermissionDenied

    #     serializer.save()
    # def get_permissions(self):
    #     if(self.request.method=='GET'):
    #         return [IsAuthenticated]
        
    #     return [IsAuthenticated, ManagerPermission]

class RetrieveMenuItemsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuItemSerializer
    permission_classes = [ManagerAndCustomerPermission]
    # lookup_fields = ['title']


#user group management APIs
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsOnlyManagerPermission])
def managersView(request, **kwargs):
    state = status.HTTP_400_BAD_REQUEST
    data = {'message': "error"}
    userId = kwargs.get('userId')

    if request.method == 'POST':
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name='Manager')
        
        managers.user_set.add(user)
        data = {'message': 'ok'}
        state = status.HTTP_201_CREATED

    elif request.method == 'GET':
        managers = User.objects.filter(groups__name='Manager')
        many = True
        if userId:
            # managers = managers.filter(pk=userId)
            managers = get_object_or_404(managers, pk=userId)
            many = False
        # managers = user.groups.filter(name='Manager')
        serialized = UserSerializer(managers, many=many)
        data = serialized.data
        state = status.HTTP_200_OK

    elif request.method == 'DELETE':
        user = get_object_or_404(User, pk=userId)
        managers = Group.objects.get(name='Manager')
        managers.user_set.remove(user)
        data = {'message': 'ok'}
        state = status.HTTP_200_OK

    return Response(data, state)



# @api_view(['DELETE'])
# @permission_classes([ManagerAndCustomerPermission])
# def usersView(request, userId):
#     state = status.HTTP_400_BAD_REQUEST
#     data = {'message': "error"}

#     if userId:
#         user = get_object_or_404(User, pk=userId)
#         managers = Group.objects.get(name='Manager')
#         managers.user_set.remove(user)
#         data = {'message': 'ok'}
#         state = status.HTTP_200_OK

#     return Response(data, state)


class DeliveryCrewView( generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = UserSerializer
    # permission_classes = [IsOnlyManagerPermission]

    # def get_queryset(self, **kwargs):
    #     delivery_crew = User.objects.filter(groups__name='Delivery crew')
    #     userId = kwargs.get('pk')
    #     print(kwargs)
    #     if userId:
    #         delivery_crew = get_object_or_404(delivery_crew, pk=userId)

    #     return delivery_crew


    def perform_create(self, serializer):
        user = serializer.save()
        delivery = Group.objects.get(name='Delivery crew')
        delivery.user_set.add(user)

    def get_permissions(self):
        methods = ['GET', 'POST', 'DELETE']
        if self.request.method in methods:
            permission_classes = [IsOnlyManagerPermission]
        else:
            permission_classes = []
    
        return [permission() for permission in permission_classes]

    # def perform_destroy(self, instance):
    #     delivery = Group.objects.get(name='Delivery crew')
    #     delivery.user_set.remove(instance)
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class RemoveUserFromGroupView(generics.RetrieveDestroyAPIView):
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = UserSerializer
    permission_classes = [IsOnlyManagerPermission]

    def destroy(self, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)

        delivery_crew = Group.objects.get(name='Delivery crew')
        delivery_crew.user_set.remove(instance)

        return Response(status=status.HTTP_200_OK)

class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    # queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.select_related('menuitem').filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        cart = Cart.objects.all().filter(user=self.request.user)
        self.perform_destroy(cart)

        return Response(status=status.HTTP_204_NO_CONTENT)


    # def perform_destroy(self, instance):
    #      cart = Cart.objects.all().filter(user=self.request.user)
    #      cart.delete()

@api_view(['GET', 'POST'])
# @permission_classes([IsOwnerPermission, IsOnlyManagerPermission])
def OrdersView(request):
    
    if request.method == 'GET':
        orders = OrderItem.objects.all()
        if request.user.groups.filter(name='Manager').exists():
            order = orders
        if request.user.groups.filter(name='Delivery crew').exists():
            order = get_object_or_404(orders, delivery_crew = request.user)
            # order = order.filter(delivery_crew = request.user)
        if not request.user.groups.filter(name='Manager').exists() and not request.user.groups.filter(name='Delivery crew').exists():
            order = get_object_or_404(orders, user = request.user)
            # order = order.filter(user = request.user)
            
        serialized_data = OrderItemSerializer(order, many=True)
        data = serialized_data.data
        return Response(data)

    elif request.method == 'POST':
        # order = Order.objects.create(user=request.user, total=0.00)
        # data = {'user': request.user, 'total': 0.00}
        order = {"user":request.user.pk}
        serialized_order = OrderSerializer(data=order)
        serialized_order.is_valid(raise_exception=True)
        
        
        data = {"message": "failed"}
        state = status.HTTP_400_BAD_REQUEST

        cart = Cart.objects.all().filter(user=request.user)
        # sum_price = user_items.aggregate(total=sum('price'))
        F = models.F
        price_sum = cart.aggregate(total=models.Sum(F('unit_price') * F('quantity'), output_field=models.DecimalField()))
        print(price_sum)

        items = []

        with transaction.atomic():
            instance = serialized_order.save(total=price_sum.get('total', 0))

            for item in cart:
                # order_item = OrderItem(order, menuitem = item.menuitem, quantity=item.quantity, unit_price=item.unit_price, price=item.price)
                # print(item.menuitem.pk, item.quantity, item.unit_price, item.price, instance.pk)
                print(item.quantity, item.price)
                order_item = {"order": instance.pk, "menuitem": item.menuitem.pk, "quantity": item.quantity, "unit_price": item.unit_price, "price": item.price}
                items.append(order_item)
                # total += float(item.price)
            
            serialized_item = OrderItemSerializer(data=items, many=True)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            cart.delete()
            data = serialized_item.data
            state = status.HTTP_201_CREATED
            
        return Response(serialized_item.data, status=state)


# class MenuItemsView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView, ManagerPermission):
#     # queryset = Cart.objects.all()
#     # serializer_class = CartSerializer
#     queryset = MenuItem.objects.select_related('category').all()
#     serializer_class = MenuItemSerializer
#     # permission_classes = [IsOwnerPermission]

        

#     def perform_create(self, serializer):
#         if ManagerPermission.has_permission()
#             serializer.save(user = self.request.user)

# @api_view(['DELETE'])
# @permission_classes([IsOwnerPermission])
# def RemoveCartView(request): 
#     cart = Cart.objects.all(user=request.user)
#     cart.delete()


class OrderView(generics.RetrieveUpdateDestroyAPIView):
    # queryset = OrderItem.objects.filter()
    serializer_class = OrderSerializer
    # authentication_classes = [IsAuthenticated]
    permission_classes = [IsOwnerAndManagerCustomerPermission]

    def getAuthorization(self, request):
        manager = request.user.groups.filter(name='Manager').exists()
        staff = manager or request.user.groups.filter(name='Delivery crew').exists()
        return manager, staff

    def get_object(self):
        try:
            orderId = self.kwargs.get('orderId')
            # items = OrderItem.objects.all().filter(order=orderId)
            _, staff = self.getAuthorization(self.request)
            order = Order.objects.get(id=orderId)
            if not staff:
                order = get_object_or_404(order, user=self.request.user)
            return order
        except Order.DoesNotExist:
            raise Http404
    
    # def get_queryset(self):
    #     orderId = self.kwargs['orderId']
    #     # print(orderId)
    #     if orderId:            
    #         # items = get_object_or_404(OrderItem, order=orderId)
    #         order = self.get_object()
    #         # user_items = order.filter(order__user=self.request.user)
    #         user_items = order.items.get(order__user=self.request.user)
    #         if user_items.exists():
    #             return user_items

    #         raise exceptions.PermissionDenied()

    # def get(self, request, *args, **kwargs):
    #     orderId = kwargs.get('orderId')
    #     item = OrderItem.objects.get(order=orderId, order__user=request.user)
    #     if self.request.user == order.user:
    #             # return Order.objects.all(id = orderId)
    #             return order
    #         else:
    #             raise exceptions.PermissionDenied()

    #     return self.retrieve(request, *args, **kwargs)

    # def perform_update(self, serializer):
    #     items = self.get_object()
    #     isManager, staff = self.getAuthorization(self.request)
    #     if isManager or not staff:
    #         order = serializer.save()
    #         if not staff:
    #             user_items = items.filter(order__user=self.request.user)
    #             sum_price = user_items.aggregate(total=sum('price'))
    #             order.total = sum_price.get('total')


    def put(self, request, *args, **kwargs):
        # order = self.get_object(orderId)
        isManager, staff = self.getAuthorization(request)
        if isManager or not staff:
            # serializer = OrderItemSerializer(order, data=kwargs)
            # serializer.is_valid(raise_exception=True)
            # serializer.save()
            return self.update(request, *args, **kwargs)

        return Response(status=status.HTTP_403_FORBIDDEN)


    def patch(self, request, *args, **kwargs):
        # if no OrderItem exists by this PK, raise a 404 error
        response = {}
        # orderId = kwargs.get('orderId')
        isManager, staff = self.getAuthorization(request)
        data = {}
        # order_item = get_object_or_404(OrderItem, pk=orderId)
        # order_item = self.get_object(orderId)
        if request.user.groups.filter(name="Delivery crew").exists():
            # this is the only field we want to update
            data = {"status": 1}
        if isManager or not staff: 
            # data_status = 
            # user = get_object_or_404(User, username='crew')
            data = kwargs

        if not data:
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        return self.partial_update(request, *args, data)
        # serializer = OrderItemSerializer(order_item, data=data, partial=True)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        # status=status.HTTP_206_PARTIAL_CONTENT
        # response = serializer.data

    # def perform_destroy(self, instance):

    def delete(self, request, *args, **kwargs):
        isManager, _ = self.getAuthorization(request)
        if isManager:
            order = Order.objects.get(pk=kwargs.get('orderId'))
            self.perform_destroy(order)
            return Response(status=status.HTTP_204_NO_CONTENT)
            # return self.destroy(request, *args, **kwargs)

        return Response(status=status.HTTP_403_FORBIDDEN)




    # def patch(self, request, pk, amount):
    #         # if no model exists by this PK, raise a 404 error
    #         model = get_object_or_404(MyModel, pk=pk)
    #         # this is the only field we want to update
    #         data = {"amount": model.amount + int(amount)}
    #         serializer = MyModelSerializer(model, data=data, partial=True)

    #         if serializer.is_valid():
    #             serializer.save()
    #             return Response(serializer.data)
    #         # return a meaningful error response
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        



        



    





        

        









        



