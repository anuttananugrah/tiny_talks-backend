from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class LiveClass(models.Model):
    TINT_CHOICES = (
        ('#FF4D8D', 'Pink'),
        ('#3B9CF2', 'Blue'),
        ('#FFA531', 'Orange'),
        ('#9B6BE0', 'Purple'),
    )

    title = models.CharField(max_length=150, help_text="e.g., Speaking Time, Listen & Learn")
    lesson = models.CharField(max_length=255, help_text="e.g., Lesson 4: My Favourite Animal")
    teacher_name = models.CharField(max_length=100, help_text="e.g., Ms. Meera")
    
    # ⚡ NEW: Class Date field added here!
    class_date = models.DateField(null=True, blank=True, help_text="Scheduled class date")
    
    duration_minutes = models.PositiveIntegerField(default=20, help_text="Duration in minutes")
    class_time = models.TimeField(help_text="Scheduled class time")
    
    rating = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )

    is_live = models.BooleanField(default=False, help_text="Mark if this class is currently live")
    is_today = models.BooleanField(default=True, help_text="Display on Today's Class section")

    tint_color = models.CharField(
        max_length=10, 
        choices=TINT_CHOICES, 
        default='#FF4D8D',
        help_text="Border and theme accent color"
    )

    # 🖼️ Teacher Uploaded Thumbnail Image
    thumbnail = models.ImageField(
        upload_to='live_classes/thumbnails/',
        blank=True,
        null=True,
        help_text="Upload custom teacher/class thumbnail image"
    )

    meeting_link = models.URLField(blank=True, null=True, help_text="URL to join the live session (Zoom/Meet)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_time', '-is_live']
        verbose_name = "Live Class"
        verbose_name_plural = "Live Classes"

    def __str__(self):
        return f"{self.title} - {self.lesson} ({self.teacher_name})"