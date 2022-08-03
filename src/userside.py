import asyncio
import requests
from src.tasks import *
from src.divisions import *


def get_id_by_login(login):
    """
    :param login: логин пользователя из USERSIDE
    :return: employee_id
    """
    request = api_url + f'&cat=employee&action=get_employee_id&data_typer=login&data_value={login}'
    result = requests.post(request)
    return result.json()['id']


def check_password(login, password):
    """
    :param login: логин из USERSIDE
    :param password: пароль из USERSIDE
    :return: bool True/False
    """
    request = api_url + f'&cat=employee&action=check_pass&login={login}&pass={password}'
    result = requests.post(request)
    try:
        return result.json()['Result'] == 'OK'
    except Exception as e:
        logging.error(str(e))
        logging.error(str(result))
        return False


def employee_data(employeeId, name=False, short_name=False, telegramId=False):
    """
    :param employeeId: ID пользователя из USERSIDE
    :param name: True, если нужно вернуть имя
    :param short_name: True, если нужно вернуть короткую форму имени
    :param telegramId: True, если нужен Telegram ID
    :return: словарь с ключами "name"/"short_name"/"telegramId"
    """
    request = api_url + f'&cat=employee&action=get_data&id={employeeId}'
    result = requests.post(request)

    answer = dict()
    try:
        data = result.json()['data'][str(employeeId)]
        if name:
            answer['name'] = data['name']
        if short_name:
            answer['short_name'] = data['short_name']
        if telegramId:
            if 'additional_data' in data and data['additional_data']['33'].isdigit():
                answer['telegramId'] = int(data['additional_data']['33'])
            else:
                answer['telegramId'] = ''
    except Exception as e:
        if name:
            answer['name'] = employeeId
        if short_name:
            answer['short_name'] = employeeId
        if telegramId:
            answer['telegramId'] = ''
    return answer


def get_executors(taskId):
    """
    :param taskId: ID задания из USERSIDE
    :return: массив с ID подразделений, выполняющих задание
    """
    data = show_task(taskId)
    if data['Result'] == 'OK':
        info = data['Data']
        if 'staff' in info and 'division' in info['staff']:
            return [int(id) for id in info['staff']['division']]
    return []


def get_division(divId, name=False, workers=False):
    """
    :param divId: ID подразделения
    :param name: True, если нужно вернуть имя
    :param workers: True, если нужно вернуть массив operator_id из USERSIDE
    :return: словарь с ключами "name"/"workers"
    """
    request = api_url + f'&cat=employee&action=get_division&id={divId}'
    result = requests.post(request)
    answer = {}
    try:
        data = result.json()
        if name:
            answer['name'] = data['data'][str(divId)]['name']
        if workers:
            answer['workers'] = [int(val['employee_id']) for val in data['data'][str(divId)]['staff']['work']]
    except Exception as e:
        logging.error(str(e))
        if name:
            answer['name'] = ''
        if workers:
            answer['workers'] = []
    return answer


def task_make_txt(taskId, last_comment=None):
    """
    :param taskId: ID задачи из USERSIDE
    :param last_comment: ID последнего комментария, если его нужно добавить
    :return: string с данными по заданию
    todo 3.16 проблема с комментариями
    """
    data = show_task(taskId)
    if data['Result'] == 'OK':
        info = data['Data']

        employee = employee_data(info['author_employee_id'], name=True, telegramId=True)
        authorName, telegramId = employee['name'], employee['telegramId']
        updateTime = info['date']['update'][:-3]

        txt = f"👁‍🗨USERSIDE\n\n"\
              f"**Тип задания**: {info['type']['name']}\n"\
              f"**Автор задания**: {authorName}\n"\
              f"**Статус**: #{info['state']['name'].replace(' ', '_')}\n\n"\
              f"**Время создания**: {info['date']['create']}\n"\
              f"**Дата работ**: {info['date']['todo']}\n\n"\
              f"**No**: {info['id']}\n"

        if 'staff' in info and 'division' in info['staff']:
            txt += '\n**Исполнители:**\n'
            for id in info['staff']['division']:
                txt += f'◦{all_divisions[int(id)].name}\n'
            txt += '\n'
        if 'address' in info and info['address']['text'] != '':
            txt += f"**Адресс**: {info['address']['text']}\n"
        if 'description' in info and info['description'] != '':
            txt += f'**Описание**: {info["description"]}\n'
        if 'additional_data' in info and len(info['additional_data']) > 0:
            txt += '\n🔘**Дополнительная информация:**\n'
            for id in info['additional_data']:
                val = info['additional_data'][id]
                txt += f'•{val["caption"]}: {val["value"]}\n'
        if last_comment is not None and 'comments' in info:
            # print(last_comment)
            # print(info['comments'])
            for id in info['comments']:
                val = info['comments'][id]
                if val['dateAdd'][:-3] == updateTime:
                    txt += f'\n📝Комментарий: {val["comment"]}\n'
                    commentator = employee_data(val['employee_id'], name=True)['name']
                    txt += f'Автор: {commentator}\n\n'
        txt += f'\n[🔗Ссылка на задание](http://us-test.trytek.ru/oper/?core_section=task&action=show&id={taskId})'

        return telegramId, txt


def task_get_comment(taskId, commentId):
    """
    :param taskId: ID задания из USERSIDE
    :param commentId: ID комментария из задания
    :return: str() комментарий к заданию
    """
    data = show_task(taskId)
    if data['Result'] == 'OK':
        info = data['Data']
        if 'comments' in info:
            comment = info['comments'][str(commentId)]['comment']
            return comment
    return ''


def task_get_state(taskId):
    """
    :param taskId: ID задания из USERSIDE
    :return: ID состояния задания из USERSIDE
    """
    data = show_task(taskId)
    if data['Result'] == 'OK':
        info = data['Data']
        return info['state']['id']
    return 0


def task_edit(taskId, newTypeId=0):
    if newTypeId:
        request = api_url + f'&cat=task&action=edit&id={taskId}&type_id={newTypeId}'
        result = requests.post(request)
        try:
            return result.json()['Result'] == 'OK'
        except Exception as e:
            logging.error(str(e))
            return False
    else:
        return True


def task_change_type(taskId):
    """
    Изменяет тип задачи, если его ID находится в словаре config_change_type (разположен в config.py)
    :param taskId: ID задания из USERSIDE
    :return: (bool) True, если тип успешно изменён, False иначе
    """
    data = show_task(taskId)
    if data['Result'] == 'OK':
        info = data['Data']
        try:
            prevTypeId = int(info['type']['id'])
            if prevTypeId in config_change_type:
                nextTypeId = config_change_type[prevTypeId]
                return task_edit(taskId, newTypeId=nextTypeId)
            else:
                return True
        except Exception as e:
            logging.error(str(e))
            return False
    else:
        return False


def task_change_state(taskId, stateId):
    """
    Изменение состояния задания в USERSIDE
    :param taskId: ID задания из USERSIDE
    :param stateId: ID состояния задачи в USERSIDE
    """
    request = api_url + f'&cat=task&action=change_state&id={taskId}&state_id={stateId}'
    result = requests.post(request)
    try:
        return result.json()['Result'] == 'OK'
    except Exception as e:
        logging.error(str(e))
        logging.error(str(result))
        return False


def show_task(taskId):
    """
    Получение данных о задаче
    :param taskId: ID задачи из USERSIDE
    """
    request = api_url + f'&cat=task&action=show&id={taskId}'
    result = requests.post(request)
    return result.json()


def task_get_catalog_type(typeId):
    """
    Получение данных о типе задач
    :param typeId: тип задач из USERSIDE
    :return:
    todo
    """
    request = api_url + f'&cat=task&action=get_catalog_type&id={typeId}'
    result = requests.post(request)
    print(result)
    print(result.json())


def task_make_calendar(date, divId):
    """
    :param date: datetime() дата
    :param divId: ID выбранного подразделения
    :return: массив с пустым временем для задачи. 0 индекс = 9 часов, 1 индекс = 10 часов . . .
    """
    data = get_all_tasks(division_id_with_staff=divId, date_do_from=date)
    result = [1 for i in range(10)]
    if data['Result'] == 'OK':
        if data['count'] > 0:
            for taskId in map(int, data['list'].split(',')):
                task_data = show_task(taskId)
                if task_data['Result'] == 'OK':
                    task_data = task_data['Data']

                    try:
                        hour_duration = int(task_data['date']['runtime_individual_hour'])
                        if hour_duration < 1:
                            raise ValueError
                    except Exception as e:
                        logging.error(str(e))
                        hour_duration = 1

                    date = datetime.fromisoformat(task_data['date']['todo']).hour
                    idx = date - 9
                    while 0 <= idx <= 9 and hour_duration > 0:
                        result[idx] = 0
                        hour_duration -= 1
                        idx += 1

    return result


def task_create_new(task_type, parent_task, divId, date, employeeId):
    """
    Создание нового задания USERSIDE
    :param task_type: тип задания
    :param parent_task: родительское задания
    :param divId: ID подразделения, на которое назначается задание
    :param date: дата, на которое назначается задание
    :param employeeId: ID создателя задания из USERSIDE
    """
    request = api_url + f'&cat=task&action=add&work_typer={task_type}&work_datedo={date}'\
                        f'&parent_task_id={parent_task}&division_id={divId}&author_employee_id={employeeId}'

    data = show_task(parent_task)
    if data['Result'] == 'OK':
        info = data['Data']
        if 'address' in info and 'addressId' in info['address']:
            request += f'&address_id={info["address"]["addressId"]}'
        if 'customer' in info and 'id' in info['customer']:
            request += f'&usercode={info["customer"]["id"]}'
        if 'additional_data' in info:
            for id in info['additional_data']:
                val = info['additional_data'][id]
                request += f'&dopf_{val["id"]}={val["value"]}'

    result = requests.post(request)
    try:
        return int(result.json()['Id'])
    except Exception as e:
        logging.error(str(e))
        return -1


def get_all_tasks(date_change_from=None, division_id_with_staff=None, date_do_from=None):
    """
    :param date_change_from: дата последнего обновления задачи
    :param division_id_with_staff: задачи подразделения
    :param date_do_from: datetime() число на которе назначено выполнение
    :return: ID всех задач
    """
    request = api_url + '&cat=task&action=get_list'
    if date_change_from is not None:
        request += f'&date_change_from={date_change_from}'
    if division_id_with_staff is not None:
        request += f'&division_id_with_staff={division_id_with_staff}'
    if date_do_from is not None:
        request += f'&date_do_from={date_do_from}' + f'&date_do_to={date_do_from + timedelta(days=1)}'

    result = requests.post(request)

    return result.json()


def get_division_list():
    """
    :return: данные по всем подразделениям из USERSIDE
    """
    request = api_url + '&cat=employee&action=get_division_list'
    result = requests.post(request)
    return result.json()


def update_divisions():
    """
    Обновление данных по подразделения из USERSIDE
    """
    data = get_division_list()
    if data['Result'] == 'OK':
        info = data['data']
        for id in info:  # получение всех отделов
            val = info[id]
            name = val['name']
            tgId = val['comment']
            parentId = val['parent_id']
            all_divisions[int(id)] = DIVISION(id, name, tgId, parentId)
        for id in info:  # получие основных отделов
            val = info[id]
            name = val['name']
            if 'Календарь' not in name and 'ОП' in name:
                tgId = val['comment']
                parentId = val['parent_id']
                if parentId == 0:
                    main_divisions[int(id)] = DIVISION(id, name, tgId, parentId)
        for id in info:  # получение подразделов
            val = info[id]
            name = val['name']
            if 'Календарь' not in name:
                tgId = val['comment']
                parentId = val['parent_id']
                if parentId in main_divisions:
                    try:
                        sub_divisions[int(parentId)][int(id)] = DIVISION(int(id), name, tgId, parentId)
                    except KeyError:
                        sub_divisions[int(parentId)] = dict()
                        sub_divisions[int(parentId)][int(id)] = DIVISION(int(id), name, tgId, parentId)
        for id in info:  # получение календарей
            val = info[id]
            name = val['name']
            if 'Календарь' in name:
                tgId = val['comment']
                parentId = val['parent_id']
                for i in range(3):
                    if parentId not in main_divisions and parentId in all_divisions:
                        parentId = all_divisions[parentId].parentId
                if parentId in main_divisions:
                    try:
                        calendar_divisions[parentId][int(id)] = DIVISION(int(id), name, tgId, parentId)
                    except KeyError:
                        calendar_divisions[parentId] = dict()
                        calendar_divisions[parentId][int(id)] = DIVISION(int(id), name, tgId, parentId)
        for id in info:  # получение подразделения для склада
            val = info[id]
            name = val['name']
            if '(список)' in name:
                tgId = val['comment']
                parentId = val['parent_id']
                for i in range(3):
                    if parentId not in main_divisions and parentId in all_divisions:
                        parentId = all_divisions[parentId].parentId
                if parentId in main_divisions:
                    try:
                        inventory_divisions[parentId][int(id)] = DIVISION(int(id), name, tgId, parentId)
                    except KeyError:
                        inventory_divisions[parentId] = dict()
                        inventory_divisions[parentId][int(id)] = DIVISION(int(id), name, tgId, parentId)


def get_typical_comments():
    """
    Обновление типовых комментариев, записанных в USERSIDE
    """
    request = api_url + '&cat=task&action=get_typical_comments'
    result = requests.post(request)
    data = result.json()
    if data['Result'] == 'OK':
        data = data['data']
        for id in sorted(data.keys()):
            comments.append(data[id]['text'])


def comment_add(taskId, comment, employeeId):
    """
    Добавление комментария
    :param taskId: ID задания
    :param comment: комментарий
    :param employeeId: operator_id сотрудника, добавившего комментарий
    :return:
    """
    request = api_url + f'&cat=task&action=comment_add&id={taskId}&comment={comment}&employee_id={employeeId}'
    result = requests.post(request)
    try:
        return int(result.json()['Id'])
    except Exception as e:
        logging.error(str(e))
        logging.error(result)
        return 0


def employee_add(taskId, employeeId, authorId):
    """
    Добавляет сотрудника в исполнители
    :param taskId: ID задания из USERSIDE
    :param employeeId: ID сотрудника из подразделения
    :param authorId: employee_id инициатор добавления
    """
    request = api_url + f'&cat=task&action=employee_add&id={taskId}'\
                        f'&employee_id={employeeId}'\
                        f'&author_employee_id={authorId}'
    result = requests.post(request)
    try:
        return result.json()['Result'] == 'OK'
    except Exception as e:
        logging.error(str(e))
        return False


def watcher_add(taskId, employeeId):
    """
    Добавление наблюдателя к задаче
    :param taskId: ID задания из USERSIDE
    :param employeeId: employee_id инициатор добавления
    todo
    """
    request = api_url + f'&cat=task&action=watcher_add&id={taskId}&employee_id={employeeId}'\
                        f'&author_employee_id={employeeId}'
    result = requests.post(request)
    try:
        return result.json()['Result'] == 'OK'
    except Exception as e:
        logging.error(str(e))
        logging.error(str(result))
        return False


def division_add(taskId, divId, employeeId):
    """
    Добавление подразделения в исполнители задачи
    :param taskId: ID задачи из USERSIDE
    :param divId: ID подразделения
    :param employeeId: инициатор (operator_id) добавления
    """
    request = api_url + f'&cat=task&action=division_add&id={taskId}'\
                        f'&division_id={divId}&employee_id={employeeId}'
    result = requests.post(request)
    try:
        return result.json()['Result'] == 'OK'
    except Exception:
        return False


def division_delete(taskId, divId, employeeId):
    """
    Удаление подразделения из исполнителей задачи
    :param taskId: ID задачи из USERSIDE
    :param divId: ID подразделения
    :param employeeId: инициатор добавления (ID сотрудника)
    """
    request = api_url + f'&cat=task&action=division_delete&id={taskId}' \
                        f'&division_id={divId}&employee_id={employeeId}'
    result = requests.post(request)
    try:
        return result.json()['Result'] == 'OK'
    except Exception:
        return False


def inventory_get_info(inventoryId):
    """
    Получение информации о ТМЦ
    :param inventoryId: ID ТМЦ из USERSIDE
    :return:
    """
    request = api_url + f'&cat=inventory&action=get_inventory&id={inventoryId}'
    result = requests.post(request)
    answer = {}
    try:
        data = result.json()['data']
        answer['section_name'] = data['section_name']
        answer['name'] = data['name']
        answer['amount'] = data['amount']
        answer['measure'] = data['measure']
    except Exception as e:
        logging.error(str(e))
        answer['section_name'] = ''
        answer['name'] = ''
        answer['amount'] = ''
        answer['measure'] = ''
    return answer


def inventory_get_amount(employeeId):
    """
    :param employeeId: ID сотрудника из USERSIDE
    :return: возвращает ТМЦ сотрудника
    """
    request = api_url + f'&cat=inventory&action=get_inventory_amount&location=employee&object_id={employeeId}'
    result = requests.post(request)
    try:
        return result.json()['data']
    except Exception as e:
        logging.error(str(e))
        return {}


def inventory_get_operation(date_start, date_finish):
    """
    Получение всех операций над ТМЦ
    :param date_start: время начала
    :param date_finish: время конца
    """
    request = api_url + f'&cat=inventory&action=get_operation'
    request += f'&date_start={date_start}&date_finish={date_finish}'
    result = requests.post(request)
    try:
        data = result.json()
        if data['Result'] == 'OK':
            data = data['Data']
            return data
        else:
            raise Exception
    except Exception as e:
        logging.error(str(e))
        return {}


update_divisions()
get_typical_comments()
