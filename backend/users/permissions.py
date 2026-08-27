from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    """Restricts access to users with the ADMIN role."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsAdminOrOperatorOrReadOnly(BasePermission):
    """Any authenticated dashboard user can read; only ADMIN/OPERATOR can write.

    Shared across cameras and alerts (blacklist) viewsets, which both need
    the same "operators manage, viewers observe" rule.
    """

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in ("ADMIN", "OPERATOR")
