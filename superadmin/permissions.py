from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to authenticated users who have the 'admin' role
    or have superuser status.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'role', None) == 'admin'
                or request.user.is_superuser
            )
        )

