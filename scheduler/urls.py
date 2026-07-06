from django.urls import path
from .views import GenerateOperationPlanView

urlpatterns = [
    path('api/generate-operation-plan', GenerateOperationPlanView.as_view(), name="generate_plan")

]