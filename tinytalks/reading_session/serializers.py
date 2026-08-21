from rest_framework import serializers
from user.serializers import StudentListSerializer
from .models import ReadingStory, ReadingStoryPage, ReadingQuestion, ReadingQuizAttempt, ReadingUserAnswer
from listening_session.serializers import validate_image_upload

# --- STUDENT SERIALIZERS ---

class ReadingStoryPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingStoryPage
        fields = ['id', 'page_number', 'content', 'image']

class ReadingStoryQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingQuestion
        # Hide correct_option from students
        fields = ['id', 'question_text', 'option_1', 'option_2', 'option_3', 'option_4']

class ReadingStorySerializer(serializers.ModelSerializer):
    pages = ReadingStoryPageSerializer(many=True, read_only=True)
    questions = ReadingStoryQuestionSerializer(many=True, read_only=True)
    teacher_name = serializers.CharField(source='teacher.first_name', read_only=True)

    class Meta:
        model = ReadingStory
        fields = ['id', 'title', 'description', 'cover_image', 'teacher_name', 'created_at', 'pages', 'questions']

class ReadingQuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingQuizAttempt
        fields = ['id', 'user', 'story', 'score', 'attempt_date']


# --- TEACHER DASHBOARD SERIALIZERS ---

class TeacherReadingStoryPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingStoryPage
        fields = '__all__'

    def validate_image(self, value):
        return validate_image_upload(value)

class TeacherReadingStoryQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingQuestion
        fields = '__all__'

class TeacherReadingStorySerializer(serializers.ModelSerializer):
    pages = TeacherReadingStoryPageSerializer(many=True, read_only=True)
    questions = TeacherReadingStoryQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReadingStory
        # Note: 'teacher' field is set automatically in views, but we can return it
        fields = ['id', 'title', 'description', 'cover_image', 'teacher', 'created_at', 'pages', 'questions']
        read_only_fields = ['teacher']

    def validate_cover_image(self, value):
        return validate_image_upload(value)

class TeacherReadingUserAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_option = serializers.IntegerField(source='question.correct_option', read_only=True)

    class Meta:
        model = ReadingUserAnswer
        fields = ['id', 'question_text', 'selected_option', 'correct_option', 'is_correct']

class TeacherReadingQuizAttemptSerializer(serializers.ModelSerializer):
    student = StudentListSerializer(source='user', read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)
    answers = TeacherReadingUserAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = ReadingQuizAttempt
        fields = ['id', 'student', 'story_title', 'score', 'attempt_date', 'created_at', 'answers']
