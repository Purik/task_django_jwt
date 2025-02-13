from hashlib import md5
from time import time

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    
    def ensure_exists(self, username, **kwargs):
        user, is_created = self.get_or_create(
            defaults=kwargs,
            username=username
        )
        if not is_created:
            for attr, val in kwargs.items():
                setattr(user, attr, val)
            user.save()
        
        return user
    
    
class RefreshTokenManager(models.Manager):
    
    def register(self, token: str, payload: dict, account, ttl: float):
        inst = self.model()
        inst.token_hash = md5(token.encode()).hexdigest()
        inst.account = account
        inst.expire_at = time() + ttl
        inst.payload = payload
        inst.save()
    

class Account(AbstractUser):
    """Наш кастомный пользователь
    """
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=16, blank=True)
    
    objects = UserManager()


class RefreshToken(models.Model):
    token_hash = models.CharField(max_length=128, db_index=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    expire_at = models.FloatField(db_index=True)
    payload = models.JSONField(null=True)
    
    objects = RefreshTokenManager()
