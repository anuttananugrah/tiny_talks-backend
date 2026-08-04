from django.urls import path
from .views import (
    TodayLiveClassListView, 
    LiveClassDetailView,
    TeacherLiveClassListCreateView,
    TeacherLiveClassDetailView
)

urlpatterns = [
    # Public Routes
    path('today/', TodayLiveClassListView.as_view(), name='today-live-classes'),
    path('<int:pk>/', LiveClassDetailView.as_view(), name='live-class-detail'),
    
    # 👩‍🏫 Teacher Admin Routes
    path('manage/', TeacherLiveClassListCreateView.as_view(), name='teacher-class-list-create'),
    path('manage/<int:pk>/', TeacherLiveClassDetailView.as_view(), name='teacher-class-detail'),
]