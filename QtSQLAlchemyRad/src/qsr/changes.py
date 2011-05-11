# -*- coding: utf-8 -*-

from model import orm
class _Singleton(object):
    def __init__(self):
        self.instance = "Instance at %d" % self.__hash__()
        self.actions = []
        
    def addDeleteAction(self, deleted):
        action = Action(deleted)
        self.actions.append(action)
            
    def restore(self, action):
        for item in action.items:
            orm().add(item)
        orm().commit()
        print self._deleteAction(action)
        
    def _deleteAction(self, action):
        for i in range(len(self.actions)):
            if self.actions[i] == action:
                del self.actions[i]
                return True
        return False          
    
    def __iter__(self):
        for action in self.actions: yield action

class Action():
    def __init__(self, items):
        self.items = items
        self.table = items[0].__class__.__tabletitle__
        
    def __repr__(self):
        return u'Удаление из таблицы "%s" %d элемента(ов)' % (self.table, len(self.items))
    
    def restore(self):
        return changes().restore(self)
    

_singleton = _Singleton()
def changes(): return _singleton
