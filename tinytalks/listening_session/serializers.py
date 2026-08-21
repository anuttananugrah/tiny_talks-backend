from user.serializers import StudentListSerializer
from .models import UserAnswer # Make sure to import this at the top
from rest_framework import serializers
from .models import StoryVideo, StoryQuestion, QuizAttempt, UserAnswer

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024


def validate_image_upload(value):
    if value.size > MAX_IMAGE_SIZE:
        raise serializers.ValidationError("Images must be 5 MB or smaller.")
    return value


def validate_video_upload(value):
    extension = "." + value.name.rsplit(".", 1)[-1].lower() if "." in value.name else ""
    if extension not in {".mp4", ".webm"} or value.size > MAX_VIDEO_SIZE:
        raise serializers.ValidationError("Upload an MP4 or WebM video no larger than 50 MB.")
    return value

class StoryQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryQuestion
        # Notice 'correct_option' is EXCLUDED so users cannot cheat!
        fields = ['id', 'question_text', 'option_1', 'option_2', 'option_3', 'option_4']

class StoryVideoSerializer(serializers.ModelSerializer):
    # This nests the questions inside the video response
    questions = StoryQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = StoryVideo
        fields = ['id', 'title', 'description', 'video_url', 'video_file', 'thumbnail', 'created_at', 'questions']

class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'user', 'video', 'score', 'attempt_date']


# --- 👩‍🏫 TEACHER DASHBOARD SERIALIZERS ---

class TeacherStoryQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryQuestion
        fields = '__all__' # Teachers need to see and edit the correct_option!

class TeacherStoryVideoSerializer(serializers.ModelSerializer):
    questions = TeacherStoryQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = StoryVideo
        fields = ['id', 'title', 'description', 'video_url', 'video_file', 'thumbnail', 'created_at', 'questions']

    def validate_video_file(self, value):
        return validate_video_upload(value)

    def validate_thumbnail(self, value):
        return validate_image_upload(value)

class TeacherUserAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_option = serializers.IntegerField(source='question.correct_option', read_only=True)

    class Meta:
        model = UserAnswer
        fields = ['id', 'question_text', 'selected_option', 'correct_option', 'is_correct']


class TeacherQuizAttemptSerializer(serializers.ModelSerializer):
    student = StudentListSerializer(source='user', read_only=True)
    video_title = serializers.CharField(source='video.title', read_only=True)
    answers = TeacherUserAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'student', 'video_title', 'score', 'attempt_date', 'created_at', 'answers']
