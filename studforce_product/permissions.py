from rest_framework import permissions

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects,
    but allow read-only access to non-admin users.
    """
    def has_permission(self, request, view):
        # Safe methods are GET, HEAD or OPTIONS, which allow read-only access.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow editing only if the user is admin
        return request.user and request.user.is_staff