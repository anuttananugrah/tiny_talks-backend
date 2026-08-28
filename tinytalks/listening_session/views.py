from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from user.views import IsTeacherOrStaffUser

from listening_session.serializers import *
from .models import QuizAttempt, StoryQuestion, StoryVideo, UserAnswer


class StoryVideoListView(generics.ListAPIView):
    """
    Endpoint to list all available listening session videos.
    """
    queryset = StoryVideo.objects.all().order_by('-created_at')
    serializer_class = StoryVideoSerializer
    permission_classes = [permissions.IsAuthenticated]

class StoryVideoDetailView(generics.RetrieveAPIView):
    """
    Endpoint to get a single video and its associated questions.
    """
    queryset = StoryVideo.objects.all()
    serializer_class = StoryVideoSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubmitQuizView(APIView):
    """
    Custom endpoint to handle quiz submissions, calculate the score, 
    save the answers for the teacher, and enforce the 1-per-day rule.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, video_id):
        user = request.user
        today = timezone.now().date()

        # 1. Enforce the "1 quiz per day" rule
        if QuizAttempt.objects.filter(user=user, video_id=video_id, attempt_date=today).exists():
            return Response(
                {"detail": "You have already completed this story's quiz today. Great job! Come back tomorrow."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Fetch the video
        video = get_object_or_404(StoryVideo, id=video_id)

        # Expected frontend data format: {"answers": [{"question_id": 1, "selected_option": 2}, ...]}
        submitted_answers = request.data.get('answers', [])
        
        # 3. Create the attempt record (Score starts at 0, updated later)
        try:
            attempt = QuizAttempt.objects.create(
                user=user,
                video=video,
                score=0 
            )
        except IntegrityError:
            return Response(
                {"detail": "You have already completed this story's quiz today. Great job! Come back tomorrow."},
                status=status.HTTP_400_BAD_REQUEST
            )

        score = 0
        answer_records = []
        feedback_results = []

        # 4. Grade the quiz
        for item in submitted_answers:
            question_id = item.get('question_id')
            selected_option = item.get('selected_option')
            
            try:
                question = StoryQuestion.objects.get(id=question_id, video=video)
            except StoryQuestion.DoesNotExist:
                continue # Skip if question doesn't belong to this video

            # Check if answer is correct
            is_correct = (question.correct_option == selected_option)
            if is_correct:
                score += 1
                
            # Queue the answer for database insertion
            answer_records.append(
                UserAnswer(
                    attempt=attempt,
                    question=question,
                    selected_option=selected_option,
                    is_correct=is_correct
                )
            )
            
            # Queue the feedback to send back to React
            feedback_results.append({
                "question_id": question.id,
                "is_correct": is_correct,
                "correct_option": question.correct_option # Send correct option back so UI can highlight it
            })

        # 5. Bulk create all answers at once (Better performance)
        UserAnswer.objects.bulk_create(answer_records)

        # 6. Save the final calculated score
        attempt.score = score
        attempt.save()

        # 7. Return the final grade to the frontend
        return Response({
            "message": "Quiz submitted successfully!",
            "score": score,
            "total_questions": video.questions.count(),
            "results": feedback_results 
        }, status=status.HTTP_201_CREATED)

# --- 👩‍🏫 TEACHER DASHBOARD VIEWS ---

class TeacherVideoListCreateView(generics.ListCreateAPIView):
    """React Dashboard: Upload new videos or list them."""
    queryset = StoryVideo.objects.all().order_by('-created_at')
    serializer_class = TeacherStoryVideoSerializer
    permission_classes = [IsTeacherOrStaffUser]

    def perform_create(self, serializer):
        instance = serializer.save()
        try:
            from user.models import Notification
            teacher = (
                f"{self.request.user.first_name} {self.request.user.last_name}".strip()
                if self.request.user.is_authenticated else "Teacher"
            )
            Notification.objects.create(
                title=f"🎧 New Listening Story: {instance.title}",
                message=f"New story video '{instance.title}' has been uploaded with a quiz challenge!",
                notification_type="listening",
                teacher_name=teacher or "Teacher",
                link="/listening",
                created_by=self.request.user if self.request.user.is_authenticated else None,
            )
        except Exception:
            pass

class TeacherVideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """React Dashboard: Edit or delete a specific video."""
    queryset = StoryVideo.objects.all()
    serializer_class = TeacherStoryVideoSerializer
    permission_classes = [IsTeacherOrStaffUser]

# 2. Manage Questions
class TeacherQuestionListCreateView(generics.ListCreateAPIView):
    """React Dashboard: Add a question to a specific video."""
    serializer_class = TeacherStoryQuestionSerializer
    permission_classes = [IsTeacherOrStaffUser]

    def get_queryset(self):
        return StoryQuestion.objects.filter(video_id=self.kwargs['video_id'])

    def perform_create(self, serializer):
        video = get_object_or_404(StoryVideo, id=self.kwargs['video_id'])
        serializer.save(video=video)

class TeacherQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """React Dashboard: Edit or delete a specific question."""
    queryset = StoryQuestion.objects.all()
    serializer_class = TeacherStoryQuestionSerializer
    permission_classes = [IsTeacherOrStaffUser]

# 3. View Student Results
class TeacherQuizResultListView(generics.ListAPIView):
    """React Dashboard: See all student quiz attempts and scores."""
    queryset = (
        QuizAttempt.objects
        .select_related('user', 'video')
        .prefetch_related('answers__question')
        .order_by('-created_at')
    )
    serializer_class = TeacherQuizAttemptSerializer
    permission_classes = [IsTeacherOrStaffUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        video_id = self.request.query_params.get('video_id')
        student_id = self.request.query_params.get('student_id')
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        if student_id:
            queryset = queryset.filter(user_id=student_id)
        return queryset