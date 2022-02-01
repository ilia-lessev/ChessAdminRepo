from django.shortcuts import render
from django.http import HttpResponse

import urllib.request
import json
import urllib.parse

def index(request):    
    return render(request,'index.html',{})
