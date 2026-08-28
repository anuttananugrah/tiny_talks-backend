import secrets
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from user.models import User, Notification
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer, StudentListSerializer,
    NotificationSerializer, NotificationCreateSerializer
)


class RegisterView(generics.CreateAPIView):
    """API endpoint for new user registration."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully. Check your email for the verification code.",
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPView(APIView):
    """API endpoint to verify the email OTP."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response(
                {"error": "Both email and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_verified:
            return Response(
                {"message": "User is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.verify_otp(otp):
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            user.clear_otp()

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Email verified successfully.",
                    "user": UserSerializer(user).data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Invalid OTP. Please try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResendOTPView(APIView):
    """Issue a fresh verification code without revealing account details."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        email = request.data.get("email")
        if email:
            try:
                user = User.objects.get(email=email)
                if not user.is_verified:
                    user.generate_otp()
            except User.DoesNotExist:
                pass
        return Response({"message": "If an unverified account exists, a new code has been sent."})


class LoginView(APIView):
    """API endpoint to authenticate user and return JWT tokens & user staff status."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Please provide both email and password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_verified:
            refresh = RefreshToken.for_user(user)
            userData = UserSerializer(user).data
            return Response(
                {
                    "message": "Login successful.",
                    "is_staff": user.is_staff,
                    "role": getattr(user, "role", "student"),
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "email": user.email,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    "user": userData,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """API endpoint for logged-in users to view or update their profile."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

from django.contrib.auth.password_validation import validate_password
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

RESET_TOKEN_MAX_AGE = 900  # 15 minutes


class IsTeacherOrStaffUser(permissions.BasePermission):
    """
    Allows access to users who are authenticated and either have role='Teacher' or is_staff=True.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, "is_staff", False)
                or getattr(request.user, "role", "") == "Teacher"
            )
        )


class TeacherStudentListView(generics.ListAPIView):
    """React Dashboard: See all registered students."""
    serializer_class = StudentListSerializer
    permission_classes = [IsTeacherOrStaffUser]

    def get_queryset(self):
        return User.objects.filter(is_staff=False).exclude(role__iexact="Teacher").exclude(role__iexact="Admin").order_by("-date_joined")


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.generate_otp()
            return Response({"message": "If an account exists, a reset code has been sent."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "If an account exists, a reset code has been sent."}, status=status.HTTP_200_OK)


class VerifyResetOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response({"error": "Both email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.verify_otp(otp):
                user.clear_otp()
                signer = TimestampSigner(salt="tinytalks.password_reset")
                reset_token = signer.sign(user.email)
                return Response(
                    {
                        "message": "OTP verified successfully.",
                        "reset_token": reset_token,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response({"error": "Invalid OTP. Please try again."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Invalid OTP. Please try again."}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        email = request.data.get("email")
        token = request.data.get("token") or request.data.get("reset_token")
        otp = request.data.get("otp")
        new_password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not (token or (email and otp)):
            return Response({"error": "Reset token or email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not new_password or not confirm_password:
            return Response({"error": "Password and confirmation are required."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        if token:
            signer = TimestampSigner(salt="tinytalks.password_reset")
            try:
                token_email = signer.unsign(token, max_age=RESET_TOKEN_MAX_AGE)
                if email and token_email.lower() != email.lower():
                    return Response({"error": "Invalid or mismatched reset token."}, status=status.HTTP_400_BAD_REQUEST)
                user = User.objects.get(email=token_email)
            except (BadSignature, SignatureExpired):
                return Response({"error": "Reset session has expired or is invalid. Please request a new code."}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                user = User.objects.get(email=email)
                if not user.verify_otp(otp):
                    return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "Invalid OTP or email."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            return Response({"error": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        user.clear_otp()
        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)


# ============================================================
# 🔔 NOTIFICATIONS VIEWS (Students & Teachers)
# ============================================================

class NotificationListView(APIView):
    """
    Authenticated Student/User endpoint to get the latest notifications.
    Includes an unread counter for the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Notification.objects.all().order_by("-created_at")[:50]
        unread_count = Notification.objects.exclude(read_by=request.user).count()

        serializer = NotificationSerializer(queryset, many=True, context={"request": request})
        return Response({
            "results": serializer.data,
            "unread_count": unread_count,
        }, status=status.HTTP_200_OK)



class NotificationMarkReadView(APIView):
    """
    Endpoint for an authenticated student to mark a single notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        notification.read_by.add(request.user)
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(APIView):
    """
    Endpoint for an authenticated student to mark all notifications as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        unread = Notification.objects.exclude(read_by=request.user)
        for n in unread:
            n.read_by.add(request.user)
        return Response({"message": "All notifications marked as read."}, status=status.HTTP_200_OK)


class TeacherNotificationListCreateView(generics.ListCreateAPIView):
    """
    Teacher/Staff endpoint to view all notifications or broadcast a new announcement/awareness notification.
    """
    queryset = Notification.objects.all().order_by("-created_at")
    serializer_class = NotificationSerializer
    permission_classes = [IsTeacherOrStaffUser]

    def perform_create(self, serializer):
        teacher_name = self.request.data.get("teacher_name")
        if not teacher_name and self.request.user.is_authenticated:
            full_name = f"{self.request.user.first_name} {self.request.user.last_name}".strip()
            teacher_name = full_name or self.request.user.email
        serializer.save(
            created_by=self.request.user if self.request.user.is_authenticated else None,
            teacher_name=teacher_name or "Teacher",
        )


class TeacherNotificationDetailView(generics.RetrieveDestroyAPIView):
    """
    Teacher/Staff endpoint to view or delete a notification.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsTeacherOrStaffUser]


# ============================================================
# 🔒 SECURITY CREDENTIAL MANAGEMENT (With OTP Verification)
# ============================================================

class SecurityRequestOTPView(APIView):
    """
    Authenticated endpoint to request an OTP before altering security credentials
    (Change Password, Change Email, Change Phone Number).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        action = request.data.get("action")  # 'change_password', 'change_email', 'change_phone'
        target_value = (request.data.get("target_value") or "").strip()

        if action not in ["change_password", "change_email", "change_phone"]:
            return Response({"error": "Invalid security action requested."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        if action == "change_email":
            if not target_value or "@" not in target_value:
                return Response({"error": "Please provide a valid new email address."}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email__iexact=target_value).exclude(pk=user.pk).exists():
                return Response({"error": "This email address is already in use by another account."}, status=status.HTTP_400_BAD_REQUEST)

            code = f"{secrets.randbelow(900_000) + 100_000:06d}"
            user.otp = make_password(code)
            user.otp_created_at = timezone.now()
            user.otp_attempts = 0
            user.save(update_fields=["otp", "otp_created_at", "otp_attempts"])

            send_mail(
                "Your Tiny Talks Email Change Verification Code",
                f"Hello {user.first_name},\n\nYour OTP code to update your Tiny Talks email address to {target_value} is: {code}\nThis code expires in 10 minutes.",
                settings.DEFAULT_FROM_EMAIL,
                [target_value],
                fail_silently=False,
            )
            return Response({"message": f"Verification code sent to {target_value}."}, status=status.HTTP_200_OK)

        elif action == "change_phone":
            if not target_value:
                return Response({"error": "Please provide a valid phone number."}, status=status.HTTP_400_BAD_REQUEST)

            code = f"{secrets.randbelow(900_000) + 100_000:06d}"
            user.otp = make_password(code)
            user.otp_created_at = timezone.now()
            user.otp_attempts = 0
            user.save(update_fields=["otp", "otp_created_at", "otp_attempts"])

            send_mail(
                "Your Tiny Talks Phone Update Verification Code",
                f"Hello {user.first_name},\n\nYour OTP code to update your phone number on Tiny Talks is: {code}\nThis code expires in 10 minutes.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return Response({"message": f"Verification code sent to your registered email ({user.email})."}, status=status.HTTP_200_OK)

        elif action == "change_password":
            code = f"{secrets.randbelow(900_000) + 100_000:06d}"
            user.otp = make_password(code)
            user.otp_created_at = timezone.now()
            user.otp_attempts = 0
            user.save(update_fields=["otp", "otp_created_at", "otp_attempts"])

            send_mail(
                "Your Tiny Talks Password Change Verification Code",
                f"Hello {user.first_name},\n\nYour OTP code to change your Tiny Talks account password is: {code}\nThis code expires in 10 minutes.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return Response({"message": f"Verification code sent to your registered email ({user.email})."}, status=status.HTTP_200_OK)


class SecurityVerifyApplyView(APIView):
    """
    Authenticated endpoint to verify OTP and apply requested security credential update.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        action = request.data.get("action")
        otp = str(request.data.get("otp") or "").strip()
        new_value = (request.data.get("new_value") or "").strip()

        if not action or not otp or not new_value:
            return Response({"error": "Action, OTP verification code, and new value are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        if not user.verify_otp(otp):
            return Response({"error": "Invalid or expired verification code. Please request a new code."}, status=status.HTTP_400_BAD_REQUEST)

        if action == "change_password":
            try:
                validate_password(new_value, user=user)
            except DjangoValidationError as exc:
                return Response({"error": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_value)
            user.clear_otp()
            user.save(update_fields=["password"])
            return Response({"message": "Password updated successfully! Please use your new password next time you log in."}, status=status.HTTP_200_OK)

        elif action == "change_email":
            if "@" not in new_value:
                return Response({"error": "Invalid email address format."}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(email__iexact=new_value).exclude(pk=user.pk).exists():
                return Response({"error": "This email address is already taken."}, status=status.HTTP_400_BAD_REQUEST)

            user.email = new_value
            user.clear_otp()
            user.save(update_fields=["email"])
            return Response({"message": "Email address updated successfully!", "new_email": new_value}, status=status.HTTP_200_OK)

        elif action == "change_phone":
            user.contact_number = new_value
            user.clear_otp()
            user.save(update_fields=["contact_number"])
            return Response({"message": "Phone number updated successfully!", "new_phone": new_value}, status=status.HTTP_200_OK)

        return Response({"error": "Unknown security action."}, status=status.HTTP_400_BAD_REQUEST)

