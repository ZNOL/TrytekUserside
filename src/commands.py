from telethon import events
from src.keyboards import *


@bot.on(events.callbackquery.CallbackQuery())
async def new_button(event):
    try:
        id = event.original_update.user_id
    except Exception as e:
        id = ''
    command = event.original_update.data.decode('utf-8')

    logging.info(f'Command|{id}: {command}')

    if 'redirect' == command[:8]:  # Перенаправлении задачи от создателя в чат опредёлённого отдела в городе
        if command.count('=') == 1:  # выбор города
            taskId = int(command.split('=')[-1])
            template = await make_main_redirect_buttons(taskId)
            await event.edit(buttons=template)
        elif command.count('=') == 2:  # выбор подразделения
            parentId, taskId = map(int, command.split('=')[1:])
            template = await make_sub_redirect_buttons(parentId, taskId)
            await event.edit(buttons=template)
        elif command.count('=') == 3:  # отправка подразделению
            parentId, divId, taskId = map(int, command.split('=')[1:])
            chatId = sub_divisions[parentId][divId].tgId
            if chatId == '':
                chatId = main_divisions[parentId].tgId
            try:
                template = await make_accept_buttons(taskId)

                task_change_state(taskId, 1)
                task_change_type(taskId)

                watcher_add(taskId, users[id].jobId)

                for prevDivId in get_executors(taskId):
                    division_delete(taskId, prevDivId, users[id].jobId)
                division_add(taskId, divId, users[id].jobId)

                authorId, txt = task_make_txt(taskId)
                await bot.send_message(chatId, txt, buttons=template)
                old = await event.edit(f'🟢Задача {taskId} перенаправлена в {sub_divisions[parentId][divId].name}')
                trash_add(datetime.now(), old)
            except Exception as e:
                logging.error(str(e))
                await bot.send_message(id, '🔴Возникла проблема при перенаправлении задачи')

    elif 'show' == command[:4]:  # кнопка показать и скрыть у задачи
        taskId, val = map(int, command.split('=')[1:])
        if val == 1:  # показать кнопки для пересылки
            template = await make_main_redirect_buttons(taskId)
            await event.edit(buttons=template)
        elif val == 2:  # скрыть кнопки для пересылки
            await event.edit(buttons=[Button.inline('⬇️Развернуть', f'show={taskId}=1')])
        elif val == 3:  # удалить уведомление
            await event.delete()
            del current_tasks[taskId]

    elif 'div_redirect' == command[:12]:  # управление задачей у персонала определённого отделения
        if command.count('=') == 4:
            parentId, divId, taskId, mode = map(int, command.split('=')[1:])
            if mode == 0:  # закрытие задачи
                users[id].change_current_task(taskId)
                current_tasks[taskId].add_action(id, 1, parentId, divId)
                old = await event.edit('🛑Выберите типовой комментарий или введите вручную🛑')
                trash_add(datetime.now(), old)
            elif mode == 1:  # перенаправление задачи в другой отдел
                users[id].change_current_task(taskId)
                current_tasks[taskId].add_action(id, 2, parentId, divId)
                old = await event.edit('🛑Выберите типовой комментарий или введите вручную🛑')
                trash_add(datetime.now(), old)

    elif 'cal_redirect' == command[:12]:  # создание заявки на выезд
        if command.count('=') == 1:  # выбор города
            taskId = int(command.split('=')[-1])
            template = await make_division_redirect_buttons(taskId)
            await event.edit(buttons=template)
        elif command.count('=') == 2:  # выбор отделения с меткой "Календарь"
            parentId, taskId = map(int, command.split('=')[1:])
            template = await make_calendar_redirect_buttons(parentId, taskId)
            await event.edit(buttons=template)
        elif command.count('=') == 4:  # выбор дня и времени для отделения
            parentId, divId, taskId, delta = map(int, command.split('=')[1:])
            template = await make_div_calendar_buttons(parentId, divId, taskId, delta)
            await event.edit(buttons=template)

    elif 'job' == command[:3]:  # выбор типа работы для заявки на вызов для уже выбранной даты и времени
        if command.count('=') == 5:  # выбор типа работ
            parentId, divId, taskId, delta, time = map(int, command.split('=')[1:])
            template = await make_job_calendar_buttons(parentId, divId, taskId, delta, time)
            await event.edit(buttons=template)
        elif command.count('=') == 6:  # выбор конкретного ID задачи
            parentId, divId, taskId, delta, time, idx = map(int, command.split('=')[1:])
            template = await make_div_job_calendar_buttons(parentId, divId, taskId, delta, time, idx)
            await event.edit(buttons=template)
        elif command.count('=') == 7:  # создание задачи на выезд
            parentId, divId, taskId, delta, time, idx, typer = map(int, command.split('=')[1:])
            date = datetime.fromisoformat(f'{(datetime.now() + timedelta(days=delta)).date()} {str(time).zfill(2)}:00')
            currentId = task_create_new(typer, taskId, divId, date, users[id].jobId)

            task_change_state(taskId, 2)
            del current_tasks[taskId]

            if currentId != -1:
                txt = f'🟢Задание #[{currentId}](http://{link_url}.trytek.ru/oper/'\
                      f'?core_section=task&action=show&id={currentId}) успешно создано'
                old = await event.edit(txt, buttons=[
                    [Button.url('Работать с задачей (USERSIDE)↗️',
                                f'http://{link_url}.trytek.ru/oper/?core_section=task&action=show&id={currentId}')],
                    [Button.inline('Добавить конкретных исполнителей', f'employee={currentId}={divId}')]
                ])
                trash_add(datetime.now(), old)
                try:
                    prevDivId = get_executors(taskId)[0]
                    chatId = all_divisions[prevDivId].tgId
                    name = employee_data(users[id].jobId, short_name=True)['short_name']
                    txt = f'Задача #{taskId} выполнена!\nСоздана задача на выезд #{currentId}\n' \
                          f'Закрыл задачу: {name}\n\n' \
                          f'[🔗Ссылка на основное задание]' \
                          f'(http://{link_url}.trytek.ru/oper/?core_section=task&action=show&id={taskId})\n' \
                          f'[🔗Ссылка на задачу на выезд]' \
                          f'(http://{link_url}.trytek.ru/oper/?core_section=task&action=show&id={currentId})'
                    old = await bot.send_message(chatId, txt)
                    trash_add(datetime.now(), old)
                except Exception as e:
                    logging.error(str(e))
                    old = await bot.send_message(id, '🔴Уведомление не отправлено в общий чат')
                    trash_add(datetime.now(), old)
            else:
                txt = f'🔴Возникла проблема при создании задачи'
                old = await event.edit(txt)
                trash_add(datetime.now(), old)

    elif 'employee' == command[:8]:
        if command.count('=') == 2:
            taskId, divId = map(int, command.split('=')[1:])
            template = await make_employee_job_buttons(taskId, divId)
            await bot.send_message(id, 'Выберите сотрудников', buttons=template)
        elif command.count('=') == 3:
            taskId, divId, workers = command.split('=')[1:]
            taskId, divId = int(taskId), int(divId)
            template = await make_employee_job_buttons(taskId, divId, workers)
            await event.edit(buttons=template)
        elif command.count('=') == 4:
            taskId, divId, workers, mode = command.split('=')[1:]
            taskId, divId = int(taskId), int(divId)

            currentWorkers = {int(val) for val in workers.split(',') if val}

            tmp_count = 0
            for employeeId in currentWorkers:
                if employee_add(taskId, employeeId, users[id].jobId):
                    tmp_count += 1

            old = await event.edit(f'Добавлено {tmp_count} сотрудников в исполнители!')
            trash_add(datetime.now(), old)

    elif 'inventory' == command[:9]:  # кнопка 📦Отчеты по складу
        if command.count('=') == 0:  # выбор города для формирования отчёта
            template = await make_inventory_buttons()
            await event.edit(buttons=template)
        elif command.count('=') == 1:  # выбор подразделения с меткой "(список)"
            parentId = int(command.split('=')[-1])
            template = await make_div_inventory_buttons(parentId)
            await event.edit('Выберите подразделение', buttons=template)
        elif command.count('=') == 2:  # выбор типа отчёта
            parentId, divId = map(int, command.split('=')[1:])
            txt = 'Выберите необходимый отчёт'
            template = await make_choose_inventory_buttons(parentId, divId)
            await event.edit(txt, buttons=template)
        elif command.count('=') == 3:  # действие с отчётами
            parentId, divId, action = map(int, command.split('=')[1:])
            if action == 1:  # выбор периода времени для формирования отчёта с типом "1"
                txt = 'Введите дату начала и конца формирования отчёта через пробел\n'\
                      'Пример: «01.01.21 01.03.21»'
                report_waiters[id] = divId
                old = await event.edit(txt, buttons=Button.inline('❌Отмена', 'stop'))
                trash_add(datetime.now(), old)
            elif action == 2:  # создание отчёта с типом "2"
                await event.delete()
                make_amount_excel(divId)
                await bot.send_file(
                    id,
                    file=main_root + 'files/record2.xlsx',
                    caption=f'Файл от {datetime.now().date()}',
                )

    elif 'confirm' == command[:7]:  # подтверждение принятия задачи
        taskId, value = map(int, command.split('=')[1:])
        if value:
            name = employee_data(users[id].jobId, short_name=True)['short_name']
            txt = f'Задача {taskId} принята!\nФИО: {name}\n\n'\
                  f'[🔗Ссылка на задание](http://us-test.trytek.ru/oper/?core_section=task&action=show&id={taskId})\n'

            old = await event.edit(txt, buttons=Button.url('Продолжить работу с задачей↗️',
                                                           'https://t.me/trytek_usersideXVI_bot'))
            trash_add(datetime.now(), old)

            # staff_add(taskId, users[id].jobId)
            task_change_state(taskId, 3)
            comment_add(taskId, 'Взял в работу', users[id].jobId)
            telegramId, txt = task_make_txt(taskId)
            template = await make_division_redirect_buttons(taskId)
            await bot.send_message(id, txt, buttons=template)
        else:
            template = await make_accept_buttons(taskId)
            await event.edit(buttons=template)

    elif 'accept' == command[:6]:  # кнопки принять в чатах подразделений
        taskId = int(command.split('=')[-1])
        if taskId in current_tasks:
            template = await make_confirm_accept_buttons(taskId)
            await event.edit(buttons=template)
        else:
            tgId, txt = task_make_txt(taskId, last_comment=True)
            old = await event.edit(txt)
            trash_add(datetime.now(), old)

    elif 'stop' == command:
        login_updaters.discard(id)
        if id in report_waiters:
            del report_waiters[id]
        old = await event.edit('Действие отмено!')
        trash_add(datetime.now(), old)

    elif 'new_login' == command:  # обновление логина
        login_updaters.add(id)
        txt = 'Отправьте логин и пароль из USERSIDE через пробел\n'\
              'Пример: «login password»'
        old = await event.edit(txt, buttons=[
            Button.inline('❌Отмена', 'stop')
        ])
        trash_add(datetime.now(), old)
