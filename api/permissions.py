from rest_framework import permissions
from base.enums.role import ROLE

class HasRolePermission(permissions.BasePermission):
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles if isinstance(allowed_roles, list) else [allowed_roles]

    def has_permission(self, request, view):
        return request.user and request.user.role in [role.value for role in self.allowed_roles]

