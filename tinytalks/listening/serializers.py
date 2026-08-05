from rest_framework import serializers
from .models import Listening

class ListeningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listening
        fields = ['id', 'title', 'video_file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    # Optional: Validate file size (e.g., limit to 50MB)
    def validate_video_file(self, value):
        max_size = 50 * 1024 * 1024 # 50 Megabytes
        if value.size > max_size:
            raise serializers.ValidationError("Video file size cannot exceed 50MB.")
        return value