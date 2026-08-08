from django.contrib import admin
from .models import StoryVideo, StoryQuestion, QuizAttempt, UserAnswer

# 1. Allows teachers to add questions while uploading the video!
class StoryQuestionInline(admin.TabularInline):
    model = StoryQuestion
    extra = 3 # Shows 3 empty question slots by default

@admin.register(StoryVideo)
class StoryVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    inlines = [StoryQuestionInline] # Connects the questions to the video form

# 2. Allows teachers to see exactly which option the student clicked!
class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'is_correct')
    can_delete = False

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'score', 'attempt_date')
    list_filter = ('attempt_date', 'video')
    search_fields = ('user__email', 'video__title')
    inlines = [UserAnswerInline] # Connects the student's answers to their attempt log
    readonly_fields = ('user', 'video', 'score', 'attempt_date')