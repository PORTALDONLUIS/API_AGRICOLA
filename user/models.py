from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True, blank=True)

    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)

    admin = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    dni = models.IntegerField(null=True, blank=True)

    USERNAME_FIELD = "username"

    class Meta:
        db_table = "user_user"
        managed = False  # ✅ no migraciones, tabla ya existe

    @property
    def is_staff(self):
        return self.admin
