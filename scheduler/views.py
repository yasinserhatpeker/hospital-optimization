from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import OperationPlanRequestSerializer
from .services import generate_schedule

