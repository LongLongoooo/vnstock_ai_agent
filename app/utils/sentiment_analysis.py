import json
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from textblob import TextBlob


def analyze_sentiment(articles):
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    words = ''

    for article in articles:
        analysis = TextBlob(article)
        words += ' '.join(article.split()) + ' '
        if analysis.sentiment.polarity > 0:
            sentiments['positive'] += 1
        elif analysis.sentiment.polarity == 0:
            sentiments['neutral'] += 1
        else:
            sentiments['negative'] += 1

    return sentiments, words


def generate_word_cloud(words):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(words)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig('static/wordcloud.png')
    plt.close()


def generate_pie_chart(sentiments):
    labels = sentiments.keys()
    sizes = sentiments.values()
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.savefig('static/sentiment_pie_chart.png')
    plt.close()
