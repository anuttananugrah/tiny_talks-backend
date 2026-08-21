from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ReadingStory(models.Model):
    title = models.CharField(max_length=200, help_text="e.g., The Lion and the Mouse")
    description = models.TextField(blank=True, help_text="Story description")
    cover_image = models.ImageField(upload_to='reading_covers/', blank=True, null=True, help_text="Cover image for the story card")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_stories', help_text="The teacher who created this story")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (by {self.teacher.email})"

class ReadingStoryPage(models.Model):
    story = models.ForeignKey(ReadingStory, on_delete=models.CASCADE, related_name='pages')
    page_number = models.PositiveIntegerField(help_text="Page sequence number (1, 2, 3...)")
    content = models.TextField(help_text="The text content of the page")
    image = models.ImageField(upload_to='reading_pages/', blank=True, null=True, help_text="Optional illustration for the page")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page_number']
        unique_together = ['story', 'page_number']

    def __str__(self):
        return f"{self.story.title} - Page {self.page_number}"

class ReadingQuestion(models.Model):
    OPTION_CHOICES = (
        (1, 'Option 1'),
        (2, 'Option 2'),
        (3, 'Option 3'),
        (4, 'Option 4'),
    )
    
    story = models.ForeignKey(ReadingStory, on_delete=models.CASCADE, related_name='questions')
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

class ReadingQuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_quiz_attempts')
    story = models.ForeignKey(ReadingStory, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.IntegerField(default=0, help_text="Total correct answers")
    
    # Enforce 1 user can only attend 1 story quiz per day
    attempt_date = models.DateField(auto_now_add=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'story', 'attempt_date']

    def __str__(self):
        return f"{self.user.email} - {self.story.title} (Score: {self.score})"

class ReadingUserAnswer(models.Model):
    attempt = models.ForeignKey(ReadingQuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(ReadingQuestion, on_delete=models.CASCADE)
    selected_option = models.IntegerField(help_text="The option (1-4) the user clicked")
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.attempt.user.email} -> Q: {self.question.question_text[:20]}..."
