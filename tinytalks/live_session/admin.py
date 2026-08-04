from django.contrib import admin
from django.utils.html import format_html
from .models import LiveClass


@admin.register(LiveClass)
class LiveClassAdmin(admin.ModelAdmin):
    list_display = [
        'thumbnail_preview',
        'title',
        'lesson',
        'teacher_name',
        'class_time',
        'duration_minutes',
        'is_live',
        'is_today',
        'tint_color',
    ]
    list_filter = ['is_live', 'is_today', 'tint_color', 'teacher_name']
    search_fields = ['title', 'lesson', 'teacher_name']
    list_editable = ['is_live', 'is_today', 'class_time']

    fieldsets = (
        ('Class Information', {
            'fields': ('title', 'lesson', 'teacher_name', 'rating', 'thumbnail')
        }),
        ('Schedule & Status', {
            'fields': ('class_time', 'duration_minutes', 'is_live', 'is_today', 'meeting_link')
        }),
        ('Visual Theme', {
            'fields': ('tint_color',)
        }),
    )

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="width: 45px; height: 45px; border-radius: 8px; object-fit: cover;" />', obj.thumbnail.url)
        return "No Image"

    thumbnail_preview.short_description = 'Thumbnail'