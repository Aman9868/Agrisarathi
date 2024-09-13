from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin,AbstractBaseUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
class CustomUserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError('Users must have a mobile number.')
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(mobile=mobile, password=password, **extra_fields)
        user.is_admin = True
        user.save(using=self._db)
        return user
    
def validate_mobile_no(value):
    if not re.match(r'^\d{10}$', value):
        raise ValidationError("Mobile number must be exactly 10 digits.")

class CustomUser(AbstractUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email=models.EmailField(max_length=255,null=True, blank=True)
    email_verified=models.BooleanField(null=True,blank=True,default="False")
    first_name = None
    last_name = None
    mobile = models.CharField(max_length=10, validators=[validate_mobile_no])
    user_type = models.CharField(max_length=10, choices=[('fpo', 'FPO'), ('supplier', 'Supplier'),('farmer', 'Farmer')])
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) 
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['mobile']
    objects = CustomUserManager()
    class Meta:
        unique_together = ('mobile', 'user_type')
    def natural_key(self):
        return (self.mobile, self.user_type)

    def __str__(self):
        return self.mobile

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def clean(self):
        if not self.mobile:
            raise ValidationError("Mobile number must be set.")

    def tokens(self):
        pass
    