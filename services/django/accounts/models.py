from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. Extends AbstractUser so we can add fields later
    (e.g., favourite team, notification preferences) without a migration nightmare.
    """

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
