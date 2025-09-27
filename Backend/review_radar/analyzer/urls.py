from django.urls import path
from . import views

app_name = 'analyzer'

urlpatterns = [
    path('', views.home, name='home'),
    path('analyze/', views.AnalyzeView.as_view(), name='analyze'),
    path('status/<int:analysis_id>/', views.analysis_status, name='analysis_status'),
    path('dashboard/<int:analysis_id>/', views.dashboard, name='dashboard'),
    path('analyses/', views.analysis_list, name='analysis_list'),
]