from django.db import models
from django.db.models import F, Q
from django.forms import ModelForm
from datetime import datetime
import math
from django.conf import settings
from computed_property import ComputedIntegerField
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver


  