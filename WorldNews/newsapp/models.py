from __future__ import unicode_literals

from django.db import models
from django import forms


# Create your models here.
class newsapp(models.Model):
    query = models.CharField(max_length=50)
    country_1 = models.CharField(max_length=50)
    country_2 = models.CharField(max_length=50)
    category = models.CharField(max_length=50)

    def __str__(self):
        return self.category

# form structure for Today's News Mode
class TodayNewsModeForm(forms.ModelForm):
    class Meta:
        model = newsapp
        fields = ["country_1", "country_2", "category"]

# form structure for Search Mode
class SearchModeForm(forms.ModelForm):
    class Meta:
        model = newsapp
        fields = ["query", "country_1", "country_2"]