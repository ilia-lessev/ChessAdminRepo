from django.urls import path
from . import views
from .views.rankingView import getRankingHistory
from .views.index import index


urlpatterns = [
    path('', index),
    path('getRankingHistory/', views.rankingView.getRankingHistory, name='getRankingHistory'),  
]
