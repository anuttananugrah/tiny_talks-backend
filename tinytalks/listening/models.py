from django.db import models
from django.core.validators import FileExtensionValidator

# Create your models here.

class Listening(models.Model):
    title=models.CharField(max_length=100)
    video_file = models.FileField(upload_to='videos/', validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'mkv', 'avi'])])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title