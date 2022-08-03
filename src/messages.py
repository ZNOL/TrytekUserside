from telethon import events
from src.keyboards import *


async def task_updater():
    """
    Обработчик появления новых заданий на USERSIDE
    Каждые 20 секунд получает все задания, которые были обновлены с момента последнего запроса
    """
    prev = datetime.now()
    while True:
        tmp = datetime.now()
        response = get_all_tasks(prev)
        prev = tmp
        if response['count'] != 0:
            for task_id in map(int, response['list'].split(',')):
                stateId = task_get_state(task_id)
                flag = True
                for divId in get_executors(task_id):
                    name = get_division(divId, name=True)['name']
                    if 'Календарь' in name:
                        flag = False
                        break
                if flag:
                    if task_id not in current_tasks and stateId != 2 and stateId != 95:
                        await new_event(task_id)
                    elif task_id not in current_tasks and stateId == 95:
                        await new_event(task_id, hide_buttons=True)
                    elif task_id in current_tasks and stateId == 2:
                        del current_tasks[task_id]
                elif task_id in current_tasks and stateId == 2:
                    del current_tasks[task_id]
        await asyncio.sleep(20)


async def trash_cleaner():
    """
    Очищает мусор, время которого пришло
    """
    while True:
        for data in trash_get(datetime.now()):
            try:
                await bot.delete_messages(data['chat_id'], data['message_id'])
            except Exception as e:
                logging.error(str(e))
            trash_delete(data['time'])
        await asyncio.sleep(60)


async def new_event(taskId, hide_buttons=False):
    """
    Оповещение пользователю о новой задаче
    :param taskId: ID задачи из USERSIDE
    :param hide_buttons: флаг для скрытия задач на перенаправление
    """
    telegramId, txt = task_make_txt(taskId)
    try:
        if not hide_buttons:
            template = await make_main_redirect_buttons(taskId)
        else:
            template = await make_show_buttons(taskId)

        await bot.send_message(telegramId, txt, buttons=template)
        current_tasks[taskId] = TASK(taskId, new=True)
        logging.info(f'NEW TASK {taskId}')
    except Exception as e:
        logging.error(str(e))


@bot.on(events.NewMessage(outgoing=True))
async def new_outgoing_message(event):
    try:
        id = event.peer_id.user_id
    except Exception as e:
        id = event.peer_id.channel_id
    text, media = event.raw_text, event.media
    # print('FROM USERSIDE', id, text)
    # await event.delete()


@bot.on(events.NewMessage(incoming=True))
async def new_message(event):
    try:
        id = event.peer_id.user_id
        flag = True
    except Exception as e:
        try:
            id = event.peer_id.channel_id
            flag = False
        except Exception as e:
            id = event.peer_id.chat_id
            flag = False
    text, media = event.raw_text, event.media

    logging.info(f'Message|{id}: {text}')

    if '/start' == text:  # отправка стартвой клавиатуры
        await event.delete()
        txt = 'Вас приветсвует бот Trytek для интеграции с USERSIDE'
        if id not in users:
            users[id] = USER(id, new=True)
        template = main_keyboard[::]
        if id in storekeepers:
            template += storekeeper_keyboard[::]
        await bot.send_message(id, txt, buttons=template)
        await event.delete()

    elif '/get_id' == text:  # получение ID текущего чата/пользователя
        await event.delete()
        txt = f'ID = `{id}`'
        await bot.send_message(id, txt)

    elif '🗿Авторизация' == text:  # данные о авторизации
        await event.delete()
        txt = f'Текущий логин: {users[id].login}'
        await bot.send_message(id, txt, buttons=[Button.inline('Обновить логин', 'new_login')])

    elif '⏏️Выйти' == text:  # возвращение к основной клавиатуре
        await event.delete()
        txt = 'Основная клавиатура'
        template = main_keyboard[::]
        if id in storekeepers:
            template += storekeeper_keyboard[::]
        await bot.send_message(id, txt, buttons=template)
        await users[id].comments_message.delete()
        users[id].change_comments_message(None)

    elif '🔖Типовые комментарии' == text:  # создание клавиатуры для типовых комментариев
        await event.delete()
        template = await make_comments_keyboard(users[id].startIdx)
        old = await bot.send_message(id, 'Комментарии', buttons=template)
        users[id].change_comments_message(old)

    elif '📦Отчеты по складу' == text:  # выбор города для формирования отчёта по складу
        await event.delete()
        txt = 'Выберите город'
        template = [
            Button.inline('Приступить↗️', 'inventory'),
            Button.inline('❌Отмена', 'stop')
        ]
        await bot.send_message(id, txt, buttons=template)

    elif '➡️' == text:  # перелистывание типовый комментариев вправо
        await event.delete()
        users[id].change_startIdx(+5)
        template = await make_comments_keyboard(users[id].startIdx)
        old = await bot.send_message(id, 'Комментарии', buttons=template)
        try:
            await users[id].comments_message.delete()
        except AttributeError:
            pass
        users[id].change_comments_message(old)

    elif '⬅️' == text:  # перелистывание типовый комментариев влево
        await event.delete()
        users[id].change_startIdx(-5)
        template = await make_comments_keyboard(users[id].startIdx)
        old = await bot.send_message(id, 'Комментарии', buttons=template)
        try:
            await users[id].comments_message.delete()
        except AttributeError:
            pass
        users[id].change_comments_message(old)

    elif id in users and int(users[id].get_current_task()) != 0:   # закрытие или пересылка задачи при работе в городе
        taskId = users[id].get_current_task()
        users[id].change_current_task(0)

        action = current_tasks[taskId].get_action()

        commentId = comment_add(taskId, text, users[id].jobId)

        trash_add(datetime.now(), event.original_update.message)

        name = employee_data(users[id].jobId, short_name=True)['short_name']
        if action[0] == 1:  # закрытие задачи
            task_change_state(taskId, 2)
            chatId = sub_divisions[action[1]][action[2]].tgId
            del current_tasks[taskId]

            old = await bot.send_message(id, f'Задача {taskId} выполнена!')
            trash_add(datetime.now(), old)

            try:
                txt = f'Задача {taskId} выполнена!\nКомментарий: {task_get_comment(taskId, commentId)}\n'\
                      f'Закрыл задачу: {name}\n\n'\
                      f'[🔗Ссылка на задание]'\
                      f'(http://{link_url}.trytek.ru/oper/?core_section=task&action=show&id={taskId})'
                old = await bot.send_message(chatId, txt)
            except Exception:
                old = await bot.send_message(id, 'Уведомление не отправлено в общий чат')
            trash_add(datetime.now(), old)

        elif action[0] == 2:  # перенаправление задачи #TODO ERROR
            parentId, divId = action[1], action[2]

            chatId = sub_divisions[parentId][divId].tgId
            if chatId == '':
                chatId = main_divisions[parentId].tgId

            try:
                task_change_state(taskId, 1)

                template = await make_accept_buttons(taskId)

                for prevDivId in get_executors(taskId):
                    division_delete(taskId, prevDivId, users[id].jobId)
                division_add(taskId, divId, users[id].jobId)

                authorId, txt = task_make_txt(taskId, last_comment=commentId)
                await bot.send_message(chatId, txt, buttons=template)
                old = await bot.send_message(
                    id,
                    f'🟢Задача {taskId} перенаправлена в {sub_divisions[parentId][divId].name}'
                )
                trash_add(datetime.now(), old)
            except Exception as e:
                logging.error(str(e) + 'TODO!')
                old = await bot.send_message(
                    id, 
                    f'🔴Возникла проблема при перенаправлении задачи\n'\
                    f'(chatId = {chatId}, parentId = {parentId}, divId = {divId})'
                )
                trash_add(datetime.now(), old)

    elif id in login_updaters:  # получение логина и пароля
        await event.delete()
        if len(text.split()) != 2:
            old = await bot.send_message(id, '🔴Неверный формат данных\nПовторите отправку', buttons=[
                Button.inline('❌Отмена', 'stop'),
            ])
        elif check_password(*text.split()):
            login_updaters.discard(id)
            login = text.split()[0]
            users[id].update_login(login)
            old = await bot.send_message(id, f'🟢Установлен новый login: {login}')
        else:
            login_updaters.discard(id)
            old = await bot.send_message(id, '🔴Неверный логин/пароль', buttons=[
                Button.inline('🔄Повторить', 'new_login'),
                Button.inline('❌Отмена', 'stop'),
            ])
        trash_add(datetime.now(), old)

    elif id in report_waiters:  # получение даты для отчёта типа "1"
        await event.delete()
        divId = report_waiters[id]
        try:
            date_start, date_finish = map(lambda x: datetime.strptime(x, '%d.%m.%y'), text.split(' '))
            date_finish += timedelta(days=1)
            if date_start > date_finish:
                raise ValueError
            del report_waiters[id]

            result = make_operation_excel(divId, date_start, date_finish)
            if result == 0:
                await bot.send_file(
                    id,
                    file=main_root + 'files/record.xlsx',
                    caption=f'Файл от {date_start.date()} до {date_finish.date()}',
                )
            else:
                old = await bot.send_message(id, 'Ошибка при формировании отчёта')
                trash_add(datetime.now(), old)
        except ValueError:
            txt = 'Неверный формат данных\nПовторите отправку\nПример: «01.01.21 01.03.21»'
            old = await bot.send_message(id, txt, buttons=Button.inline('❌Отмена', 'stop'))
            trash_add(datetime.now(), old)

    else:  # удаление необработанных сообщения в личке бота
        if flag:
            await event.delete()
