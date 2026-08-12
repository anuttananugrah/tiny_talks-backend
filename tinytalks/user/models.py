from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.mail import send_mail
from django.conf import settings
from random import randint
# Create your models here.

# 1. Custom Manager to handle user creation without a username
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# 2. Custom User Model
class User(AbstractUser):
    # Remove the default username field
    username = None

    # Gender choices
    GENDER_CHOICES = (
        ('M', 'Boy'),
        ('F', 'Girl'),
        ('O', 'Other'),
    )
    role_options=(

        ("User","User"),
        ("Teacher","Teacher"),
    )
    # Email as unique primary login identifier
    email = models.EmailField(unique=True, verbose_name='email address')
    role=models.CharField(max_length=20,choices=role_options,default="User")

    # Custom Fields
    # Note: first_name and last_name (second name) are already inherited from AbstractUser
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    dob = models.DateField(verbose_name='Date of Birth', blank=True, null=True)
    guardian_name = models.CharField(max_length=150, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image=models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_verified=models.BooleanField(default=True)
    otp=models.CharField(max_length=10,null=True,blank=True)
    def generate_otp(self):
        otp_number = str(randint(1000, 9000)) + str(self.id)
        self.otp = otp_number
        self.save()
        
        # Send OTP email
        subject = "Your Verification Code - Tiny Talks"
        message = f"Hello {self.first_name},\n\nYour secret verification code is: {self.otp}\n\nLet's keep making English a Happy Habit! 🐰"
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send email: {e}")
    # Set email as the main identifier for authentication
    USERNAME_FIELD = 'email'
    
    # Required fields when creating a user via createsuperuser command in terminal
    REQUIRED_FIELDS = ['first_name', 'last_name']

    # Attach the custom manager
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} ({self.email})"