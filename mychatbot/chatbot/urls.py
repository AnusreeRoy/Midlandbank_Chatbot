from django.urls import include, path
from . import views

# urlpatterns = [
#     #  path('chatbot/',include('chatbot.urls')),
#     path("",views.index, name="index" ),
#  ]

from django.urls import path
from .views import chatbot_response

urlpatterns = [
    path("", chatbot_response, name="chatbot_response"),
]