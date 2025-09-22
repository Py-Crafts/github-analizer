from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    # Analysis Tasks
    path('tasks/', views.AnalysisTaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<uuid:pk>/', views.AnalysisTaskDetailView.as_view(), name='task-detail'),
    path('tasks/<uuid:task_id>/progress/', views.task_progress, name='task-progress'),
    path('tasks/<uuid:task_id>/cancel/', views.cancel_task, name='task-cancel'),
    
    # Analysis Results
    path('results/<uuid:task_id>/', views.AnalysisResultDetailView.as_view(), name='result-detail'),
    
    # Analysis Exports
    path('exports/', views.AnalysisExportListCreateView.as_view(), name='export-list-create'),
    path('exports/<uuid:export_id>/download/', views.download_export, name='export-download'),
    
    # Analysis Templates
    path('templates/', views.AnalysisTemplateListCreateView.as_view(), name='template-list-create'),
    path('templates/<int:pk>/', views.AnalysisTemplateDetailView.as_view(), name='template-detail'),
    
    # Statistics
    path('stats/', views.analysis_stats, name='stats'),
]