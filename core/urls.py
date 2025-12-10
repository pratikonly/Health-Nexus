from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('home/', views.home, name='home'),
    path('dashboard-home/', views.dashboard_home, name='dashboard_home'),
    path('quiz/', views.quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/submit/', views.quiz_submit, name='quiz_submit'),
    path('progress/', views.progress, name='progress'),
    path('ai-cam/', views.ai_cam, name='ai_cam'),
    path('analyze-food/', views.analyze_food, name='analyze_food'),
    path('diet-plan/', views.diet_plan, name='diet_plan'),
    path('log-meal/', views.log_meal, name='log_meal'),
    path('delete-meal/<int:meal_id>/', views.delete_meal, name='delete_meal'),
    path('settings/', views.settings_view, name='settings'),
    path('log-weight/', views.log_weight, name='log_weight'),
    path('api/nutrition-data/', views.get_nutrition_data, name='nutrition_data'),
    path('api/progress-data/', views.get_progress_data, name='progress_data'),
]
