# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import csv
import telebot
import io
from telebot import types
from constant import TOKEN
bot = telebot.TeleBot(TOKEN)
markup_new = types.ReplyKeyboardMarkup(True, True)
markup_new.row('Начать парсинг новой страницы')
markup_number = types.ReplyKeyboardMarkup(True, True)
markup_number.row('Ввести самостоятельно', 'Все страницы')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
           'Accept': '*/*'}
HOST = 'https://auto.ria.com'
FILE = 'cars_tab.csv'
URL = ''
NUMBER= None
#sys.setdefaultencoding("utf-8")
def get_html(URL, params=None):
    r = requests.get(URL, headers=HEADERS, params=params)
    print(r.encoding)
    return r
def get_pages_count(html):
    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find_all('span', class_='mhide')
    if pagination:
        return int(pagination[-1].get_text())
    else:
        return 1
def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='content-bar')
    #название цена$ цена город
    cars = []
    for item in items:
        uah_price = item.find('span', class_='i-block')
        if uah_price:
            uah_price = uah_price.get_text().replace("\xa0", ' ')
        else:
            uah_price = 'цену уточняйте'
        cars.append({
            'title': item.find('div', class_='item ticket-title').get_text(strip=True),
            'link': item.find('a', class_='m-link-ticket').get('href'),
            'usd_price': item.find('span', class_='green').get_text(),
            'uah_price': uah_price,
            'city': item.find('li', class_='item-char view-location').get_text(strip=True)
        })
    return cars

def save_file(items):
    with open('cars_tab.csv', 'w', newline='') as file:
        writer = csv.writer(file, dialect='excel', delimiter=';')
        writer.writerow(['Mark', 'URL', 'Price in $', 'Price in UAH', 'City'])
        for item in items:
            writer.writerow([item['title'], item['link'], item['usd_price'], item['uah_price'], item['city']])
    return file

def parse(message, URL, NUMBER):
    html = get_html(URL)
    if html.status_code == 200:
        cars = []
        pages_all = get_pages_count(html.text)
        for page in range(1, NUMBER+1):
            bot.send_message(message.chat.id, f'Парсинг страницы {page} из {NUMBER}...')
            html = get_html(URL, params={'page': page})
            cars.extend(get_content(html.text))
        save_file(cars)
        bot.send_message(message.chat.id, f'Получено {len(cars)} автомобилей')
        file = open('cars_tab.csv', 'rb')
        bot.send_document(message.chat.id, file)
        file.close()
        bot.send_message(message.chat.id, 'Документ отправлен!')
    else:
        return bot.send_message(message.chat.id, 'Простите, произошла ошибка:(')
def get_NUMBER(message):
    bot.send_message(message.chat.id, 'Сколько страниц вы хотите спарсить?', reply_markup=markup_number)
@bot.message_handler(commands = ['start'])
def welcome(message):
    bot.send_message(message.chat.id, 'Привет! Я бот парсер сайта auto.ria. Введя URL и количество страниц,'
                                      'вы получите от меня таблицу с информацией из объявлений.')
    bot.send_message(message.chat.id, 'Для начала введите URL:')

@bot.message_handler(commands = ['help'])
def help(message):
    bot.send_message(message.chat.id, 'Введите ссылку на страницу с объявлениями с сайта auto.ria,'
                                      'и я отправлю вам информацию по каждому из предложений.')

@bot.message_handler(content_types = ['text'])
def answer(message):
    global NUMBER
    global all
    global URL
    if 'https://auto.ria.com' in message.text:
        global html
        html = get_html(message.text)
        if html.status_code == 200:
            URL = message.text
            all = int(get_pages_count((get_html(URL)).text))
            get_NUMBER(message)
        else:
            bot.send_message(message.chat.id, 'Простите, но ссылка некорректна. Проверьте соблюдены ли следующие условия:')
            bot.send_message(message.chat.id, '1. Адрес должен ссылаться на старницу с объявлениями, выданными по выбранным вами критериями, на сайте AUTO.RIA.\n'
                                              '2. Ссылка - она должна начинаться с "https://auto.ria.com/" ')

    elif message.text == 'Ввести самостоятельно':
        bot.send_message(message.chat.id, f'Введите число не превышающее {all} - '
                                              'общее количество страниц')

    elif message.text == 'Начать парсинг новой страницы':
        NUMBER = None
        URL = ''
        help(message)

    elif message.text.isdigit() == True:
        if URL != '':
            if int(message.text) > all:
                bot.send_message(message.chat.id, 'Простите, но вы ввели число превышающее общее число страниц.')
                return bot.send_message(message.chat.id, 'Попробуйте ввести число страниц ещё раз:')
        if URL != '':
            NUMBER = int(message.text)
            parse(message, URL, NUMBER)
            URL = ''
            NUMBER = None
            bot.send_message(message.chat.id, 'Начать парсинг новой страницы', reply_markup=markup_new)
        else:
            bot.send_message(message.chat.id, 'Вы забыли ввести ссылку, начните с неё.')
            bot.send_message(message.chat.id, 'Введите ссылку на страницу с объявлениями:')

    elif message.text == 'Все страницы':
        parse(message, URL, all)
        URL = ''
        bot.send_message(message.chat.id, 'Начать парсинг новой страницы?', reply_markup=markup_new)

    else:
        bot.send_message(message.chat.id, 'Простите, возникла ошибка:(')
        bot.send_message(message.chat.id, 'Попробуйте начать парсинг заново', reply_markup=markup_new)


@bot.message_handler(commands = ['start_again'])
def again(message):
    bot.send_message(message.chat.id, 'Вы начали сессию заново.')
    URL = ''
    NUMBER = None
    bot.send_message(message.chat.id, 'Введите ссылку на страницу с объявлениями с сайта auto.ria,')


bot.polling(none_stop = True)