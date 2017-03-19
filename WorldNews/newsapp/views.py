from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.views import generic
from django.contrib import messages

from .models import newsapp, TodayNewsModeForm, SearchModeForm

import feedparser
import json
from translate import Translator
from urllib.parse import quote
import html
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import string
import re
import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud
from wordcloud import get_single_color_func
from PIL import Image, ImageChops
import seaborn as sns
from os.path import dirname, abspath

# map countries to respective edition codes
country_dict = {'au': 'Australia',
                'pt-BR_br': 'Brazil',
                'cn': 'China',
                'fr': 'France',
                'de': 'Germany',
                'in': 'India',
                'jp': 'Japan',
                'ru_ru': 'Russia',
                'es': 'Spain',
                'uk': 'U.K.',
                'us': 'U.S.A.'
                }

# map categories to respective category codes
category_dict = {'n': 'Home',
                 'w': 'World',
                 'b': 'Business',
                 'e': 'Entertainment',
                 's': 'Sports',
                 'm': 'Health'
                 }
# dictionary of tokens and frequencies pairs of country 1 for word cloud
word_cloud_dict_1 = {}
# dictionary of tokens and frequencies pairs of country 2 for word cloud
word_cloud_dict_2 = {}
# list of news articles of country 1 for sentiment analysis
sentiment_analysis_list_1 = []
# list of news articles of country 1 for sentiment analysis
sentiment_analysis_list_2 = []

# name of country 1
country_1_name = ''
# name of country 2
country_2_name = ''
# name of category
category_name = ''
# query term to be searched
query = ''

# current directory to save images
dir_name = dirname(abspath(__file__))

# strip html tags from text
def striphtml(data):
    # regular expression comprising of html tags
    p = re.compile(r'<.*?>')
    return p.sub('', data)

# return list of stop words and punctuations for eliminating them during visualization
def stopwords_list():
    stop_list = []
    # append stop words to list
    for item in stopwords.words('english'):
        stop_list.append(item)
    # append punctuations to list
    for item in string.punctuation:
        stop_list.append(item)
    # append '...' which occurs in description of news article to list
    stop_list.append('...')
    return stop_list

# return dictionary with tokens and their frequencies with text input for word cloud visualization
def word_cloud(text):
    word_cloud_dict = {}
    # list to contain lemmatized tokens
    word_cloud_list = []
    # call stopwords_list()
    stop_list = stopwords_list()
    # create WordNetLemmatizer object
    wordnet_lemmatizer = WordNetLemmatizer()
    # tokenize text
    for word in word_tokenize(text.lower()):
        # lemmatize tokens that are longer than 2 characters and are not stopwords
        if (word not in stop_list and len(word)>2):
            wordnet_lemmatizer.lemmatize(word)
            # append lemmatize token to list
            word_cloud_list.append(word)
    # calculate frequency of lemmatize token for word cloud
    for word in word_cloud_list:
        word_cloud_dict[word] = word_cloud_list.count(word)
    return word_cloud_dict

# render homepage
def home_view(request):

    # model form data for Today's News Mode
    form_1 = TodayNewsModeForm(request.POST or None)
    # model form data for Search Mode
    form_2 = SearchModeForm(request.POST or None)
    # pass data as context to index.html
    context = {
        "form": [form_1, form_2]
    }
    return render(request, 'index.html')

# render display of news results after Today's News Mode form is submitted
def today_news_mode_form_view(request):

    # model form data for Today's News Mode
    form_1 = TodayNewsModeForm(request.POST or None)

    # list of titles of news articles from country 1
    title_list_1 = []
    # list of URL links of news articles from country 1
    link_list_1 = []
    # list of published dates of news articles from country 1
    pub_date_list_1 = []
    # list of descriptions of news articles from country 1
    description_list_1 = []
    # text for word cloud visualization of country 1
    word_cloud_text_1 = ''

    # list of titles of news articles from country 2
    title_list_2 = []
    # list of URL links of news articles from country 2
    link_list_2 = []
    # list of published dates of news articles from country 2
    pub_date_list_2 = []
    # list of descriptions of news articles from country 2
    description_list_2 = []
    # text for word cloud visualization of country 2
    word_cloud_text_2 = ''

    # if Today's News Mode and its fields are chosen and submitted
    if 'today_news_mode_submit' in request.POST:

        # obtain country 1 name
        country_1 = form_1['country_1'].value()
        # obtain country 2 name
        country_2 = form_1['country_2'].value()
        # obtain category name
        category = form_1['category'].value()

        # URL for RSS feed with 'ned' parameter as country 1, 'topic' parameter as category (num=100 is default since max no. of articles from RSS feed is 30)
        news_feed_1 = 'https://news.google.com/news/section?pz=1&cf=all&ned=' + country_1 + '&topic=' + category + '&output=rss&num=100'
        # parse RSS feed content from URL to XML
        feed_1 = feedparser.parse(news_feed_1)
        # parse XML content to JSON
        feed_1 = json.dumps(feed_1)
        feed_1 = json.loads(feed_1)

        # iterate through JSON object of country 1
        for item_1 in feed_1['entries']:

            # find position of news source mentioned in title
            source_position_1 = item_1['title'].rfind(' - ')
            # title of news article of country 1
            title_1 = item_1['title'][:source_position_1]
            # URL link of news article of country 1
            link_1 = item_1['links'][0]['href']
            # published date of news article of country 1
            pub_date_1 = 'Published on ' + item_1['published']
            str_source_1 = '<b><font color="#6f6f6f">' + item_1['title'][source_position_1 + 3:] + '</font></b></font><br><font size="-1">'
            position_1 = item_1['summary'].find(str_source_1)
            # description of news article of country 1 ('...' added to indicate clicking the URL to read the entire description)
            description_1 = item_1['summary'][position_1 + len(str_source_1):].split('.')[0] + '...'
            # if country 1 is Brazil
            if (country_1 == 'pt-BR_br'):
                # translate text from Portuguese to English
                from_lang_1 = 'pt'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is China
            elif (country_1 == 'cn'):
                # translate text from Simplified Chinese to English
                from_lang_1 = 'zh-CN'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is France
            elif (country_1 == 'fr'):
                # translate text from French to English
                from_lang_1 = 'fr'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is Germany
            elif (country_1 == 'de'):
                # translate text from German to English
                from_lang_1 = 'de'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is Japan
            elif (country_1 == 'jp'):
                # translate text from Japanese to English
                from_lang_1 = 'jp'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is Russia
            elif (country_1 == 'ru_ru'):
                # translate text from Russian to English
                from_lang_1 = 'ru'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is Spain
            elif (country_1 == 'es'):
                # translate text from Spanish to English
                from_lang_1 = 'es'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)

            # strip HTML elements from text to make it human-readable
            title_1 = html.unescape(title_1)
            title_1 = striphtml(title_1)
            description_1 = html.unescape(description_1)
            description_1 = striphtml(description_1)
            # append title of news article of country 1 to list
            title_list_1.append(title_1)
            # append URL link of news article of country 1 to list
            link_list_1.append(link_1)
            # concatenate title and description of news article of country 1 for nlp
            text_1 = title_1 + ' ' + description_1
            # join title and description to string containing all titles and descriptions of news articles of country 1
            word_cloud_text_1 = word_cloud_text_1 + text_1
            # append published date of news article of country 1 to list
            pub_date_list_1.append(pub_date_1)
            # append description of news article of country 1 to list
            description_list_1.append(description_1)

        global word_cloud_dict_1
        # call word_cloud() for country 1
        word_cloud_dict_1 = word_cloud(word_cloud_text_1)

        # URL for RSS feed with 'ned' parameter as country 2, 'topic' parameter as category (num=100 is default since max no. of articles from RSS feed is 30)
        news_feed_2 = 'https://news.google.com/news/section?pz=1&cf=all&ned=' + country_2 + '&topic=' + category + '&output=rss&num=100'
        # parse RSS feed content from URL to XML
        feed_2 = feedparser.parse(news_feed_2)
        # parse XML content to JSON
        feed_2 = json.dumps(feed_2)
        feed_2 = json.loads(feed_2)

        # iterate through JSON object of country 2
        for item_2 in feed_2['entries']:

            # find position of news source mentioned in title
            source_position_2 = item_2['title'].rfind(' - ')
            # title of news article of country 2
            title_2 = item_2['title'][:source_position_2]
            # URL link of news article of country 2
            link_2 = item_2['links'][0]['href']
            # published date of news article of country 2
            pub_date_2 = 'Published on ' + item_2['published']
            str_source_2 = '<b><font color="#6f6f6f">' + item_2['title'][
                                                         source_position_2 + 3:] + '</font></b></font><br><font size="-1">'
            position_2 = item_2['summary'].find(str_source_2)
            # description of news article of country 2 ('...' added to indicate clicking the URL to read the entire description)
            description_2 = item_2['summary'][position_2 + len(str_source_2):].split('.')[0] + '...'
            # if country 2 is Brazil
            if (country_2 == 'pt-BR_br'):
                # translate text from Portuguese to English
                from_lang_2 = 'pt'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is China
            elif (country_2 == 'cn'):
                # translate text from Simplified Chinese to English
                from_lang_2 = 'zh-CN'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is France
            elif (country_2 == 'fr'):
                # translate text from French to English
                from_lang_2 = 'fr'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is Germany
            elif (country_2 == 'de'):
                # translate text from German to English
                from_lang_2 = 'de'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is Japan
            elif (country_2 == 'jp'):
                # translate text from Japanese to English
                from_lang_2 = 'jp'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is Russia
            elif (country_2 == 'ru_ru'):
                # translate text from Russian to English
                from_lang_2 = 'ru'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is Spain
            elif (country_2 == 'es'):
                # translate text from Spanish to English
                from_lang_2 = 'es'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)

            # strip HTML elements from text to make it human-readable
            title_2 = html.unescape(title_2)
            title_2 = striphtml(title_2)
            description_2 = html.unescape(description_2)
            description_2 = striphtml(description_2)
            # append title of news article of country 2 to list
            title_list_2.append(title_2)
            # append URL link of news article of country 2 to list
            link_list_2.append(link_2)
            # concatenate title and description of news article of country 2 for nlp
            text_2 = title_2 + ' ' + description_2
            # join title and description to string containing all titles and descriptions of news articles of country 2
            word_cloud_text_2 = word_cloud_text_2 + text_2
            # append published date of news article of country 2 to list
            pub_date_list_2.append(pub_date_2)
            # append description of news article of country 2 to list
            description_list_2.append(description_2)

        global word_cloud_dict_2
        # call word_cloud() for country 2
        word_cloud_dict_2 = word_cloud(word_cloud_text_2)

    zipped_list_1 = zip(title_list_1, link_list_1, pub_date_list_1, description_list_1)

    zipped_list_2 = zip(title_list_2, link_list_2, pub_date_list_2, description_list_2)

    global country_1_name, country_2_name, category_name

    country_1_name = country_dict[country_1]
    country_2_name = country_dict[country_2]
    category_name = category_dict[category]

    # pass data as context to today_news.html
    context_1 = {
        "zipped_list_1": zipped_list_1,
        "zipped_list_2": zipped_list_2,
        "country_1_name": country_1_name,
        "country_2_name": country_2_name,
        "category_name": category_name
    }
    return render(request, 'today_news.html', context_1)

# render display of news results after Search Mode form is submitted
def search_mode_form_view(request):

    # model form data for Search Mode
    form_2 = SearchModeForm(request.POST or None)

    # list of titles of news articles from country 1
    title_list_1 = []
    # list of URL links of news articles from country 1
    link_list_1 = []
    # list of published dates of news articles from country 1
    pub_date_list_1 = []
    # list of descriptions of news articles from country 1
    description_list_1 = []

    # list of titles of news articles from country 2
    title_list_2 = []
    # list of URL links of news articles from country 2
    link_list_2 = []
    # list of published dates of news articles from country 2
    pub_date_list_2 = []
    # list of descriptions of news articles from country 2
    description_list_2 = []

    # if Search Mode and its fields are chosen and submitted
    if 'search_mode_submit' in request.POST:

        global query
        # obtain query term
        query = form_2['query'].value()
        # encode query to be embedded in URL
        query_safe = quote(query, safe=[])
        # obtain country 1 name
        country_1 = form_2['country_1'].value()
        # obtain country 1 name
        country_2 = form_2['country_2'].value()

        # URL for RSS feed with 'ned' parameter as country 1, 'q' parameter as query_safe (num=100 is default since max no. of articles from RSS feed is 30)
        news_feed_1 = 'https://news.google.com/news?ned=' + country_1 + '&num=100&output=rss&q=%22' + query_safe + '%22'
        # parse RSS feed content from URL to XML
        feed_1 = feedparser.parse(news_feed_1)
        # parse XML content to JSON
        feed_1 = json.dumps(feed_1)
        feed_1 = json.loads(feed_1)

        # URL for RSS feed with 'ned' parameter as country 2, 'q' parameter as query_safe (num=100 is default since max no. of articles from RSS feed is 30)
        news_feed_2 = 'https://news.google.com/news?ned=' + country_2 + '&num=100&output=rss&q=%22' + query_safe + '%22'
        # parse RSS feed content from URL to XML
        feed_2 = feedparser.parse(news_feed_2)
        # parse XML content to JSON
        feed_2 = json.dumps(feed_2)
        feed_2 = json.loads(feed_2)

        for item_1 in feed_1['entries']:

            # find position of news source mentioned in title
            source_position_1 = item_1['title'].rfind(' - ')
            # title of news article of country 1
            title_1 = item_1['title'][:source_position_1]
            # URL link of news article of country 1
            link_1 = item_1['links'][0]['href']
            # published date of news article of country 1
            pub_date_1 = 'Published on ' + item_1['published']
            str_source_1 = '<b><font color="#6f6f6f">' + item_1['title'][
                                                         source_position_1 + 3:] + '</font></b></font><br><font size="-1">'
            position_1 = item_1['summary'].find(str_source_1)
            # description of news article of country 1 ('...' added to indicate clicking the URL to read the entire description)
            description_1 = item_1['summary'][position_1 + len(str_source_1):].split('.')[0] + '...'
            # if country 1 is Brazil
            if (country_1 == 'pt-BR_br'):
                # translate text from Portuguese to English
                from_lang_1 = 'pt'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is China
            elif (country_1 == 'cn'):
                # translate text from Simplified Chinese to English
                from_lang_1 = 'zh-CN'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is France
            elif (country_1 == 'fr'):
                # translate text from French to English
                from_lang_1 = 'fr'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is Germany
            elif (country_1 == 'de'):
                # translate text from German to English
                from_lang_1 = 'de'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is Japan
            elif (country_1 == 'jp'):
                # translate text from Japanese to English
                from_lang_1 = 'jp'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is Russia
            elif (country_1 == 'ru_ru'):
                # translate text from Russian to English
                from_lang_1 = 'ru'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)
            # if country 1 is Spain
            elif (country_1 == 'es'):
                # translate text from Spanish to English
                from_lang_1 = 'es'
                translator_1 = Translator(to_lang='en', from_lang=from_lang_1)
                title_1 = translator_1.translate(title_1)
                description_1 = translator_1.translate(description_1)

            # strip HTML elements from text to make it human-readable
            title_1 = html.unescape(title_1)
            title_1 = striphtml(title_1)
            description_1 = html.unescape(description_1)
            description_1 = striphtml(description_1)
            # append title of news article of country 1 to list
            title_list_1.append(title_1)
            # append URL link of news article of country 1 to list
            link_list_1.append(link_1)
            # concatenate title and description of news article of country 1 for nlp
            text_1 = title_1 + ' ' + description_1

            global sentiment_analysis_list_1
            # append title and description to list for sentiment analysis visualization for country 1
            sentiment_analysis_list_1.append(text_1)

            # append published date of news article of country 1 to list
            pub_date_list_1.append(pub_date_1)
            # append description of news article of country 1 to list
            description_list_1.append(description_1)

        for item_2 in feed_2['entries']:

            # find position of news source mentioned in title
            source_position_2 = item_2['title'].rfind(' - ')
            # title of news article of country 2
            title_2 = item_2['title'][:source_position_2]
            # URL link of news article of country 2
            link_2 = item_2['links'][0]['href']
            # published date of news article of country 2
            pub_date_2 = 'Published on ' + item_2['published']
            str_source_2 = '<b><font color="#6f6f6f">' + item_2['title'][
                                                         source_position_2 + 3:] + '</font></b></font><br><font size="-1">'
            position_2 = item_2['summary'].find(str_source_2)
            # description of news article of country 2 ('...' added to indicate clicking the URL to read the entire description)
            description_2 = item_2['summary'][position_2 + len(str_source_2):].split('.')[0] + '...'
            # if country 2 is Brazil
            if (country_2 == 'pt-BR_br'):
                # translate text from Portuguese to English
                from_lang_2 = 'pt'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is China
            elif (country_2 == 'cn'):
                # translate text from Simplified Chinese to English
                from_lang_2 = 'zh-CN'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is France
            elif (country_2 == 'fr'):
                # translate text from French to English
                from_lang_2 = 'fr'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is Germany
            elif (country_2 == 'de'):
                # translate text from German to English
                from_lang_2 = 'de'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is Japan
            elif (country_2 == 'jp'):
                # translate text from Japanese to English
                from_lang_2 = 'jp'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is Russia
            elif (country_2 == 'ru_ru'):
                # translate text from Russian to English
                from_lang_2 = 'ru'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)
            # if country 2 is Spain
            elif (country_2 == 'es'):
                # translate text from Spanish to English
                from_lang_2 = 'es'
                translator_2 = Translator(to_lang='en', from_lang=from_lang_2)
                title_2 = translator_2.translate(title_2)
                description_2 = translator_2.translate(description_2)

            # strip HTML elements from text to make it human-readable
            title_2 = html.unescape(title_2)
            title_2 = striphtml(title_2)
            description_2 = html.unescape(description_2)
            description_2 = striphtml(description_2)
            # append title of news article of country 2 to list
            title_list_2.append(title_2)
            # append URL link of news article of country 2 to list
            link_list_2.append(link_2)
            # concatenate title and description of news article of country 2 for nlp
            text_2 = title_2 + ' ' + description_2

            global sentiment_analysis_list_2
            # append title and description to list for sentiment analysis visualization for country 2
            sentiment_analysis_list_2.append(text_2)

            # append published date of news article of country 2 to list
            pub_date_list_2.append(pub_date_2)
            # append description of news article of country 2 to list
            description_list_2.append(description_2)

    zipped_list_1 = zip(title_list_1, link_list_1, pub_date_list_1, description_list_1)

    zipped_list_2 = zip(title_list_2, link_list_2, pub_date_list_2, description_list_2)

    global country_1_name, country_2_name

    country_1_name = country_dict[country_1]
    country_2_name = country_dict[country_2]

    # pass data as context to search.html
    context_2 = {
        "query": query,
        "zipped_list_1": zipped_list_1,
        "zipped_list_2": zipped_list_2,
        "country_1_name": country_1_name,
        "country_2_name": country_2_name
    }
    return render(request, 'search.html', context_2)

# return trimmed image by removing whitespace surrounding it
def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

# render word cloud visualization for Today's News Mode
def word_cloud_view(request):

    # if Generate Word Cloud is submitted
    if 'word_cloud_submit' in request.POST:

        word_cloud_dict_updated_1 = {}
        word_cloud_dict_updated_2 = {}
        word_cloud_dict_3 = {}

        # dictionary containing common tokens and frequencies to both country 1 and country 2
        for key_1 in word_cloud_dict_1:
            for key_2 in word_cloud_dict_2:
                if key_1 == key_2:
                    word_cloud_dict_3[key_1] = word_cloud_dict_1[key_1] + word_cloud_dict_2[key_2]

        # dictionary containing tokens and frequencies exclusive to country 1
        for key_1 in word_cloud_dict_1:
            if key_1 not in word_cloud_dict_3:
                word_cloud_dict_updated_1[key_1] = word_cloud_dict_1[key_1]

        # dictionary containing tokens and frequencies exclusive to country 2
        for key_2 in word_cloud_dict_2:
            if key_2 not in word_cloud_dict_3:
                word_cloud_dict_updated_2[key_2] = word_cloud_dict_2[key_2]

        plt.clf()

        # word cloud for country 1 terms colored in dark blue
        color_func1 = get_single_color_func('darkblue')
        # word cloud for country 1 terms colored in dark red
        color_func2 = get_single_color_func('darkred')
        # word cloud for common terms colored in dark green
        color_func3 = get_single_color_func('darkgreen')

        # generate word cloud for country 1 terms
        wordcloud_1 = WordCloud(background_color ='#DCDCDC', color_func = color_func1).generate_from_frequencies(word_cloud_dict_updated_1)
        # generate word cloud for country 2 terms
        wordcloud_2 = WordCloud(background_color ='#DCDCDC', color_func = color_func2).generate_from_frequencies(word_cloud_dict_updated_2)
        # generate word cloud for common terms
        wordcloud_3 = WordCloud(background_color ='#DCDCDC', color_func = color_func3).generate_from_frequencies(word_cloud_dict_3)

        plt.axis('off')

        # image link for word cloud for country 1 terms in static folder
        img_link_1 = dir_name + '/static/images/wordcloud_1.png'
        # image link for word cloud for country 2 terms in static folder
        img_link_2 = dir_name + '/static/images/wordcloud_2.png'
        # image link word cloud for country 3 terms in static folder
        img_link_3 = dir_name + '/static/images/wordcloud_3.png'

        # save word cloud for country 1 terms
        plt.imshow(wordcloud_1)
        plt.savefig(img_link_1)
        img_1 = Image.open(img_link_1)
        # call trim()
        img_1 = trim(img_1)
        img_1.save(img_link_1)

        # save word cloud for country 2 terms
        plt.imshow(wordcloud_2)
        plt.savefig(img_link_2)
        img_2 = Image.open(img_link_2)
        # call trim()
        img_2 = trim(img_2)
        img_2.save(img_link_2)

        # save word cloud for common terms
        plt.imshow(wordcloud_3)
        plt.savefig(img_link_3)
        img_3 = Image.open(img_link_3)
        # call trim()
        img_3 = trim(img_3)
        img_3.save(img_link_3)

        # pass data as context to word_cloud.html
        context_3 = {
            "country_1_name": country_1_name,
            "country_2_name": country_2_name,
            "category_name": category_name
        }

    return render(request, 'word_cloud.html', context_3)

# render sentiment analysis visualization for Search Mode
def sentiment_analysis_view(request):

    # if Generate Sentiment Analysis is submitted
    if 'sentiment_analysis_submit' in request.POST:

        # list for compound polarity scores of news articles of country 1
        sentiment_score_list_1 = []
        # list for compound polarity scores of news articles of country 1
        sentiment_score_list_2 = []
        # dictionary of frequency of articles based on compound polarity scores of news articles of country 1
        sentiment_score_dict_1 = {'Positive Articles': 0, 'Negative Articles': 0, 'Neutral Articles': 0}
        # dictionary of frequency of articles based on compound polarity scores of news articles of country 2
        sentiment_score_dict_2 = {'Positive Articles': 0, 'Negative Articles': 0, 'Neutral Articles': 0}
        # strip '...' present in description
        stripped_list_1 = [sentence.strip('...') for sentence in sentiment_analysis_list_1]
        stripped_list_2 = [sentence.strip('...') for sentence in sentiment_analysis_list_2]
        # create SentimentIntensityAnalyzer object
        sentiment = SentimentIntensityAnalyzer()
        for sentence in stripped_list_1:
            # append compound polarity score of news articles of country 1
            sentiment_score_list_1.append(sentiment.polarity_scores(text=sentence)['compound'])
        for sentence in stripped_list_2:
            # append compound polarity score of news articles of country 2
            sentiment_score_list_2.append(sentiment.polarity_scores(text=sentence)['compound'])

        # create bins for histogram
        bins = np.arange(-1.0, 1.0, 0.1)

        # combine country 1 and country 2 scores
        data = np.vstack([sentiment_score_list_1, sentiment_score_list_2]).T
        # image link for sentiment analysis histogram in static folder
        sentiment_analysis_link = dir_name + '/static/images/sentiment_analysis.png'
        # image link for sentiment analysis pie chart of country 1 in static folder
        pie_chart_1_link = dir_name + '/static/images/pie_chart_1.png'
        # image link for sentiment analysis pie chart of country 2 in static folder
        pie_chart_2_link = dir_name + '/static/images/pie_chart_2.png'

        plt.clf()
        # create histogram of polarity scores with heights defined by frequency of articles
        # histogram bar of country 1 and country 2 is dark blue and dark red respectively
        plt.hist(data, bins=bins, alpha=0.7, color=['darkblue', 'darkred'], label=[country_1_name, country_2_name])
        # set x-axis label
        plt.xlabel('Normalized Polarity Scores')
        # set y-axis label
        plt.ylabel('Number of Articles')
        # create legend
        plt.legend()

        # save sentiment analysis histogram
        plt.savefig(sentiment_analysis_link)
        img = Image.open(sentiment_analysis_link)
        # call trim()
        img = trim(img)
        img.save(sentiment_analysis_link)
        plt.clf()
        # iterate through news articles of country 1
        for score_1 in sentiment_score_list_1:
            # increment number of positive articles if compound polarity score is positive
            if score_1 > 0.0:
                sentiment_score_dict_1['Positive Articles'] += 1
            # increment number of negative articles if compound polarity score is negative
            elif score_1 < 0.0:
                sentiment_score_dict_1['Negative Articles'] += 1
            # increment number of neutral articles if compound polarity score is zero
            elif score_1 == 0.0:
                sentiment_score_dict_1['Neutral Articles'] += 1
        # set pie chart shape to circle
        plt.axis("equal")
        # create pie chart for distribution of news articles of country 1 based on compound polarity scores
        plt.pie([v for v in sentiment_score_dict_1.values()],labels=[k for k in sentiment_score_dict_1.keys()],autopct='%.2f%%')
        plt.suptitle('Distribution of Polarity Scores for News about "' + query + '" in ' + country_1_name, fontsize=14, fontweight='bold')
        # save sentiment analysis pie chart of country 1
        plt.savefig(pie_chart_1_link)
        img = Image.open(pie_chart_1_link)
        # call trim()
        img = trim(img)
        img.save(pie_chart_1_link)
        plt.clf()

        # iterate through news articles of country 2
        for score_2 in sentiment_score_list_2:
            # increment number of positive articles if compound polarity score is positive
            if score_2 > 0.0:
                sentiment_score_dict_2['Positive Articles'] += 1
            # increment number of negative articles if compound polarity score is negative
            elif score_2 < 0.0:
                sentiment_score_dict_2['Negative Articles'] += 1
            # increment number of neutral articles if compound polarity score is zero
            elif score_2 == 0.0:
                sentiment_score_dict_2['Neutral Articles'] += 1
        # set pie chart shape to circle
        plt.axis("equal")
        # create pie chart for distribution of news articles of country 2 based on compound polarity scores
        plt.pie([v for v in sentiment_score_dict_2.values()], labels=[k for k in sentiment_score_dict_2.keys()], autopct='%.2f%%')
        plt.suptitle('Distribution of Polarity Scores for News about "' + query + '" in ' + country_2_name, fontsize=14, fontweight='bold')
        # save sentiment analysis pie chart of country 1
        plt.savefig(pie_chart_2_link)
        img = Image.open(pie_chart_2_link)
        # call trim()
        img = trim(img)
        img.save(pie_chart_2_link)
        # pass data as context to sentiment_analysis.html
        context_4 = {
            "query": query
        }
    return render(request, 'sentiment_analysis.html', context_4)