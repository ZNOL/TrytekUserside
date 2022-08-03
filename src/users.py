from src.excel import *


class USER:
    def __init__(self, id, login='Отсутствует', jobId='', startIdx=0, comments_message=None, new=False):
        self.id = int(id)
        self.login = login
        self.jobId = int(jobId) if jobId != '' else ''
        self.startIdx = startIdx
        self.comments_message = comments_message
        if new:
            users_add(self.id)

    def update_login(self, new_login):
        self.login = new_login
        self.jobId = get_id_by_login(self.login)
        users_update(self.id, 'login', self.login)
        users_update(self.id, 'job_id', self.jobId)

    def change_current_task(self, taskId):
        users_update(self.id, 'current_task', taskId)

    def get_current_task(self):
        return users_get_current(self.id)

    def change_startIdx(self, add_val):
        self.startIdx += add_val

    def change_comments_message(self, new_val):
        self.comments_message = new_val


login_updaters = set()
report_waiters = dict()
users = dict()


for user in users_get_all():
    users[user['user_id']] = USER(user['user_id'], user['login'], user['job_id'])
