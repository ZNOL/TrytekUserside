from src.database import *


class TASK:
    def __init__(self, id, new=False):
        self.id = id
        if new:
            task_add(id)

    def __del__(self):
        task_delete(self.id)

    def add_action(self, telegramId, action_id, parentId=0, divId=0):
        task_update(self.id, 'telegram_id', telegramId)
        task_update(self.id, 'action_id', action_id)
        task_update(self.id, 'parent_id', parentId)
        task_update(self.id, 'div_id', divId)

    def get_action(self):
        tmp = task_get_action(self.id)
        return [tmp['action_id'], tmp['parent_id'], tmp['div_id']]


current_tasks = dict()

for task in task_get_all():
    current_tasks[task['task_id']] = TASK(task['task_id'])
