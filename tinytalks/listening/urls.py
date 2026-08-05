from django.urls import path
from listening.views import ListCreateAPIView


urlpatterns=[
    path("/listening/",ListCreateAPIView.as_view(),name="listening")
]