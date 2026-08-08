from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class LiveClass(models.Model):
    TINT_CHOICES = (
        ('#FF4D8D', 'Pink'),
        ('#3B9CF2', 'Blue'),
        ('#FFA531', 'Orange'),
        ('#9B6BE0', 'Purple'),
    )

    # ⚡ NEW: Status Choices
    STATUS_CHOICES = (
        ('scheduled', '🟡 Scheduled'),
        ('live', '🔴 In Progress (Live)'),
        ('completed', '🟢 Completed'),
    )

    title = models.CharField(max_length=150, help_text="e.g., Speaking Time, Listen & Learn")
    lesson = models.CharField(max_length=255, help_text="e.g., Lesson 4: My Favourite Animal")
    teacher_name = models.CharField(max_length=100, help_text="e.g., Ms. Meera")
    
    class_date = models.DateField(null=True, blank=True, help_text="Scheduled class date")
    duration_minutes = models.PositiveIntegerField(default=20, help_text="Duration in minutes")
    class_time = models.TimeField(help_text="Scheduled class time")
    
    rating = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])

    # ⚡ REPLACED: is_live and is_today are gone. We use status now!
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    tint_color = models.CharField(max_length=10, choices=TINT_CHOICES, default='#FF4D8D')
    thumbnail = models.ImageField(upload_to='live_classes/thumbnails/', blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_time']
        verbose_name = "Live Class"

    def __str__(self):
        return f"{self.title} - {self.lesson} ({self.get_status_display()})"

    # ⚡ DYNAMIC PROPERTY: Automatically checks if class_date is today!
    @property
    def is_today(self):
        if self.class_date:
            return self.class_date == timezone.now().date()
        return False