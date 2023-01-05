from rest_framework import permissions

class ManagerAndCustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # request.user.filter(pk=userId, groups__name='Editor').exists()

        if request.method in permissions.SAFE_METHODS:
            return True

        else:
            return request.user.groups.filter(name='Manager').exists()

        

class IsOnlyManagerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # request.user.filter(pk=userId, groups__name='Editor').exists()
        return request.user.groups.filter(name='Manager').exists()


class IsOwnerPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method == 'DELETE':
            return obj.owner == request.user

        # Write permissions are only allowed to the owner of the snippet.
        return False

class IsOwnerAndManagerCustomerPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to put, patch it. Only managers can delete an object
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        
        if request.method in ['DELETE', 'PUT', 'PATCH'] and request.user.groups.filter(name='Manager').exists():
            return True

        if request.method in ['PATCH'] and request.user.groups.filter(name='Delivery crew').exists():
            return True

        if request.method in ['GET', 'PUT', 'PATCH'] and not request.user.groups.filter(name='Manager').exists() and not request.user.groups.filter(name='Delivery crew').exists():
            return True

        # Write permissions are only allowed to the owner of the snippet.
        else:
            return False
