import requests
import psycopg2
import configparser


class Fill_DB:
    """Класс для создания схемы БД, её наполнения с помощью сервисов Yandex API и Free Dictionary API.

    Этот класс предназначен для работы с базой данных, включая
    создание ее схемы и наполнения данными, полученными через
    различные API. Он обеспечивает методы для создания как
    самой базы данных, так и таблиц, а также для работы
    с переводами и примерами слов.

    Методы:
        get_settings: Читает данные из конфигурационного файла.
        create_database: Создает базу данных, если она не существует.
        create_tables: Создает необходимые таблицы для хранения данных.
        get_token: Получает токен доступа для Yandex Dictionary API.
        translate_word: Выполняет перевод слова с английского на русский.
        get_example: Определяет примеры использования слова в контексте.
        load_data: Наполняет базу данных данными, полученными через API.

    Примечания:
        Убедитесь, что у вас есть все необходимые ключи и токены
        для доступа к API перед использованием методов.
        Ключи хранятся в файле настроек settings.ini
    """

    def __init__(self, database: str) -> None:
        """
        Инициализация соединения с базой данных PostgreSQL.

        Параметры:
            database (str): Имя Базы Данных.

        Создает соединение с базой данных 'easyenglish_db', настраивает курсор и
        устанавливает режим автокоммита для всех транзакций.
        """
        self.database = database
        database, user, password, host, port = Fill_DB.get_settings()
        self.conn = psycopg2.connect(
            database=self.database, user=user, password=password, host=host, port=port
        )
        self.cur = self.conn.cursor()
        self.conn.autocommit = True

    def __enter__(self) -> None:
        """
        Позволяет использовать класс в качестве контекстного менеджера.

        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Закрывает курсор и соединение при выходе из контекстного менеджера.

        Параметры:
            exc_type (type): Тип исключения, возникшего в блоке with.
            exc_val (Exception): Значение исключения.
            exc_tb (traceback): Объект трассировки.
        """
        self.cur.close()
        self.conn.close()

    def get_settings(file_name: str='settings.ini') -> tuple:
        """
        Читает данные из конфигурационного файла.

        Параметры:
            file_name (str): Имя файла конфигурации.

        Возвращает:
            tuple: Данные для подключения к БД
        """
        config = configparser.ConfigParser()
        config.read(file_name)
        database = config["SETTINGS"]["database"]
        user = config["SETTINGS"]["user"]
        password = config["SETTINGS"]["password"]
        host = config["SETTINGS"]["host"]
        port = config["SETTINGS"]["port"]
        return database, user, password, host, port

    def create_database() -> None:
        """
        Создает новую базу данных с именем 'easyenglish_db'.

        Метод соединяется с базой данных 'postgres', создает новую базу данных и
        выводит сообщение об успешном создании. Если произошла ошибка, она будет выведена.
        """
        database, user, password, host, port = Fill_DB.get_settings()
        try:
            conn = psycopg2.connect(
                database=database, user=user, password=password, host=host, port=port
            )
            cursor = conn.cursor()
            conn.autocommit = True

            sql = """ CREATE database easyenglish_db """

            cursor.execute(sql)
            print("Database has been created successfully")
            conn.close()
        except Exception as e:
            print(e)

    def create_tables(self) -> None:
        """
        Создает таблицы в базе данных, если они не существуют.

        Создаются три таблицы: 'words', 'users' и 'words_to_users'. Метод выводит
        сообщение об успешном создании таблиц.
        """
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS words(
            word_id SERIAL PRIMARY KEY,
            word VARCHAR(40) UNIQUE NOT NULL,
            translation VARCHAR(40) NOT NULL,
            definition VARCHAR(900)
            );
        """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
            user_id SERIAL PRIMARY KEY);
        """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS words_to_users(
            word_id INTEGER NOT NULL REFERENCES words(word_id),
            user_id INTEGER NOT NULL REFERENCES users(user_id),
            learn_counter INTEGER NOT NULL,
            CONSTRAINT pk_word_chat PRIMARY KEY (word_id, user_id)
            );
        """
        )
        print("Tables has been created successfully")

    def get_token(self) -> tuple:
        """
        Получает токен API Yandex для использования с сервисом перевода.

        Считывает настройки из файла 'settings.ini' и возвращает кортеж с токеном
        и URL API.

        Возвращает:
            tuple: Токен и URL Yandex API.
        """
        config = configparser.ConfigParser()
        config.read("settings.ini")
        self.token_ya = config["YANDEX"]["token_ya"]
        self.url = config["YANDEX"]["url"]
        return self.token_ya, self.url

    def translate_word(self, word: str) -> str:
        """
        Переводит указанное слово с английского на русский язык.

        Использует API Yandex для перевода слова и возвращает его перевод.

        Параметры:
            word (str): Слово на английском языке, которое необходимо перевести.

        Возвращает:
            str: Переведенное слово на русский языке или сообщение об ошибке.
        """
        token_ya, url = self.get_token()
        param = {"key": token_ya, "lang": "en-ru", "text": word, "ui": "en"}
        try:
            response = requests.get(url=url, params=param).json()
            return response["def"][0]["tr"][0]["text"]
        except Exception as e:
            return e

    def get_example(self, word: str) -> str:
        """
        Получает пример использования указанного слова из API.

        Если доступен пример, возвращается он; если нет, возвращается определение слова.

        Параметры:
            word (str): Слово, для которого нужно получить пример или определение.

        Возвращает:
            str: Пример использования слова или его определение, если пример отсутствует.
        """
        url = "https://api.dictionaryapi.dev/api/v2/entries/en/"
        response = requests.get(url=url + word).json()
        try:
            for i in response[0]["meanings"][0]["definitions"]:
                if "example" in i:
                    example = i["example"]
                    return example
                else:
                    return response[0]["meanings"][0]["definitions"][0]["definition"]
        except Exception as e:
            return e

    def load_data(self, file_name: str) -> None:
        """
        Заполняет базу данных словами из указанного файла.

        Читает файл построчно, переводит каждое слово и получает определение.

        Параметры:
            file_name (str): Путь к файлу, содержащему слова для загрузки.

        Возвращает:
            None
        """
        with open(file_name, encoding="utf-8") as f:
            for i in f.readlines():
                word = i.capitalize().replace("\n", "")
                translation = self.translate_word(word).capitalize()
                definition = self.get_example(word)
                if type(definition) is KeyError:
                    definition = "Sorry pal, we couldn't find definitions for the word you were looking for"
                    self.cur.execute(
                        """
                    INSERT INTO words(word, translation, definition) 
                    VALUES(%s, %s, %s);
                    """,
                        (word, translation, definition),
                    )
                else:
                    self.cur.execute(
                        """
                        INSERT INTO words(word, translation, definition) 
                        VALUES(%s, %s, %s);
                        """,
                        (word, translation, definition),
                    )
                    print(f"Word {word} has been added")
            print(f"Total uploaded words: {f.readlines().__len__()}")


if __name__ == "__main__":
    database = "easyenglish_db"
    Fill_DB.create_database()
    with Fill_DB(database) as fill_data_base:
        print(
            "Status OK" if fill_data_base.conn.closed == 0 else "Connection is closed"
        )
        fill_data_base.create_tables()
        fill_data_base.load_data("words.txt")
        print("Completed!")
    print(
        "Connection is closed"
        if fill_data_base.conn.closed == 1
        else "Close connection!"
    )
