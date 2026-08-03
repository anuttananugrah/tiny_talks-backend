from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from .serializers import UserRegistrationSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # TODO: Add your logic here to send user.otp to user.email via email (e.g., send_mail)

        return Response(
            {
                "message": "Registration successful. Please check your email for the verification OTP.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPView(APIView):
    """API endpoint to verify the email OTP."""

    permission_classes = [permissions.AllowAny]

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

        if user.otp == str(otp):
            user.is_verified = True
            user.otp = None  # Clear OTP after successful verification
            user.save()

            # Issue JWT tokens so the user is logged in automatically after OTP verification
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


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Please provide both email and password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if not user.is_verified:
                return Response(
                    {"error": "Please verify your email OTP before logging in."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login successful.",
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

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from .serializers import UserRegistrationSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """API endpoint for new user registration."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Optional: Generate JWT token immediately upon registration so user is logged in
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "User registered successfully.",
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """API endpoint to authenticate user and return JWT tokens."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Please provide both email and password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, email=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login successful.",
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
        # Always return the currently authenticated user
        return self.request.user