from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import StoryVideo, StoryQuestion, QuizAttempt, UserAnswer
from listening_session.serializers import *

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
        try:
            video = StoryVideo.objects.get(id=video_id)
        except StoryVideo.DoesNotExist:
            return Response({"detail": "Video not found."}, status=status.HTTP_404_NOT_FOUND)

        # Expected frontend data format: {"answers": [{"question_id": 1, "selected_option": 2}, ...]}
        submitted_answers = request.data.get('answers', [])
        
        # 3. Create the attempt record (Score starts at 0, updated later)
        attempt = QuizAttempt.objects.create(
            user=user,
            video=video,
            score=0 
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

# Make sure your IsStaffUser permission from live_session is imported or recreated here
class IsStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

# --- 👩‍🏫 TEACHER DASHBOARD VIEWS ---

# 1. Manage Videos
class TeacherVideoListCreateView(generics.ListCreateAPIView):
    """React Dashboard: Upload new videos or list them."""
    queryset = StoryVideo.objects.all().order_by('-created_at')
    serializer_class = TeacherStoryVideoSerializer
    permission_classes = [IsStaffUser]

class TeacherVideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """React Dashboard: Edit or delete a specific video."""
    queryset = StoryVideo.objects.all()
    serializer_class = TeacherStoryVideoSerializer
    permission_classes = [IsStaffUser]

# 2. Manage Questions
class TeacherQuestionListCreateView(generics.ListCreateAPIView):
    """React Dashboard: Add a question to a specific video."""
    serializer_class = TeacherStoryQuestionSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        return StoryQuestion.objects.filter(video_id=self.kwargs['video_id'])

    def perform_create(self, serializer):
        video = StoryVideo.objects.get(id=self.kwargs['video_id'])
        serializer.save(video=video)

class TeacherQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """React Dashboard: Edit or delete a specific question."""
    queryset = StoryQuestion.objects.all()
    serializer_class = TeacherStoryQuestionSerializer
    permission_classes = [IsStaffUser]

# 3. View Student Results
class TeacherQuizResultListView(generics.ListAPIView):
    """React Dashboard: See all student quiz attempts and scores."""
    queryset = QuizAttempt.objects.all().order_by('-created_at')
    serializer_class = TeacherQuizAttemptSerializer
    permission_classes = [IsStaffUser]
    
    # Optional: Filter by specific video if passed in URL
    def get_queryset(self):
        queryset = super().get_queryset()
        video_id = self.request.query_params.get('video_id')
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        return queryset