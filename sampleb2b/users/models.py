from django.apps import apps
from django.contrib import auth
from django.contrib import admin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import MinimumLengthValidator
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from uuid import uuid4
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User, UserManager
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.

class CustomUserModel(AbstractBaseUser):
    """
        Base user model for all users
    """

    username_validator = UnicodeUsernameValidator()

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, null=False, blank=False, unique=True, validators=[username_validator],
                                error_messages={
                                    "unique": _("A user with that username already exists."),
                                })
    email = models.EmailField(null=False, blank=False, unique=True)
    mobile_no = PhoneNumberField(null=False, blank=False, unique=True)
    password = models.CharField(max_length=100, null=False, blank=False, validators=[
        MinimumLengthValidator])
    is_admin = models.BooleanField(null=False, blank=False)
    is_common_user = models.BooleanField(null=False, blank=False)
    is_org_user = models.BooleanField(null=False, blank=False)
    organization = models.UUIDField(null=True, blank=True)
    is_superuser = models.BooleanField(null=False, blank=False, default=False)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [
        'email', 'mobile_no', 'password', 'is_admin', 'is_common_user', 'is_org_user'
    ]

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True


class OrganizationModel(models.Model):
    id = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=250, null=False, blank=False, unique=True)
    email = models.EmailField(null=False, blank=False, unique=True)
    mobile_number = PhoneNumberField(null=False, blank=False, unique=True)
    address = models.TextField(null=False, blank=False)
    admin = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE)


class OrgDbModel(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    db_name = models.CharField(null=False, blank=False, max_length=150, unique=True)
    db_host = models.CharField(max_length=50, null=False, blank=False)
    db_user = models.CharField(null=False, blank=False, max_length=150)
    db_password = models.CharField(null=False, blank=False, max_length=150)
    db_port = models.PositiveIntegerField(null=False, blank=False)
    admin_data = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, null=False, blank=False)
    organization = models.ManyToManyField(OrganizationModel)


admin.site.register(CustomUserModel)
