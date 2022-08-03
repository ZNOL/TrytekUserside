class DIVISION:
    def __init__(self, id, name, tgId, parentId):
        self.id = int(id)
        self.name = name
        self.tgId = int(tgId) if tgId.isdigit() else ''
        self.parentId = int(parentId)


all_divisions = dict()
main_divisions = dict()
sub_divisions = dict()
calendar_divisions = dict()
inventory_divisions = dict()

comments = []
