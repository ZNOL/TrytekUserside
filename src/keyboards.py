from telethon.tl.types import *
from telethon.tl.custom import *
from src.users import *


async def make_main_redirect_buttons(taskId):
    """
    :param taskId: ID задания с USERSIDE
    :return: Кнопки выбора города при первом создании задачи на USERSIDE
    """
    redirect_buttons = []
    k = 0
    for id in main_divisions:
        division = main_divisions[id]
        if not k:
            redirect_buttons.append([Button.inline(division.name, f'redirect={division.id}={taskId}')])
        else:
            redirect_buttons[-1].append(Button.inline(division.name, f'redirect={division.id}={taskId}'))
        k = (k + 1) % 1
    redirect_buttons.append([Button.inline('Не требует пересылки', f'show={taskId}=3')])
    redirect_buttons.append([Button.inline('⬆️Свернуть', f'show={taskId}=2')])
    return redirect_buttons


async def make_sub_redirect_buttons(parentId, taskId):
    """
    :param parentId: ID подразделения города
    :param taskId: ID задания из USERSIDE
    :return: кнопки выбор подразделения в конкретном городе
    """
    redirect_buttons = []
    k = 0
    for id in sub_divisions[parentId]:
        division = sub_divisions[parentId][id]
        if not k:
            redirect_buttons.append([Button.inline(division.name, f'redirect={parentId}={division.id}={taskId}')])
        else:
            redirect_buttons[-1].append(Button.inline(division.name, f'redirect={parentId}={division.id}={taskId}'))
        k = (k + 1) % 1
    redirect_buttons.append([Button.inline('Назад🔼', f'redirect={taskId}')])
    return redirect_buttons


async def make_division_redirect_buttons(taskId):
    """
    :param taskId: ID задания из USERSIDE
    :return: кнопки взаимодействия с задачей у исполнителя из назначенного города: в другой отдел/на выезд/закрыть
    """
    executor = get_executors(taskId)
    parentId = all_divisions[executor[0]].parentId
    redirect_buttons = []
    k = 0
    for id in sub_divisions[parentId]:
        division = sub_divisions[parentId][id]
        template = Button.inline(division.name, f'div_redirect={parentId}={division.id}={taskId}=1')
        if not k:
            redirect_buttons.append([template])
        else:
            redirect_buttons[-1].append(template)
        k = (k + 1) % 1
    redirect_buttons.append([Button.inline('Заявка на выезд', f'cal_redirect={parentId}={taskId}')])
    redirect_buttons.append([Button.inline('Закрыть задачу❎', f'div_redirect={parentId}={executor[0]}={taskId}=0')])
    return redirect_buttons


async def make_calendar_redirect_buttons(parentId, taskId):
    """
    :param parentId: ID подразделения города
    :param taskId: ID задания из USERSIDE
    :return: кнопки с выбором отделений с пометкой "Календарь"
    """
    redirect_buttons = []
    k = 0
    for id in calendar_divisions[parentId]:
        division = calendar_divisions[parentId][id]
        if not k:
            redirect_buttons.append([Button.inline(division.name,
                                                   f'cal_redirect={parentId}={division.id}={taskId}=0')])
        else:
            redirect_buttons[-1].append(Button.inline(division.name,
                                                      f'cal_redirect={parentId}={division.id}={taskId}=0'))
        k = (k + 1) % 1
    redirect_buttons.append([Button.inline('Назад🔼', f'cal_redirect={taskId}')])
    return redirect_buttons


async def make_div_calendar_buttons(parentId, divId, taskId, delta):
    """
    :param parentId: ID подразделения города
    :param divId: ID подразделения с пометкой "Календарь"
    :param taskId: ID задания из USERSIDE
    :param delta: разница в днях с текущим числом. Целое число
    :return: кнопки для выбора свободных часов для формирования заявки на выезд
    """
    redirect_buttons = []
    k = 0
    result = task_make_calendar((datetime.now() + timedelta(days=delta)).date(), divId)
    for idx in range(10):
        if result[idx]:
            if not k:
                redirect_buttons.append(
                    [Button.inline(f'{idx + 9}:00', f'job={parentId}={divId}={taskId}={delta}={idx + 9}')]
                )
            else:
                redirect_buttons[-1].append(
                    Button.inline(f'{idx + 9}:00', f'job={parentId}={divId}={taskId}={delta}={idx + 9}')
                )
            k = (k + 1) % 3

    redirect_buttons.append([
        Button.inline(f'◀️{(datetime.now() + timedelta(days=delta - 1)).date()}',
                      f'cal_redirect={parentId}={divId}={taskId}={delta - 1}'),
        Button.inline(f'⏺{(datetime.now() + timedelta(days=delta)).date()}',
                      f'cal_redirect={parentId}={divId}={taskId}={delta}'),
        Button.inline(f'{(datetime.now() + timedelta(days=delta + 1)).date()}▶️',
                      f'cal_redirect={parentId}={divId}={taskId}={delta + 1}'),
    ])
    redirect_buttons.append([Button.inline('Назад🔼', f'cal_redirect={parentId}={taskId}')])
    return redirect_buttons


async def make_job_calendar_buttons(parentId, divId, taskId, delta, time):
    """
    :param parentId: ID подразделения города
    :param divId: ID подразделения с пометкой "Календарь"
    :param taskId: ID задания из USERSIDE
    :param delta: разница в днях с текущим числом. Целое число
    :param time: час назначения работ от 9 до 18
    :return: кнопки выбора типа задания для формирования заявки на выезд
    """
    return [
        [
            Button.inline('Услуги ФЛ', f'job={parentId}={divId}={taskId}={delta}={time}=0'),
            Button.inline('Услуги ЮЛ', f'job={parentId}={divId}={taskId}={delta}={time}=1')
        ],
        [
            Button.inline('Ремонты ФЛ', f'job={parentId}={divId}={taskId}={delta}={time}=2'),
            Button.inline('Ремонты ЮЛ', f'job={parentId}={divId}={taskId}={delta}={time}=3'),
        ],
        [
            Button.inline('Назад🔼', f'cal_redirect={parentId}={divId}={taskId}={delta}')
        ],
    ]


async def make_div_job_calendar_buttons(parentId, divId, taskId, delta, time, idx):
    """
    :param parentId: ID подразделения города
    :param divId: ID подразделения с пометкой "Календарь"
    :param taskId: ID задания из USERSIDE
    :param delta: разница в днях с текущим числом. Целое число
    :param time: час назначения работ от 9 до 18
    :param idx: ID типов работ
    :return: кнопки для выбора работы отпределённого типа для формирования заявки на выезд
    """
    buttons = []
    if idx == 0:
        buttons = [
            [
                Button.inline('ИНЕТ-фл-FTTB (медь)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=294'),
                Button.inline('КТВ-ПОДКЛЮЧЕНИЕ',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=295'),
            ],
            [
                Button.inline('ИНЕТ-фл-FTTB (медь)+КТВ',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=296'),
                Button.inline('ИНЕТ-ФЛ-ЧС (opt)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=85'),
            ],
            [
                Button.inline('ИНЕТ-фл-FTTH(opt)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=193'),
                Button.inline('ИНЕТ-фл-FTTH(opt)+КТВ(rf)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=321'),
            ],
        ]
    elif idx == 1:
        buttons = [
            [
                Button.inline('Облачное видеонаблюдение (ЮЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=323'),
                Button.inline('ТЕХВОЗМОЖНОСТЬ-Облачное видеонаблюдение (ЮЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=311'),
            ],
            [
                Button.inline('ТЕХВОЗМОЖНОСТЬ-ИНЕТ-юл',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=334'),
                Button.inline('ИНЕТ-юл-FTTB (медь)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=335'),
            ],
            [
                Button.inline('ИНЕТ-юл-FTTH (opt)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=336'),
            ]
        ]
    elif idx == 2:
        buttons = [
            [
                Button.inline('РЕМОНТ-КТВ (ФЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=309'),
                Button.inline('РЕМОНТ-МЕДЬ (ФЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=300'),
            ],
            [
                Button.inline('РЕМОНТ-ОПТИКА (ФЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=301'),
                Button.inline('РЕМОНТ-ТЕХНИК (ФЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=299'),
            ],
            [
                Button.inline('Ремонт-облачное видеонаблюдение (ФЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=293'),
            ],
        ]
    elif idx == 3:
        buttons = [
            [
                Button.inline('РЕМОНТ-МЕДЬ (ЮЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=302'),
                Button.inline('Ремонт-облачное видеонаблюдение (ЮЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=324'),
            ],
            [
                Button.inline('РЕМОНТ-ОПТИКА (ЮЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=304'),
                Button.inline('РЕМОНТ-ТЕХНИК (ЮЛ)',
                              f'job={parentId}={divId}={taskId}={delta}={time}={idx}=303'),
            ],
        ]

    buttons.append([
        Button.inline('Назад🔼', f'job={parentId}={divId}={taskId}={delta}={time}')
    ])
    return buttons


async def make_employee_job_buttons(taskId, divId, workers=''):
    buttons = []
    currentWorkers = {int(val) for val in workers.split(',') if val}
    workers = get_division(divId, workers=True)['workers']

    k = 0
    for employeeId in workers:
        name = employee_data(employeeId, short_name=True)['short_name']
        if employeeId in currentWorkers:
            tmp_set = {val for val in currentWorkers}
            tmp_set.discard(employeeId)
            name = '✅' + name
        else:
            tmp_set = {val for val in currentWorkers}
            tmp_set.add(employeeId)
        template = Button.inline(name, f'employee={taskId}={divId}={",".join(str(val) for val in tmp_set)}')

        if not k:
            buttons.append([template])
        else:
            buttons[-1].append(template)
        k = (k + 1) % 2
    buttons += [
        [
            Button.inline(f'🟢Подтвердить',
                          f'employee={taskId}={divId}={",".join(str(val) for val in currentWorkers)}=1'),
            Button.inline('🔴Отмена', 'stop'),
        ],
    ]
    return buttons


async def make_inventory_buttons():
    """
    :return: Выбор подразделение города для оформирования отчёта по складу
    """
    redirect_buttons = []
    k = 0
    for id in main_divisions:
        division = main_divisions[id]
        if not k:
            redirect_buttons.append([Button.inline(division.name, f'inventory={id}')])
        else:
            redirect_buttons[-1].append(Button.inline(division.name, f'inventory={id}'))
        k = (k + 1) % 1
    redirect_buttons.append([Button.inline('❌Отмена', 'stop')])
    return redirect_buttons


async def make_div_inventory_buttons(parentId):
    """
    :param parentId: ID подразделения города
    :return: кнопки выбора подразделения с пометкой "(список)"
    """
    redirect_buttons = []
    k = 0
    if parentId in inventory_divisions:
        for id in inventory_divisions[parentId]:
            division = inventory_divisions[parentId][id]
            if not k:
                redirect_buttons.append([Button.inline(division.name, f'inventory={parentId}={id}')])
            else:
                redirect_buttons[-1].append(Button.inline(division.name, f'inventory={parentId}={id}'))
            k = (k + 1) % 1
    redirect_buttons.append([Button.inline('Назад⏏️', 'inventory')])
    return redirect_buttons


async def make_choose_inventory_buttons(parentId, divId):
    """
    :param parentId: ID подразделения города
    :param divId: ID подразделения с пометкой "(список)"
    :return: кнопки выбора типа отчёта.
    """
    buttons = [
        [Button.inline('📦Отчет по расходу ТМЦ', f'inventory={parentId}={divId}=1')],
        [Button.inline('📦Отчет по остатку ТМЦ', f'inventory={parentId}={divId}=2')],
        [Button.inline('Назад⏏️', f'inventory={parentId}')],
    ]
    return buttons


async def make_accept_buttons(taskId):
    return Button.inline('Приступить к выполнению↗️', f'accept={taskId}')


async def make_confirm_accept_buttons(taskId):
    return [Button.inline('✅', f'confirm={taskId}=1'),
            Button.inline('❌', f'confirm={taskId}=0')]


async def make_show_buttons(taskId):
    return [
        Button.inline('Переслать', f'show={taskId}=1'),
        Button.inline('Удалить оповещение', f'show={taskId}=3')
    ]


async def make_comments_keyboard(start_idx):
    """
    изменить параметр `size` для изменения количество комментариев на 1ой странице
    :param start_idx: кнопка первого комментария
    :return: клавиатура типовых комментарием
    """
    start_idx = start_idx if start_idx >= 0 else 0
    size = 5
    last_idx = start_idx + size if start_idx + size <= len(comments) else len(comments)

    keyboard = []
    k = 0
    for idx in range(start_idx, last_idx):
        if not k:
            keyboard.append([Button.text(comments[idx], resize=True)])
        else:
            keyboard[-1].append(Button.text(comments[idx], resize=True))
        k = (k + 1) % 2

    if start_idx == 0:
        keyboard.append([Button.text(f'➡️', resize=True)])
    elif start_idx != 0 and last_idx < len(comments):
        keyboard.append([Button.text(f'⬅️', resize=True),
                         Button.text(f'➡️', resize=True)])
    else:
        keyboard.append([Button.text(f'⬅️', resize=True)])
    keyboard.append([Button.text('⏏️Выйти', resize=True)])
    return keyboard


main_keyboard = [
    [Button.text('🗿Авторизация', resize=True), Button.text('🔖Типовые комментарии', resize=True)],
]

storekeeper_keyboard = [
    [
        Button.text('📦Отчеты по складу', resize=True)
    ]
]
