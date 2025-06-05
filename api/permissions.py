from rest_framework import permissions
import base64
from base.models import UserModel

def get_authenticated_user(request):
    auth = request.META.get('HTTP_AUTHORIZATION')
    if not auth or not auth.startswith('Basic '):
        return None
    try:
        _, encoded = auth.split(' ', 1)
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        # Do raw password checking instead of using authenticate
        try:
            user = UserModel.objects.get(username=username)
            if user.password == password:  # Raw password comparison
                return user
            return None
        except UserModel.DoesNotExist:
            return None
    except Exception as e:
        print("[PERM] Error decoding auth header:", e)
        return None

class HasRolePermission(permissions.BasePermission):
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles if isinstance(allowed_roles, list) else [allowed_roles]

    def has_permission(self, request, view):
        user = get_authenticated_user(request)
        if user:
            return (
                user.is_authenticated
                and hasattr(user, "role")
                and user.role in [role.value for role in self.allowed_roles]
            )
        
        return False
