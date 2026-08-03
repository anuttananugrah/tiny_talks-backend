from rest_framework import serializers
from user.models import User



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
            "role",
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
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        # Explicitly set is_verified to False for new users
        user = User.objects.create_user(
            password=password, is_verified=False, **validated_data
        )

        # Generate the OTP stored in the model
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
            "gender",
            "dob",
            "guardian_name",
            "contact_number",
            "profile_image",
            "is_verified",
        ]
        read_only_fields = ["id", "email", "is_verified"]