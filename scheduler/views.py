from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from scheduler.services import generate_schedule, generate_gantt_html, generate_heatmap_html
from .serializers import OperationPlanRequestSerializer

class GenerateOperationPlanView(APIView):
    def post(self, request):
        serializer = OperationPlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
        result = generate_schedule(serializer.validated_data)
        
        if not result:
            return Response({"error": "Plan bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
            
        return Response(result, status=status.HTTP_200_OK)

class VisualizePlanView(APIView):
    def post(self, request):
        serializer = OperationPlanRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            
            schedule = generate_schedule(serializer.validated_data)
            html = generate_gantt_html(schedule)
            return HttpResponse(html, content_type='text/html')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VisualizeHeatmapView(APIView):
    def post(self, request):
        serializer = OperationPlanRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            
            schedule = generate_schedule(serializer.validated_data)
            html = generate_heatmap_html(schedule)
            return HttpResponse(html, content_type='text/html')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)