from rest_framework import serializers
from .models import LiveClass


class LiveClassSerializer(serializers.ModelSerializer):
    formatted_time = serializers.SerializerMethodField()
    thumbnail = serializers.ImageField(use_url=True, required=False, allow_null=True)

    class Meta:
        model = LiveClass
        fields = [
            'id',
            'title',
            'lesson',
            'teacher_name',
            'class_date',
            'duration_minutes',
            'class_time',
            'formatted_time',
            'rating',
            'status',
            'is_today',
            'tint_color',
            'thumbnail',
            'meeting_link',
        ]

    def get_formatted_time(self, obj):
        return obj.class_time.strftime("%I:%M %p").lstrip('0')