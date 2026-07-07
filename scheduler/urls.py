from django.urls import path
from .views import GenerateOperationPlanView, VisualizePlanView, VisualizeHeatmapView

urlpatterns = [
    path('generate-operation-plan/', GenerateOperationPlanView.as_view(), name="generate_plan"),
    path('visualize-operation-plan/', VisualizePlanView.as_view(), name="visualize_plan"),
    path('visualize-heatmap/', VisualizeHeatmapView.as_view(), name="visualize_heatmap"),
]