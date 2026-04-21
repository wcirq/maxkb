from django.urls import path

from . import views

app_name = "system_manage_chat"

urlpatterns = [
    path('display/info', views.DisplaySettingView.as_view()),
]
