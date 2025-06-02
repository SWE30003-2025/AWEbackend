from rest_framework import permissions
import base64
from django.contrib.auth import authenticate

def get_authenticated_user(request):
    auth = request.META.get('HTTP_AUTHORIZATION')
    if not auth or not auth.startswith('Basic '):
        return None
    try:
        _, encoded = auth.split(' ', 1)
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        user = authenticate(username=username, password=password)
        return user
    except Exception as e:
        print("[PERM] Error decoding auth header:", e)
        return None

class HasRolePermission(permissions.BasePermission):
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles if isinstance(allowed_roles, list) else [allowed_roles]

    def has_permission(self, request, view):
        user = get_authenticated_user(request)
        print("[PERM] user:", user)
        if user:
            print("[PERM] is_authenticated:", user.is_authenticated)
            print("[PERM] user.role:", getattr(user, "role", None))
            print("[PERM] allowed_roles:", [role.value for role in self.allowed_roles])
            return (
                user.is_authenticated
                and hasattr(user, "role")
                and user.role in [role.value for role in self.allowed_roles]
            )
        return False
