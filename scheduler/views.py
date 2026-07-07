from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import OperationPlanRequestSerializer
from .services import generate_schedule, generate_gantt_html, generate_heatmap_html
from django.http import HttpResponse


class GenerateOperationPlanView(APIView):
    def post(self,request):
        serializer = OperationPlanRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            schedule_result = generate_schedule(serializer.validated_data)
            
            return Response(schedule_result,status=status.HTTP_200_OK)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisualizeOperationPlanView(APIView):
    def post(self,request):
        serializer = OperationPlanRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            schedule_result = generate_schedule(serializer.validated_data)
            gantt_html = generate_gantt_html(schedule_result)
            
            return HttpResponse(gantt_html, content_type='text/html')
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
class VisualizeOperationHeatMapView(APIView):
    def post(self,request):
        serializer = OperationPlanRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            schedule_result = generate_schedule(serializer.validated_data)
            heatmap_html = generate_heatmap_html(schedule_result)
            
            return HttpResponse(heatmap_html,content_type='text/html')
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)