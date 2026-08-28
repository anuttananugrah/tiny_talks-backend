from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from user.views import IsTeacherOrStaffUser
from .models import LiveClass
from .serializers import LiveClassSerializer


class TodayLiveClassListView(generics.ListAPIView):
    """
    Public / Authenticated endpoint to retrieve today's live classes.
    Supports optional category filtering via query param: ?category=Listening
    """
    serializer_class = LiveClassSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = LiveClass.objects.filter(is_today=True)
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(title__iexact=category)
        return queryset

class LiveClassDetailView(generics.RetrieveAPIView):
    """
    Retrieve details for a single live class by ID.
    """
    queryset = LiveClass.objects.all()
    serializer_class = LiveClassSerializer
    permission_classes = [permissions.AllowAny]

# --- 👩‍🏫 NEW TEACHER VIEWS FOR THE DASHBOARD ---

class TeacherLiveClassListCreateView(generics.ListCreateAPIView):
    """Teacher endpoint to list all classes or create a new class."""
    queryset = LiveClass.objects.all().order_by('-created_at')
    serializer_class = LiveClassSerializer
    permission_classes = [IsTeacherOrStaffUser]

    def perform_create(self, serializer):
        instance = serializer.save()
        try:
            from user.models import Notification
            teacher = instance.teacher_name or (
                f"{self.request.user.first_name} {self.request.user.last_name}".strip()
                if self.request.user.is_authenticated else "Teacher"
            )
            time_str = instance.class_time.strftime("%I:%M %p") if hasattr(instance.class_time, "strftime") else str(instance.class_time)
            Notification.objects.create(
                title=f"🎥 New Live Class: {instance.title}",
                message=f"Live class '{instance.lesson or instance.title}' is scheduled for {instance.class_date} at {time_str}.",
                notification_type="class",
                teacher_name=teacher or "Teacher",
                link="/live-class",
                created_by=self.request.user if self.request.user.is_authenticated else None,
            )
        except Exception:
            pass


class TeacherLiveClassDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Teacher endpoint to edit or delete a class."""
    queryset = LiveClass.objects.all()
    serializer_class = LiveClassSerializer
    permission_classes = [IsTeacherOrStaffUser]