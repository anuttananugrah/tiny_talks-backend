from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from .models import ReadingStory, ReadingStoryPage, ReadingQuestion, ReadingQuizAttempt, ReadingUserAnswer
from .serializers import (
    ReadingStorySerializer, ReadingStoryPageSerializer, ReadingStoryQuestionSerializer, ReadingQuizAttemptSerializer,
    TeacherReadingStorySerializer, TeacherReadingStoryPageSerializer, TeacherReadingStoryQuestionSerializer, TeacherReadingQuizAttemptSerializer
)

# ==============================================================
# STUDENT API ENDPOINTS
# ==============================================================

class StudentStoryListView(generics.ListAPIView):
    """List all stories for students"""
    permission_classes = [IsAuthenticated]
    queryset = ReadingStory.objects.all().order_by('-created_at')
    serializer_class = ReadingStorySerializer

class StudentStoryDetailView(generics.RetrieveAPIView):
    """Get a specific story (includes pages and questions without correct answers)"""
    permission_classes = [IsAuthenticated]
    queryset = ReadingStory.objects.all()
    serializer_class = ReadingStorySerializer

class StudentSubmitQuizView(APIView):
    """Submit quiz answers for a reading story"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        story = get_object_or_404(ReadingStory, pk=pk)
        answers_data = request.data.get('answers', [])
        
        if not answers_data:
            return Response({"detail": "No answers provided."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Check if user already attempted today
        try:
            attempt = ReadingQuizAttempt.objects.create(
                user=request.user,
                story=story,
            )
        except IntegrityError:
            return Response({"detail": "You have already attempted this story's quiz today."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Grade the answers
        score = 0
        total_questions = story.questions.count()
        results_data = []

        for item in answers_data:
            q_id = item.get('question_id')
            selected = item.get('selected_option')
            
            try:
                question = ReadingQuestion.objects.get(id=q_id, story=story)
            except ReadingQuestion.DoesNotExist:
                continue

            is_correct = (selected == question.correct_option)
            if is_correct:
                score += 1
                
            ReadingUserAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_option=selected,
                is_correct=is_correct
            )
            
            results_data.append({
                "question_id": question.id,
                "is_correct": is_correct,
                "correct_option": question.correct_option
            })

        # 3. Save final score
        attempt.score = score
        attempt.save()

        return Response({
            "detail": "Quiz submitted successfully!",
            "score": score,
            "total_questions": total_questions,
            "results": results_data
        }, status=status.HTTP_201_CREATED)


from user.views import IsTeacherOrStaffUser

# ==============================================================
# TEACHER DASHBOARD API ENDPOINTS
# ==============================================================

class TeacherStoryListCreateView(generics.ListCreateAPIView):
    """Teachers list their own stories and create new ones"""
    permission_classes = [IsTeacherOrStaffUser]
    serializer_class = TeacherReadingStorySerializer

    def get_queryset(self):
        return ReadingStory.objects.filter(teacher=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        instance = serializer.save(teacher=self.request.user)
        try:
            from user.models import Notification
            teacher = (
                f"{self.request.user.first_name} {self.request.user.last_name}".strip()
                if self.request.user.is_authenticated else "Teacher"
            )
            Notification.objects.create(
                title=f"📖 New Storybook: {instance.title}",
                message=f"New storybook '{instance.title}' is available to read with fun pages and a quiz!",
                notification_type="reading",
                teacher_name=teacher or "Teacher",
                link="/reading",
                created_by=self.request.user if self.request.user.is_authenticated else None,
            )
        except Exception:
            pass

class TeacherStoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Teachers update/delete their own stories"""
    permission_classes = [IsTeacherOrStaffUser]
    serializer_class = TeacherReadingStorySerializer

    def get_queryset(self):
        return ReadingStory.objects.filter(teacher=self.request.user)

class TeacherStoryPageCreateView(generics.CreateAPIView):
    """Add a page to a specific story (must be owned by the teacher)"""
    permission_classes = [IsTeacherOrStaffUser]
    serializer_class = TeacherReadingStoryPageSerializer

    def perform_create(self, serializer):
        story = get_object_or_404(ReadingStory, pk=self.kwargs['story_pk'], teacher=self.request.user)
        serializer.save(story=story)

class TeacherStoryPageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Update/delete a specific page (must belong to a story owned by the teacher)"""
    permission_classes = [IsTeacherOrStaffUser]
    serializer_class = TeacherReadingStoryPageSerializer

    def get_queryset(self):
        return ReadingStoryPage.objects.filter(story__teacher=self.request.user)

class TeacherStoryQuestionCreateView(generics.CreateAPIView):
    """Add a question to a specific story (must be owned by the teacher)"""
    permission_classes = [IsTeacherOrStaffUser]
    serializer_class = TeacherReadingStoryQuestionSerializer

    def perform_create(self, serializer):
        story = get_object_or_404(ReadingStory, pk=self.kwargs['story_pk'], teacher=self.request.user)
        serializer.save(story=story)

class TeacherStoryQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Update/delete a specific question (must belong to a story owned by the teacher)"""
    permission_classes = [IsTeacherOrStaffUser]
    serializer_class = TeacherReadingStoryQuestionSerializer

    def get_queryset(self):
        return ReadingQuestion.objects.filter(story__teacher=self.request.user)

class TeacherQuizResultListView(generics.ListAPIView):
    """Teachers view results for their stories"""
    permission_classes = [IsTeacherOrStaffUser]
    serializer_class = TeacherReadingQuizAttemptSerializer

    def get_queryset(self):
        return ReadingQuizAttempt.objects.filter(story__teacher=self.request.user).order_by('-created_at')
