import schedule
import time
import threading

class Notification:
    """
    Класс для управления подписками на ежедневные напоминания.

    Атрибуты:
        subscribers (dict): Словарь, где ключами являются идентификаторы пользователей,
    подписанных на напоминания.

    Методы:
        __init__(bot): Инициализация класса Notification.
        start(message): Подписка пользователя на ежедневные напоминания.
        stop(message): Отписка пользователя от ежедневных напоминаний.
        send_reminders(): Фоновая задача для проверки и отправки напоминаний подписанным пользователям.
        job(): Отправка напоминаний всем подписанным пользователям.
    """
    subscribers={}

    def __init__(self, bot):
        """
        Инициализация класса Notification.

        Параметры:
            bot (object): Объект бота для отправки сообщений.
        """
        self.bot = bot
        

    def start(self, message):
        """
        Подписка пользователя на ежедневные напоминания.

        Параметры:
            message (Message): Сообщение от пользователя, содержащее информацию о чате.
        """
        user_id = message.chat.id
        if user_id not in self.subscribers:
            self.subscribers[user_id] = True
            self.bot.reply_to(message, 'Вы подписались на ежедневные напоминания о изучении английского языка!')
        else:
            self.bot.reply_to(message, 'Вы уже подписаны!')

    def stop(self, message):
        """
        Отписка пользователя от ежедневных напоминаний.

        Параметры:
            message (Message): Сообщение от пользователя, содержащее информацию о чате.
        """
        user_id = message.chat.id
        if user_id in self.subscribers:
            del self.subscribers[user_id]
            self.bot.reply_to(message, 'Вы отписались от ежедневных напоминаний.')
        else:
            self.bot.reply_to(message, 'Вы не подписаны на напоминания.')

    def send_reminders(self):
        """
        Фоновая задача для проверки и отправки напоминаний подписанным пользователям.

        Этот метод запускает бесконечный цикл, который проверяет запланированные задачи
        и ждет 10 секунд между проверками.
        """
        while True:
            schedule.run_pending()
            time.sleep(10)

    def job(self):
        """
        Отправка напоминаний всем подписанным пользователям.

        Этот метод рассылает сообщение всем пользователям, которые подписались на напоминания.
        """
        for user_id in self.subscribers.keys():
            self.bot.send_message(user_id, 'Не забудьте поучить английский язык сегодня! 📚')
        
def start_reminders(bot):
    """
    Запуск напоминаний для подписанных пользователей.

    Параметры:
        bot (object): Объект бота для отправки сообщений.
    """
    notification = Notification(bot)

    # Запланировать напоминание на каждый день в 12:00
    schedule.every().day.at("12:00").do(notification.job)

    # Запуск потока для работы с задачами
    thread = threading.Thread(target=notification.send_reminders)
    thread.daemon = True
    thread.start()