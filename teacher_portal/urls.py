from django.urls import path
from . import views

app_name = "teacher_portal"

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('export-results/', views.export_class_results, name='export_class_results'),
    path('notify-students/', views.notify_students, name='notify_students'),  # ✅ NEW
]