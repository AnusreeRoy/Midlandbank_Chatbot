from django.urls import include, path
from . import views
from .views import chatbot_response
from .views import index

urlpatterns = [
    path("", index, name="index"),  # serves HTML page
    path("chatbot/", chatbot_response, name="chatbot_response"),  # POST endpoint
 ]


# urlpatterns = [
#     path("", chatbot_response, name="chatbot_response"),
# ]