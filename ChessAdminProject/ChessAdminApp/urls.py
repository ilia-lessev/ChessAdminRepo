from django.urls import path
from . import views
from .views.index import index

urlpatterns = [
    path('', index),

]
