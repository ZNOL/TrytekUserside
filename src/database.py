import pymysql
from src.bot import *
from datetime import datetime, timedelta


def on_start(createBase=False, createTables=False, showTables=False):
    """
    Настройка MySQL при первом запуске
    :param createBase: изменить на True для создания базы данных
    :param createTables: изменить на True для создания полей в таблице
    :param showTables: изменить на True для получения описания таблиц
    """
    if createBase:
        create_db_query = f'CREATE DATABASE {DB_DATABASE}'
        with pymysql.connect(
            # host=DB_HOST,
            unix_socket=DB_SOCKET,
            user=DB_USER,
            password=DB_PASSWORD,
            cursorclass=pymysql.cursors.DictCursor
        ) as con:
            with con.cursor() as cursor:
                cursor.execute(create_db_query)
                con.commit()
    if createTables:
        drop_users_table_query = 'DROP TABLE IF EXISTS `users`'
        create_users_table_query = '''
                CREATE TABLE `users` (
                    `user_id` bigint NOT NULL PRIMARY KEY,
                    `login` varchar(45) DEFAULT NULL,
                    `job_id` int DEFAULT 0,
                    `current_task` int DEFAULT 0
                );        
                '''
        drop_tasks_table_query = 'DROP TABLE IF EXISTS `tasks`'
        create_tasks_table_query = '''
                CREATE TABLE `tasks` (
                    `task_id` bigint NOT NULL PRIMARY KEY,
                    `telegram_id` int DEFAULT 0,
                    `action_id` int DEFAULT 0,
                    `parent_id` int DEFAULT 0,
                    `div_id` int DEFAULT 0
                );
                '''
        drop_trash_table_query = 'DROP TABLE IF EXISTS `trash`'
        create_trash_table_query = '''
                CREATE TABLE `trash` (
                    `time` datetime NOT NULL PRIMARY KEY,
                    `chat_id` int NOT NULL,
                    `message_id` int NOT NULL
                );
                '''
        with pymysql.connect(
            # host=DB_HOST,
            unix_socket=DB_SOCKET,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        ) as con:
            with con.cursor() as cursor:
                cursor.execute(drop_users_table_query)
                con.commit()
                cursor.execute(create_users_table_query)
                con.commit()
                cursor.execute(drop_tasks_table_query)
                con.commit()
                cursor.execute(create_tasks_table_query)
                con.commit()
                cursor.execute(drop_trash_table_query)
                con.commit()
                cursor.execute(create_trash_table_query)
                con.commit()
    if showTables:
        show_users_query = 'DESCRIBE users'
        show_tasks_query = 'DESCRIBE tasks'
        show_trash_query = 'DESCRIBE trash'
        with pymysql.connect(
                # host=DB_HOST,
                unix_socket=DB_SOCKET,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_DATABASE,
                cursorclass=pymysql.cursors.DictCursor
        ) as con:
            with con.cursor() as cursor:
                cursor.execute(show_users_query)
                result = cursor.fetchall()
                print(*result, sep='\n')
                cursor.execute(show_tasks_query)
                result = cursor.fetchall()
                print(*result, sep='\n')
                cursor.execute(show_trash_query)
                result = cursor.fetchall()
                print(*result, sep='\n')


def commit_execute(sql, values=None):
    """
    :param sql: комманда MySQL
    :param values: tuple с данными для комманды
    """
    with pymysql.connect(
            # host=DB_HOST,
            unix_socket=DB_SOCKET,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor,

    ) as con:
        with con.cursor() as cursor:
            try:
                cursor.execute(sql, values)
                con.commit()
                logging.info(f'SUCCESS: {sql}')
            except Exception as e:
                logging.error(str(e))


def fetchone_execute(sql, values=None):
    """
    :param sql: комманда MySQL
    :param values: tuple с данными для комманды
    :return: 1 словарь с данными из таблицы
    """
    with pymysql.connect(
            # host=DB_HOST,
            unix_socket=DB_SOCKET,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor,
    ) as con:
        with con.cursor() as cursor:
            try:
                cursor.execute(sql, values)
                logging.info(f'SUCCESS: {sql}')
                return cursor.fetchone()
            except Exception as e:
                logging.error(str(e))
                return ()


def fetchall_execute(sql, values=None):
    """
    :param sql: комманда MySQL
    :param values: tuple с данными для комманды
    :return: возвращает несколько словарей, сформированных запросом
    """
    with pymysql.connect(
            # host=DB_HOST,
            unix_socket=DB_SOCKET,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            cursorclass=pymysql.cursors.DictCursor,
    ) as con:
        with con.cursor() as cursor:
            try:
                cursor.execute(sql, values)
                logging.info(f'SUCCESS: {sql}')
                return cursor.fetchall()
            except Exception as e:
                logging.error(str(e))
                return ()


def users_add(telegramId):
    """
    Добавление нового пользователя в базу
    :param telegramId: ID пользователя из Telegram
    """
    sql = f'INSERT INTO users (user_id) VALUES ({telegramId})'
    commit_execute(sql)


def users_update(telegramId, field, new_val):
    """
    Обновления поля в базе пользователей
    :param telegramId: ID пользователя из Telegram
    :param field: поле для обновления
    :param new_val: новое значение
    """
    sql = f'UPDATE `users` SET `{field}` = %s WHERE `user_id` = %s'
    commit_execute(sql, (new_val, telegramId))


def users_get_current(telegramId):
    """
    :param telegramId: ID пользователя из Telegram
    :return: ID задачи из USERSIDE, с которой работает пользователь
    """
    sql = f'SELECT current_task FROM users WHERE user_id = {telegramId}'
    try:
        return fetchone_execute(sql)['current_task']
    except Exception as e:
        logging.error(str(e))


def users_get_all():
    """
    Получения данных о всех пользователях, содержащихся в таблице
    """
    sql = 'SELECT user_id, login, job_id FROM users'
    return fetchall_execute(sql)


def task_add(taskId):
    """
    Добавление новое задачи в базу
    :param taskId: ID задачи из USERSIDE
    """
    sql = f'INSERT INTO tasks (task_id) VALUES ({taskId})'
    commit_execute(sql)


def task_update(taskId, field, new_val):
    """
    Обновления поля в базе задач
    :param taskId: ID задачи из USERSIDE
    :param field: поле для обновления
    :param new_val: новое значение
    """
    sql = f'UPDATE `tasks` SET `{field}` = %s WHERE `task_id` = %s'
    commit_execute(sql, (new_val, taskId))


def task_delete(taskId):
    """
    Удаление информации о задачи из базы
    :param taskId: ID задачи из USERSIDE
    """
    sql = f'DELETE FROM tasks WHERE `task_id` = {taskId}'
    commit_execute(sql)


def task_get_action(taskId):
    """
    Получение ID действия с заданием
    :param taskId: ID задачи из USERSIDE
    """
    sql = f'SELECT action_id, parent_id, div_id FROM tasks WHERE task_id = {taskId}'
    return fetchone_execute(sql)


def task_get_all():
    """
    Получение всех задач из базы данных
    """
    sql = 'SELECT task_id, telegram_id, action_id, parent_id, div_id FROM tasks'
    return fetchall_execute(sql)


def trash_add(time, message):
    """
    Добавление нового сообщения в корзина
    :param time: время, после которого нужно удалить сообщение
    :param message: Message entity from Telethon
    :return:
    """
    time += timedelta(minutes=delete_minutes)
    messageId = message.id
    try:
        chatId = message.peer_id.user_id
    except Exception as e:
        try:
            chatId = message.peer_id.channel_id
        except Exception as e:
            chatId = message.peer_id.chat_id
    sql = f'INSERT INTO trash (time, chat_id, message_id) VALUES (%s, %s, %s)'
    with pymysql.connect(
        # host=DB_HOST,
        unix_socket=DB_SOCKET,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    ) as con:
        with con.cursor() as cursor:
            try:
                cursor.execute(sql, (time, chatId, messageId))
                con.commit()
                logging.info(f'NEW TRASH {messageId} FROM {chatId}')
            except Exception as e:
                time += timedelta(minutes=0.5)
                try:
                    cursor.execute(sql, (time, chatId, messageId))
                    con.commit()
                    logging.info(f'NEW TRASH {messageId} FROM {chatId}')
                except Exception as e:
                    logging.error(str(e))


def trash_get(time=None):
    """
    Получение всех сообщений, время которых пришло
    :param time: текущее время
    """
    sql = 'SELECT time, chat_id, message_id FROM trash'
    if time is not None:
        sql += f' WHERE time <= %s'
        values = (time, )
    else:
        values = None
    return fetchall_execute(sql, values)


def trash_delete(time):
    """
    Удаление сообщения из базы
    :param time: время отправки сообщения
    """
    sql = 'DELETE FROM `trash` WHERE `time` = %s'
    commit_execute(sql, (time, ))


try:
    connection = pymysql.connect(
        # host=DB_HOST,
        unix_socket=DB_SOCKET,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )
    # on_start(createTables=True, showTables=True)
    logging.info('BASE CONNECTED')
except Exception as e:
    logging.error(str(e))
    on_start(createBase=True, createTables=True)
