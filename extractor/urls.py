# extractor/urls.py
from django.urls import path
from .views import OCRExtractorAPIView

urlpatterns = [
    path('extract/', OCRExtractorAPIView.as_view(), name='ocr_extractor'),
]