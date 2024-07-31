import psycopg2
from typing import List
from random import randint


class BotDB:
    """Класс управления базой данных с помощью модуля psycopg2.

    Этот класс предоставляет методы для взаимодействия с базой данных,
    включая операции создания, чтения, обновления и удаления (CRUD).
    Он позволяет управлять словами, пользователями и анализировать
    прогресс в изучении слов.
    
    Атрибуты:
        connection (psycopg2.extensions.connection): Соединение с базой данных.
        
    Методы:
        word_to_word_id: Получает идентификатор слова (word_id) из таблицы слов.
        word_id_to_word: Получает слово из его идентификатора (word_id) из таблицы слов.
        all_users_list: Возвращает список всех пользователей из таблицы users.
        generate_10_words: Генерирует 10 случайных слов для пользователя и записывает их в таблицу words_to_users.
        register_user: Добавляет нового пользователя в таблицу users, если он отсутствует.
        drop_progress: Обнуляет прогресс для указанного пользователя.
        get_random_word: Выбирает случайное слово, его перевод и пример использования для определенного пользователя.
        get_random_examples: Извлекает случайное слово, перевод и пример использования из общей базы слов.
        delete_word: Удаляет указанное слово из списка изучаемых слов.
        all_words_ids: Возвращает идентификаторы всех слов из таблицы слов, предназначенных для изучения.
        all_main_words_ids: Возвращает идентификаторы всех слов из общей таблицы слов.
        count_words_to_learn: Подсчитывает количество слов, которые ещё не изучены до конца.
        count_words_already_learnt: Возвращает количество слов, которые уже изучены.
        add_word: Добавляет слово в список изучаемых слов из общей таблицы слов.
        add_learn_counter: Увеличивает счетчик изученности слова на 1.
        check_if_learnt: Проверяет, изучено ли слово.

    Примечания:
        Убедитесь, что установлено соединение с базой данных перед вызовом методов,
        требующих взаимодействия с ней.
    """

    def __init__(self):
        self.conn = psycopg2.connect(database='easyenglish_db', user='postgres', password='12341')
        self.cur = self.conn.cursor()

    def word_to_word_id(self, word: str) -> int:
        """
        Получает word_id из word из общей таблицы слов (words).

        Параметры:
            self: Экземпляр класса.
            word: (str): Слово.

        Возвращает:
            int: Идентификатор слова.

        """
        self.cur.execute("""
                         SELECT word_id 
                         FROM words
                         WHERE translation LIKE %s;
                         """, (word,))
        return self.cur.fetchone()
    
    def word_id_to_word(self, word_id: int) -> str:
        """
        Получает word из word_id из общей таблицы слов (words).

        Параметры:
            self: Экземпляр класса.
            word: (str): Слово

        Возвращает:
            int: Идентификатор слова.

        """
        self.cur.execute("""
                         SELECT word 
                         FROM words
                         WHERE word_id=%s;
                         """, (word_id,))
        return self.cur.fetchone()[0]
    
    def all_users_list(self) -> List[int]:
        """
        Получает список всех пользователей в таблице users.

        Параметры:
            self: Экземпляр класса.

        Возвращает:
            List[int]: Cписок всех пользователей в таблице users.

        """
        self.cur.execute("""
                         SELECT user_id
                         FROM users;
                 """)
        res = self.cur.fetchall()
        res_int = list(map(lambda x: int(x[0]), res))
        return res_int
    
        
    def generate_10_words(self, user_id: int, learn_counter: int=0) -> None:
        """
        Генерирует 10 случайных слов для пользователя и записывает в таблицу words_to_users.

        Параметры:
            user_id (int): Идентификатор пользователя.
            learn_counter (int, необязательный): Счетчик обучения, по умолчанию равен 0.

        Возвращает:
            None
        """
        used_ids = []
        for _ in range(10):
            while True:
                word_id = randint(1, 40)
                if word_id not in used_ids:
                    used_ids.append(word_id)
                    break
        for id in used_ids:
            word_id = id
            self.cur.execute("""
                                INSERT INTO words_to_users(word_id, user_id, learn_counter) 
                                VALUES(%s, %s, %s);
                                """, (word_id, user_id, learn_counter))
        return self.conn.commit()
    
    def register_user(self, user_id: int) -> None:
        """
        Добавляет нового пользователя в таблицу users если отстуствует.

        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.

        Возвращает:
            None
        
        """
        if user_id not in self.all_users_list():
            self.cur.execute ("""
                         INSERT INTO users(user_id)
                         VALUES(%s);
                 """, (user_id,))
            self.generate_10_words(user_id)
        return self.conn.commit()
    
    def drop_progress(self, user_id: int) -> None:
        """
        Обнуление прогресса для конкретного пользователя.

        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.

        Возвращает:
            None        
        """
        self.cur.execute("""
            DELETE FROM words_to_users 
            WHERE user_id=%s;
                """, (user_id,))
        self.cur.execute("""
            DELETE FROM users 
            WHERE user_id=%s;
                """, (user_id,))
        return self.conn.commit()
    
    def get_random_word(self, user_id: int) -> tuple:
        """
        Выбирает случайное слово, перевод и пример использования из таблицы для конкретного пользователя.

        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.

        Возвращает:
            tuple: Кортеж из трёх значений: слово, перевод, пример.
        """
        self.cur.execute("""
                    SELECT word, translation, definition from words
                    JOIN words_to_users
                    ON  words_to_users.word_id =  words.word_id
                    WHERE user_id=%s AND words_to_users.learn_counter < 5
                    ORDER by random();
                    """, (user_id,))
        res = self.cur.fetchone()
        word, translation, example = res[0], res[1], res[2]
        return word, translation, example
    

    def get_random_examples(self) -> tuple:
        """
        Выбирает случайное слово, перевод и пример использования из общей базы слов.

        Параметры:
            self: Экземпляр класса.

        Возвращает:
            tuple: Кортеж из трёх значений: слово, перевод, пример.
        """
        self.cur.execute("""
                    SELECT word, translation, definition from words
                    ORDER by random();
                    """,)
        res = self.cur.fetchone()
        word, translation, example = res[0], res[1], res[2]
        return word, translation, example
    
    def delete_word(self, user_id:int , word: str) -> None:
        """
        Удаляет слово из списка изучаемых слов.
        
        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.
            word (str): Слово, которое требуется удалить.

        Возвращает:
            tuple: Кортеж из трёх значений: слово, перевод, пример.
        """
        word_id = self.word_to_word_id(word)
        self.cur.execute("""
                            DELETE FROM words_to_users
                            WHERE word_id=%s AND user_id=%s;
                        """, (word_id, user_id))
        return self.conn.commit()
    

    def all_words_ids(self, user_id: int) -> List[int]:
        """
        Возвращает id всех слов из таблицы слов для изучения.

        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.
        
        Возвращает:
            List[int]: Список целых чисел (уникальные идентификаты слов).
        """
        self.cur.execute("""
                         SELECT word_id
                         FROM words_to_users
                         WHERE user_id=%s;
                 """, (user_id,))
        res = self.cur.fetchall()
        res_int = list(map(lambda x: int(x[0]), res))
        return res_int
    
    def all_main_words_ids(self) -> List[int]:
        """
        Возвращает id всех слов из общей таблицы слов.

        Параметры:
            self: Экземпляр класса.

        Возвращает:
            List[int]: Список целых чисел (уникальные идентификаты слов).
        """
        self.cur.execute("""
                         SELECT word_id
                         FROM words;
                 """)
        res = self.cur.fetchall()
        res_int = list(map(lambda x: int(x[0]), res))
        return res_int
    
    def count_words_to_learn(self, user_id: int) -> int:
        """
        Подсчитывает количество слов из таблицы слов для изучения, которые ещё не изучены до конца.

        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.
        
        Возвращает:
            int: Количество слов, счётчик изученности которых меньше 5.
        """
        self.cur.execute("""
                         SELECT word_id
                         FROM words_to_users
                         WHERE user_id=%s AND learn_counter < 5;
                 """, (user_id,))
        res = self.cur.fetchall()
        return len(res)
    
    def count_words_already_learnt(self, user_id: int) -> int:
        """
        Возвращает количество слов из таблицы слов для изучения, которые уже изучены.
        
        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.
        
        Возвращает:
            int: Количество слов, счётчик изученности которых больше или равен 5.
        """
        self.cur.execute("""
                         SELECT word_id
                         FROM words_to_users
                         WHERE user_id=%s AND learn_counter >= 5;
                 """, (user_id,))
        res = self.cur.fetchall()
        return len(res)

    def add_word(self, user_id: int, learn_counter: int=0) -> int:
        """
        Добавляет слово в список изучаемых слов из общей таблицы слов.

        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.
            learn_counter (int, необязательный): Счетчик обучения, по умолчанию равен 0.

        Возвращает:
            int: Идентификатор слова в таблице слов для изучения.
        """
        while True:
            word_id = randint(1, 40)
            all_ids = self.all_words_ids(user_id)
            if word_id not in all_ids:
                break
        self.cur.execute("""
                            INSERT INTO words_to_users(word_id, user_id, learn_counter) 
                            VALUES(%s, %s, %s);
                        """, (word_id, user_id, learn_counter))
        self.conn.commit()
        return word_id
    
    def add_learn_counter(self, user_id:int , word: str) -> None:
        """
        Добавляет +1 к счётчику изученности слова.

        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.
            word (str): Слово, счётчик изученности которого нужно увеличить.

        Возвращает:
            None
        """
        word_id = self.word_to_word_id(word)
        self.cur.execute("""
                            UPDATE words_to_users
                            SET learn_counter=learn_counter+1
                            WHERE word_id=%s
                            AND user_id=%s;
                        """, (word_id, user_id))
        return self.conn.commit()

    def check_if_learnt(self, user_id, word) -> int:
        """
        Проверка изученности слова.

        Параметры:
            self: Экземпляр класса.
            user_id (int): Идентификатор пользователя.
            word (str): Слово, счётчик изученности которого нужно узнать.

        Возвращает:
            int: Количество угадываний из списка изучаемых слов для конкретного слова.
        """
        word_id = self.word_to_word_id(word)
        self.cur.execute("""
                         SELECT learn_counter
                         FROM words_to_users
                         WHERE word_id=%s AND user_id=%s;
                 """, (word_id, user_id))
        return self.cur.fetchone()[0]

bot_db=BotDB()
