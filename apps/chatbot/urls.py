from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot, name='chatbot'),
    path('response/', views.chatbot_response, name='chatbot_response'),
    path('diagnostics/', views.chatbot_diagnostics, name='chatbot_diagnostics'),
]