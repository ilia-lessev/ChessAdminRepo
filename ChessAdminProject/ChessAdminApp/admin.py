from django.contrib import admin
from .models import Player
from .models import Match
from django.forms import ModelForm
from django.db.models import F, Q, ExpressionWrapper, IntegerField
from django.db.models import Value, Count, OuterRef, Subquery, Sum
from django.db.models.expressions import RawSQL

admin.site.site_header = 'Netstock Chess Club - Admin Site'

admin.site.register(Player)
admin.site.register(Match) 





