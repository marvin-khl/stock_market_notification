import time
import requests
import datetime as dt
import os
from twilio.rest import Client

# NEWS DATA
COUNTRY = 'de'  # de stands for Germany
NAME = 'Tesla'
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
NEWS_ENDPOINT = 'https://newsapi.org/v2/top-headlines?'

# STOCK DATA
STOCK_API_KEY = os.environ.get('STOCK_API_KEY')
STOCK_ENDPOINT = 'https://www.alphavantage.co/query?'
FUNCTION = 'TIME_SERIES_DAILY'
SYMBOL = 'TSLA'  # company stock name

# TWILIO
ACCOUNT_SID = os.environ.get('ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('AUTH_TOKEN')


def check_weekday():
    weekday = dt.datetime.now().weekday()
    if 0 < weekday < 6:  # we get the yesterdays stock market data (monday to friday)
        return True


def get_stock_data():
    yesterday = dt.date.today() - dt.timedelta(days=3)

    stock_response = requests.get(url=STOCK_ENDPOINT, params={
        'function': FUNCTION,
        'symbol': SYMBOL,
        'apikey': STOCK_API_KEY
    })
    stock_response.raise_for_status()
    stock_data = stock_response.json()
    print(stock_data)
    open_value = stock_data['Time Series (Daily)'][str(yesterday)]['1. open']
    close_value = stock_data['Time Series (Daily)'][str(yesterday)]['4. close']

    value = (open_value, close_value)
    return value


def get_news():
    news_response = requests.get(url=NEWS_ENDPOINT, params={
        'country': COUNTRY,
        'q': NAME,
        'apiKey': NEWS_API_KEY
    })
    news_response.raise_for_status()
    news_data = news_response.json()['articles']

    if len(news_data) > 3:
        news_articles = news_data[:3]
    else:
        news_articles = news_data[:len(news_data)]

    formatted_articles = [
        f'Headline: {articles["title"]}\nDescription: {articles["description"]}\nRead more on: {articles["url"]}' for
        articles in news_articles]

    return formatted_articles


def send_sms(_percentage, is_up, _news):
    if is_up:
        sign = '⬆️'
    else:
        sign = '⬇️'

    account_sid = ACCOUNT_SID
    auth_token = AUTH_TOKEN
    client = Client(account_sid, auth_token)

    if _news:
        for article in _news:
            message = client.messages \
                .create(
                body=f'{NAME} {sign} {_percentage}\n{article}',
                from_='+000000000',
                to='+0000000000'  # phone number
            )
    else:
        message = client.messages \
            .create(
            body=f'{NAME} {sign} {_percentage}\nWithout news!',
            from_='+000000000',
            to='+00000000000'  # phone number
        )

    print(message.status)


time_hour = dt.datetime.now().hour

while True:
    # if time_hour == 6 and check_weekday():  # Opens at 7 a.m. in Frankfurt. So we get the news 1 hour earlier

    stock_values = get_stock_data()
    percentage = (float(stock_values[1]) / float(stock_values[0]) - 1.0) * 100.0

    if percentage > 5 or percentage < -5:
        news = get_news()
        if percentage > 5:
            send_sms(percentage, True, news)
        else:
            send_sms(percentage, False, news)

    time.sleep(3600)  # sleep for 1 hour
