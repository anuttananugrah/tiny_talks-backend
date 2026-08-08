from django.urls import path
from .views import (
    StoryVideoListView, StoryVideoDetailView, SubmitQuizView,
    TeacherVideoListCreateView, TeacherVideoDetailView,
    TeacherQuestionListCreateView, TeacherQuestionDetailView,
    TeacherQuizResultListView
)

urlpatterns = [
    # --- 👧 STUDENT ROUTES ---
    path('videos/', StoryVideoListView.as_view(), name='story-video-list'),
    path('videos/<int:pk>/', StoryVideoDetailView.as_view(), name='story-video-detail'),
    path('videos/<int:video_id>/submit-quiz/', SubmitQuizView.as_view(), name='submit-quiz'),

    # --- 👩‍🏫 TEACHER DASHBOARD ROUTES ---
    path('manage/videos/', TeacherVideoListCreateView.as_view(), name='teacher-video-list'),
    path('manage/videos/<int:pk>/', TeacherVideoDetailView.as_view(), name='teacher-video-detail'),
    path('manage/videos/<int:video_id>/questions/', TeacherQuestionListCreateView.as_view(), name='teacher-question-list'),
    path('manage/questions/<int:pk>/', TeacherQuestionDetailView.as_view(), name='teacher-question-detail'),
    path('manage/results/', TeacherQuizResultListView.as_view(), name='teacher-quiz-results'),
]