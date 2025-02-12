from django.db import models
from django.contrib.auth.models import AbstractUser

class Account(AbstractUser):
    """Наш кастомный пользователь
    """
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
