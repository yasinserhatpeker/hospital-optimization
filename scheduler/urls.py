from django.urls import path
from .views import GenerateOperationPlanView,VisualizeOperationPlanView

urlpatterns = [
    path('generate-operation-plan/', GenerateOperationPlanView.as_view(), name="generate_plan"),
    path('visualize-operation-plan/', VisualizeOperationPlanView.as_view(), name="visualize_plan")

]