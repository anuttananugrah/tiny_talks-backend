from django.urls import path
from . import views

urlpatterns = [
    # Student Routes
    path('stories/', views.StudentStoryListView.as_view(), name='student-stories-list'),
    path('stories/<int:pk>/', views.StudentStoryDetailView.as_view(), name='student-stories-detail'),
    path('stories/<int:pk>/submit-quiz/', views.StudentSubmitQuizView.as_view(), name='student-submit-quiz'),

    # Teacher Routes
    path('manage/stories/', views.TeacherStoryListCreateView.as_view(), name='teacher-stories-list-create'),
    path('manage/stories/<int:pk>/', views.TeacherStoryDetailView.as_view(), name='teacher-stories-detail'),
    path('manage/stories/<int:story_pk>/pages/', views.TeacherStoryPageCreateView.as_view(), name='teacher-pages-create'),
    path('manage/pages/<int:pk>/', views.TeacherStoryPageDetailView.as_view(), name='teacher-pages-detail'),
    path('manage/stories/<int:story_pk>/questions/', views.TeacherStoryQuestionCreateView.as_view(), name='teacher-questions-create'),
    path('manage/questions/<int:pk>/', views.TeacherStoryQuestionDetailView.as_view(), name='teacher-questions-detail'),
    path('manage/results/', views.TeacherQuizResultListView.as_view(), name='teacher-results-list'),
]
