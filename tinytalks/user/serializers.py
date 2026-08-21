from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import AuthenticationFailed
from user.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Token Serializer returning user metadata during login.
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_verified:
            raise AuthenticationFailed("Please verify your email before signing in.")

        data["is_staff"] = self.user.is_staff
        data["role"] = getattr(self.user, "role", "student")
        data["email"] = self.user.email
        data["first_name"] = self.user.first_name
        data["last_name"] = self.user.last_name
        data["is_verified"] = self.user.is_verified

        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "gender",
            "dob",
            "guardian_name",
            "contact_number",
            "password",
            "confirm_password",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Password fields do not match."}
            )
        user = User(
            email=attrs.get("email", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        validate_password(attrs["password"], user=user)
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password, is_verified=False, **validated_data
        )

        user.generate_otp()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for fetching and updating user profiles."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_staff",
            "gender",
            "dob",
            "guardian_name",
            "contact_number",
            "profile_image",
            "is_verified",
        ]
        read_only_fields = ["id", "email", "role", "is_verified", "is_staff"]

    def validate_profile_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Profile images must be 5 MB or smaller.")
        return value

class StudentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'contact_number', 'guardian_name', 'gender', 'dob',
            'profile_image', 'date_joined',
        ]
