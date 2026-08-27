from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # `is_superuser` is a Django auth concept; ADMIN is ours. A superuser
        # created via `createsuperuser` should also be an ADMIN in our RBAC,
        # otherwise they'd be locked out of every write endpoint by role.
        extra_fields.setdefault("role", User.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Dashboard/API user. Camera nodes authenticate separately via API key
    (see cameras.authentication.CameraAPIKeyAuthentication) and are not
    represented as Users."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        OPERATOR = "OPERATOR", "Operator"
        VIEWER = "VIEWER", "Viewer"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"
