import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "Teacher")
        if not extra_fields.get("is_staff") or not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    GENDER_CHOICES = (("M", "Boy"), ("F", "Girl"), ("O", "Other"))
    ROLE_CHOICES = (("User", "User"), ("Teacher", "Teacher"))

    email = models.EmailField(unique=True, verbose_name="email address")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="User")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    dob = models.DateField(verbose_name="Date of Birth", blank=True, null=True)
    guardian_name = models.CharField(max_length=150, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)
    is_verified = models.BooleanField(default=True)
    otp = models.CharField(max_length=128, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = CustomUserManager()

    OTP_VALIDITY = timedelta(minutes=10)
    OTP_MAX_ATTEMPTS = 5

    def generate_otp(self):
        code = f"{secrets.randbelow(900_000) + 100_000:06d}"
        self.otp = make_password(code)
        self.otp_created_at = timezone.now()
        self.otp_attempts = 0
        self.save(update_fields=["otp", "otp_created_at", "otp_attempts"])
        send_mail(
            "Your Tiny Talks verification code",
            f"Hello {self.first_name},\n\nYour verification code is: {code}\nIt expires in 10 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )

    def verify_otp(self, code):
        if not self.otp or not self.otp_created_at:
            return False
        if self.otp_attempts >= self.OTP_MAX_ATTEMPTS or timezone.now() > self.otp_created_at + self.OTP_VALIDITY:
            return False
        if not check_password(str(code), self.otp):
            self.otp_attempts += 1
            self.save(update_fields=["otp_attempts"])
            return False
        return True

    def clear_otp(self):
        self.otp = None
        self.otp_created_at = None
        self.otp_attempts = 0
        self.save(update_fields=["otp", "otp_created_at", "otp_attempts"])

    def __str__(self):
        return f"{self.first_name} ({self.email})"
