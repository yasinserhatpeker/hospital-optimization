from django.urls import path
from .views import GenerateOperationPlanView,VisualizeOperationPlanView,VisualizeOperationHeatMapView

urlpatterns = [
    path('generate-operation-plan/', GenerateOperationPlanView.as_view(), name="generate_plan"),
    path('visualize-operation-plan/', VisualizeOperationPlanView.as_view(), name="visualize_plan"),
    path('visualize-heatmap/', VisualizeOperationHeatMapView.as_view(), name="visualize_heatmap" )

]