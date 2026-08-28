from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, ResendOTPView,
    VerifyOTPView,
    LoginView,
    UserProfileView,
    CustomTokenObtainPairView, TeacherStudentListView,
    ForgotPasswordView, VerifyResetOTPView, ResetPasswordView,
    NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView,
    TeacherNotificationListCreateView, TeacherNotificationDetailView,
    SecurityRequestOTPView, SecurityVerifyApplyView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('manage/students/', TeacherStudentListView.as_view(), name='teacher-student-list'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-reset-otp/', VerifyResetOTPView.as_view(), name='verify-reset-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # 🔒 Student & User Security endpoints (OTP protected)
    path('security/request-otp/', SecurityRequestOTPView.as_view(), name='security-request-otp'),
    path('security/verify-apply/', SecurityVerifyApplyView.as_view(), name='security-verify-apply'),

    # 🔔 Student Notification endpoints
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),

    # 👩‍🏫 Teacher Notification Management endpoints
    path('manage/notifications/', TeacherNotificationListCreateView.as_view(), name='teacher-notification-manage'),
    path('manage/notifications/<int:pk>/', TeacherNotificationDetailView.as_view(), name='teacher-notification-detail'),

    # SimpleJWT endpoints
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/obtain/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]

