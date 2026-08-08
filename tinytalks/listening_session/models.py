from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class StoryVideo(models.Model):
    title = models.CharField(max_length=200, help_text="e.g., The Lion and the Mouse")
    description = models.TextField(blank=True, help_text="Story description")
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or external video link")
    video_file = models.FileField(upload_to='story_videos/', blank=True, null=True, help_text="Or upload MP4 file directly")
    thumbnail = models.ImageField(upload_to='story_thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class StoryQuestion(models.Model):
    OPTION_CHOICES = (
        (1, 'Option 1'),
        (2, 'Option 2'),
        (3, 'Option 3'),
        (4, 'Option 4'),
    )
    
    video = models.ForeignKey(StoryVideo, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500, help_text="e.g., What did the mouse do?")
    
    # The 4 Options
    option_1 = models.CharField(max_length=200)
    option_2 = models.CharField(max_length=200)
    option_3 = models.CharField(max_length=200)
    option_4 = models.CharField(max_length=200)
    
    # Admin selects which option is correct
    correct_option = models.IntegerField(choices=OPTION_CHOICES, help_text="Which option is the correct answer?")

    def __str__(self):
        return self.question_text

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    video = models.ForeignKey(StoryVideo, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.IntegerField(default=0, help_text="Total correct answers")
    
    # ⚡ This helps enforce the "1 user can only attend 1 video quiz per day" rule
    attempt_date = models.DateField(auto_now_add=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Blocks the database from saving more than 1 attempt per video, per user, per day!
        unique_together = ['user', 'video', 'attempt_date']

    def __str__(self):
        return f"{self.user.email} - {self.video.title} (Score: {self.score})"

class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(StoryQuestion, on_delete=models.CASCADE)
    selected_option = models.IntegerField(help_text="The option (1-4) the user clicked")
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.attempt.user.email} -> Q: {self.question.question_text[:20]}..."