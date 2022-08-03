import xlsxwriter
from src.userside import *


def make_operation_excel(divId, data_start, data_finish):
    """
    Формирует отчёт по операциям с ТМЦ персонала из подразделения с divId
    :param divId: ID подразделения из отдела Персонал/Подразделения
    :param data_start: Дата, с которой идёт формирование отчёта
    :param data_finish: Дата, по которую идёт формирование отчёта
    :return: возвращает 0 при правильной обработке
    """
    data = inventory_get_operation(data_start, data_finish)
    workers = {*get_division(divId, workers=True)['workers']}
    separator = '----------------------------------------------------------------------------------------------------'\
                '----------------------------------------------------------------------------------------------------'\
                '-------'
    workbook = xlsxwriter.Workbook(main_root + 'files/record.xlsx')
    table_header = ['ID', 'Дата', 'Куда', 'Категория', 'Наименование', 'Кол-во']

    for employeeId in workers:
        worksheet = workbook.add_worksheet(employee_data(employeeId, short_name=True)['short_name'])
        worksheet.set_column(0, 0, 10)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 35)
        worksheet.set_column(4, 4, 45)
        worksheet.set_column(5, 5, 10)

        row = 0
        for idx, item in enumerate(table_header):
            worksheet.write(row, idx, item)

        row = 1
        for id in data:
            val = data[id]
            if int(val['account_src']) % 10000000 != employeeId:
                continue

            if int(val['account_dst']) // 10000000 == 21203:
                destination = f'Заявка {int(val["account_dst"]) % 10000000}'
            elif int(val['account_dst']) // 10000000 == 20403:
                destination = f'Возвращено на склад'
            elif int(val['account_dst']) // 1000000000 == 900:
                destination = 'Списано'
            else:
                destination = str(val['account_dst'])

            column = 0
            items = [val['id'], val['date'], destination]
            for item in items:
                worksheet.write(row, column, item)
                column += 1
            for inventoryId in val['inventory_ids']:
                info = inventory_get_info(inventoryId)
                column = 3
                items = [info['section_name'], info['name'], f'{info["amount"]} {info["measure"]}']
                for idx, item in enumerate(items):
                    worksheet.write(row, column + idx, item)
                row += 1
            worksheet.write(row, 0, separator)
            row += 1
    workbook.close()
    return 0


def make_amount_excel(divId):
    """
    Формирует отчёт по ТМЦ у сотрудников подразделения divId на данны момент
    :param divId: ID подразделения из отдела Персонал/Подразделения
    :return: возвращает 0 при правильной обработке
    """
    workers = {*get_division(divId, workers=True)['workers']}

    table_header = ['Категория', 'Наименование', 'Кол-во']

    workbook = xlsxwriter.Workbook(main_root + 'files/record2.xlsx')
    for employeeId in workers:
        worksheet = workbook.add_worksheet(employee_data(employeeId, short_name=True)['short_name'])
        worksheet.set_column(0, 0, 35)
        worksheet.set_column(1, 1, 45)
        worksheet.set_column(2, 2, 10)

        data = inventory_get_amount(employeeId)

        row = 0
        for idx, item in enumerate(table_header):
            worksheet.write(row, idx, item)
        row += 1

        for id in data:
            val = data[id]
            info = inventory_get_info(val['id'])
            items = [info['section_name'], info['name'], f'{info["amount"]} {info["measure"]}']

            for idx, item in enumerate(items):
                worksheet.write(row, idx, item)

            row += 1
    workbook.close()
    return 0
