from django.conf.urls import url
import os

from . import views

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))

from .views import (
    home_view,
    today_news_mode_form_view,
    search_mode_form_view,
    word_cloud_view,
    sentiment_analysis_view,
)

# application name
app_name = 'newsapp'

urlpatterns = [
    # view for homepage
    url(r'^$', home_view, name='index'),
    # view for displaying news articles in Today's News Mode
    url(r'^today_news/?$', today_news_mode_form_view, name='today_news'),
    # view for displaying news articles in Search Mode
    url(r'^search/?$', search_mode_form_view, name='search'),
    # view for displaying word cloud visualization for Today's News Mode
    url(r'^word_cloud/?$', word_cloud_view, name='word_cloud'),
    # view for displaying sentiment analysis visualization for Search Mode
    url(r'^sentiment_analysis/?$', sentiment_analysis_view, name='sentiment_analysis'),
]