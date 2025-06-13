from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True, blank=False)
    username = models.CharField(max_length=32, unique=True, blank=False)
    telegram_id = models.BigIntegerField(unique=True, blank=True, null=True)
    telegram_username = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.username