from django.urls import path
from .views import *

urlpatterns = [
    path('init/', init),
    path('chat/', response_streaming_view),
]
