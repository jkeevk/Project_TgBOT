"""
Модуль для создания Telegram бота с использованием библиотеки Telebot.

Этот модуль реализует Telegram бота, который предоставляет пользователям возможность
взаимодействовать с системой обучения, добавлять и удалять слова, а также подписываться
на напоминания.

Импортированные модули и классы:
- random: для генерации случайных чисел.
- types и TeleBot из telebot: для работы с типами сообщений и создания бота.
- StateMemoryStorage и StatesGroup из telebot.storage: для управления состояниями пользователя.
- start_reminders и Notification из notification_scheduler: для обработки напоминаний.
- bot_db из data_base_tools: для работы с базой данных бота.
"""
import telebot
import configparser
import random

from telebot import types, TeleBot
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from notification_scheduler import start_reminders, Notification  
from data_base_tools import bot_db

class Command:
    """Класс, содержащий кнопки в качестве констант для быстроты использования и удобства."""
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово❌'
    NEXT = 'Пропустить ⏭'
    RULES = '📜Правила'
    START = '🚀Начать'
    START_AGAIN = '🔄Начать заново'

class MyStates(StatesGroup):
    """Класс для определения состояний бота."""
    english_word = State()
    russian_word = State()
    
def get_token():
    """Получает токен Telegram из файла конфигурации.
    
    Возвращает:
        str: токен доступа для бота.
    """
    config = configparser.ConfigParser()
    config.read("settings.ini")
    token_tg = config["TELEGRAM"]["token_tg"]
    return token_tg

state_storage = StateMemoryStorage()
token_tg = get_token()
bot=telebot.TeleBot(token_tg)


start_reminders(bot)
notification = Notification(bot)
@bot.message_handler(commands=['subscribe'])
def handle_subscribe(message):
    """Обрабатывает команду подписки на напоминания.
    
    Параметры:
        message (Message): Объект сообщения от пользователя.
    """
    notification.start(message)

@bot.message_handler(commands=['unsubscribe'])
def handle_unsubscribe(message):
    """Обрабатывает команду отписки от напоминаний.
    
    Параметры:
        message (Message): Объект сообщения от пользователя.
    """
    notification.stop(message)

commands = [
    telebot.types.BotCommand("start", "Запустить бота"),
    telebot.types.BotCommand("help", "Помощь"),
    telebot.types.BotCommand("menu", "Показать меню"),
    telebot.types.BotCommand("subscribe", "Подписаться на напоминания"),
    telebot.types.BotCommand("unsubscribe", "Отписаться от напоминаний")
]

bot.set_my_commands(commands)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(
    message.chat.id, 
    '👋 Здравствуйте!\n\n'
    'Нажмите "🚀Начать", чтобы открыть меню выбора переводов.\n'
    'Выберите правильный перевод предложенного слова. '
    '💡 Вам будет предоставлен пример использования или описание слова.\n\n'
    'Дополнительные функции:\n'
    'Нажмите "Добавить слово ➕" чтобы изучать дополнительное слово\n'
    'Нажмите "Удалить слово❌" чтобы оно больше не появлялось\n'
    'Нажмите "Пропустить ⏭" чтобы вернуться к слову позднее\n'
    '🔔 Подпишись, чтобы получать напоминания каждый день!\n\n'
    )


@bot.message_handler(commands=['menu'])
def show_menu(message):
    bot.send_message(message.chat.id, 
                     'Вы можете использовать следующие команды:\n'
                      '/start - Запустить бота\n'
                      '/help - Помощь\n'
                      '/menu - Показать меню\n'
                      '/subscribe - Подписаться на напоминания\n'
                      '/unsubscribe - Отписаться от напоминаний\n'
    )


@bot.message_handler(commands=['start'])
def start_message(message):
    """Функция приветствия нового пользователя.

    Отправляет стикер приветствия и сообщение с информацией о боте. 
    Также создает клавиатуру с вариантами действий для пользователя.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий информацию о пользователе и чате.
    """
    sti = open('static/welcome.webm', 'rb')
    bot.send_sticker(message.chat.id, sti)

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton("📜Правила")
    item2 = types.KeyboardButton("🚀Начать")
    item3 = types.KeyboardButton("🔄Начать заново")
 
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\n✨ Я - <b>{1.first_name}</b>, ваш личный помощник для улучшения английского языка!\n\n📚 Я здесь, чтобы сделать ваш процесс обучения интересным и эффективным. Давайте вместе достигать больших результатов!".format(message.from_user, bot.get_me()),
        parse_mode='html', reply_markup=markup)
    
@bot.message_handler(commands=['drop'])
def drop_progress(message):
    """Функция сброса прогресса пользователя.

    Проверяет текст ввода от пользователя для сброса прогресса. Если пользователь 
    нажимает 'да', сбрасывает прогресс и регистрирует пользователя в базе данных.
    В противном случае возвращает пользователя в главное меню.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий информацию о пользователе и чате.
    """
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)        
    markup.add(types.KeyboardButton("В начало↩️"))
    if message.text:
        if message.text.lower() == 'да':
            bot_db.drop_progress(user_id)
            bot_db.register_user(user_id)
            bot.send_message(message.chat.id, 'Прогресс сброшен', reply_markup=markup)
        elif message.text.lower() == 'нет':
            bot.send_message(message.chat.id, 'Вернуться в главное меню↩️', reply_markup=markup)
        bot.register_next_step_handler(message, start_message)
    else:
        bot.send_message(message.chat.id, "Я не понимаю это сообщение!")
        start_message(message)

def get_user_id(message):
    """Функция получения ID пользователя и добавления в базу данных, если отсутствует.

    Регистрирует пользователя в базе данных и возвращает его ID.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий информацию о пользователе.

    Возвращает:
        int: ID пользователя.
    """
    user_id = message.from_user.id
    bot_db.register_user(user_id)
    bot.register_next_step_handler(message, start_word_learning_session)
    return user_id


def generate_buttons(english_word):
    """Функция генерации кнопок с вариантами слов.

    Создает кнопки с правильным словом и случайными словами из базы данных, 
    чтобы пользователь мог выбирать из них.

    Параметры:
        english_word (str): Английское слово, для которого генерируются кнопки.

    Возвращает:
        ReplyKeyboardMarkup: Размеченная клавиатура с кнопками.
    """
    other_words_btns = set([english_word])    
    while len(other_words_btns) < 4:
        translation = bot_db.get_random_examples()[1]
        other_words_btns.add(translation)
    buttons = list(other_words_btns)
    random.shuffle(buttons) 
    buttons.extend([
        types.KeyboardButton(Command.NEXT),
        types.KeyboardButton(Command.ADD_WORD),
        types.KeyboardButton(Command.DELETE_WORD)
    ])
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add(*buttons)
    return markup

def offer_reset_progress(message):
    """Функция предложения сброса прогресса при отсутствии слов для изучения.

    Отправляет сообщение пользователю с предложением сбросить прогресс, если у него
    закончились слова для изучения. Пользователь может ответить 'Да' или 'Нет'.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий информацию о пользователе и чате.
    """
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('Да'), types.KeyboardButton('Нет'))
    
    bot.send_message(
        message.chat.id,
        'Похоже, вы выучили все слова!🥇 Сбросить прогресс и начать заново?',
        reply_markup=markup
    )
    bot.register_next_step_handler(message, drop_progress)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def start_word_learning_session(message):
    """Основная функция для начала сессии обучения слов.
    
    Генерирует необходимые кнопки для перевода слова, сбрасывает прогресс обучения 
    при необходимости и обрабатывает команды пользователя.
    
    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий текст и информацию о пользователе.
    """
    if message.text == Command.START:
        user_id = get_user_id(message)
        if bot_db.count_words_to_learn(user_id) != 0: # проверка если в таблице words_to_learn ещё остались слова                                                       
            russian_word, english_word, example = bot_db.get_random_word(user_id) 
            bot.set_state(message.from_user.id, MyStates.russian_word, message.chat.id)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['english_word'] = english_word
            markup = generate_buttons(english_word)
            greeting = f"Выбери перевод слова:\n{russian_word.capitalize()}\nПример использования слова:\n{example}"
            bot.send_message(message.chat.id, greeting, reply_markup=markup)

            bot.register_next_step_handler(message, handle_user_answer)
        else:
            offer_reset_progress(message)
    elif message.text == Command.RULES or message.text == '/help':
        send_help(message)
    elif message.text == Command.START_AGAIN:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        yes_button = types.KeyboardButton('Да')
        no_button = types.KeyboardButton('Нет')
        markup.add(yes_button, no_button)            
        bot.send_message(message.chat.id, 'Сбросить прогресс и начать заново?', reply_markup=markup)
        bot.register_next_step_handler(message, drop_progress)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_user_answer(message):
    """Обрабатывает ответ пользователя на вопрос о переводе слова.

    Сравнивает ответ пользователя с правильным ответом и определяет дальнейшие действия 
    в зависимости от ввода.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий текст ответа.
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        english_word = data['english_word']
    user_id = get_user_id(message)
    user_message = message.text
    if user_message:
        if user_message.lower() == english_word.lower():
            handle_correct_answer(message, user_id)
        elif user_message in ['/start', '/menu', '/subscribe', '/unsubscribe']:
            handle_special_commands(message)
        elif user_message == Command.NEXT:
            start_new_round(message)
        elif user_message == Command.ADD_WORD:
            add_new_word(message, user_id)
        elif user_message == Command.DELETE_WORD:
            delete_word(message, user_id)
        else:
            handle_incorrect_answer(message)
    else:
        bot.send_message(message.chat.id, "Я не понимаю это сообщение!")
        start_new_round(message)

def handle_correct_answer(message, user_id):
    """Обрабатывает правильный ответ пользователя.

    Увеличивает счетчик изучения слова и выводит сообщение о том, что слово выучено 
    достигнув определенного количества раз (5).

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий текст ответа.
        user_id (int): ID пользователя.
    """
    bot.send_message(message.chat.id, '✅ Верно!')
    bot_db.add_learn_counter(user_id, message.text)
    
    if bot_db.check_if_learnt(user_id, message.text) == 5:
        bot.send_message(message.chat.id, f'🎉Вы выучили слово {message.text}, угадав его 5 раз!🏆')
    
    start_new_round(message)

def handle_incorrect_answer(message):
    """Обрабатывает неправильный ответ пользователя.

    Выводит сообщение о неверном ответе и запрашивает новый ответ от пользователя.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий текст ответа.
    """
    bot.send_message(message.chat.id, '❌ Не верно. Попробуйте ещё')
    bot.register_next_step_handler(message, handle_user_answer)

def handle_special_commands(message):
    """Обрабатывает специальные команды от пользователя.

    Вызывает соответствующие функции для выполнения команд, таких как 
    отображение меню, подписка и отписка.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий текст команды.
    """
    command_handlers = {
        '/start': show_menu,
        '/menu': start_message,
        '/subscribe': handle_subscribe,
        '/unsubscribe': handle_unsubscribe
    }
    
    command = message.text
    command_handlers[command](message)

def start_new_round(message):
    """Начинает новый раунд обучения.

    Обновляет текст сообщения для начала нового раунда обучения.

    Параметры:
        message (Message): Объект сообщения от пользователя, который будет использован для начала нового раунда.
    """
    message.text = Command.START
    start_word_learning_session(message)

def add_new_word(message, user_id):
    """Добавляет новое слово в базу данных.

    Увеличивает количество слов для изучения и выводит сообщение об успешном добавлении нового слова.
    Выводит количество изучаемых слов и количество уже изученных слов.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий информацию о пользователе.
        user_id (int): ID пользователя.
    """
    if len(bot_db.all_words_ids(user_id)) == len(bot_db.all_main_words_ids()):
        bot.send_message(message.chat.id, f'❌ Вы добавили максимальное количество слов')
        start_new_round(message)
    else:
        new_word = bot_db.word_id_to_word(bot_db.add_word(user_id))
        bot.send_message(message.chat.id, f'🆕Добавлено новое слово для изучения: {new_word}\n'
                                        f'📜Количество изучаемых слов: {bot_db.count_words_to_learn(user_id)}\n'
                                        f'🧠Слов изучено: {bot_db.count_words_already_learnt(user_id)}')
        start_new_round(message)

def delete_word(message, user_id):
    """Удаляет слово из базы данных.

    Удаляет указанное слово из базы данных и выводит сообщение об успешном удалении.

    Параметры:
        message (Message): Объект сообщения от пользователя, содержащий информацию о пользователе.
        user_id (int): ID пользователя.
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        # russian_word = data['russian_word']
        english_word = data['english_word']
    bot_db.delete_word(user_id, english_word)
    bot.send_message(message.chat.id, f'🗑️Слово удалено: {english_word}')
    start_new_round(message)

if __name__ == '__main__':
    print('Bot is running')
    bot.polling(none_stop=True)