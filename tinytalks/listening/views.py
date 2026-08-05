from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Listening
from .serializers import ListeningSerializer

# Create your views here.

class VideoUploadAPIView(ListCreateAPIView):
    queryset = Listening.objects.all()
    serializer_class = ListeningSerializer
    parser_classes = [MultiPartParser, FormParser] # Required for handling files
