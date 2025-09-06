from django.shortcuts import render

# Create your views here.
# extractor/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .processing_logic import process_file


class OCRExtractorAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.data.get('file')

        if not file_obj:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            # Call the unified processing function
            extracted_data = process_file(file_obj)
            return Response(extracted_data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)