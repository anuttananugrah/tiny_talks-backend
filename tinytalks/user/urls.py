from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    VerifyOTPView,
    LoginView,
    UserProfileView,
    CustomTokenObtainPairView,TeacherStudentListView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('manage/students/', TeacherStudentListView.as_view(), name='teacher-student-list'),
    # SimpleJWT endpoints
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/obtain/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]