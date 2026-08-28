from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from user.models import User
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer, StudentListSerializer
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
            return Response(
                {
                    "message": "Login successful.",
                    "is_staff": user.is_staff,
                    "role": getattr(user, "role", "student"),
                    "user": UserSerializer(user).data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
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
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    serializer_class = StudentListSerializer
    permission_classes = [IsTeacherOrStaffUser]


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
