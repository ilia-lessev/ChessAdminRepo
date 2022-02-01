from django.contrib import admin
from django.urls import path
from ChessAdminApp import views
from django.conf.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ChessAdminApp.urls')),
]
