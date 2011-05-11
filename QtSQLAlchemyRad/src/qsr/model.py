# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.schema import Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, sessionmaker, MapperExtension, class_mapper, EXT_CONTINUE
import ConfigParser
import datetime
import pickle
from sqlalchemy import desc
import sqlalchemy.exc

isEchoModeEnabled = False


'''Соединяемся с БД'''
if __name__ != '__main__':
    config = ConfigParser.RawConfigParser()
    config.read('conf/settings.cfg')
    
    type = config.get('db', 'type')
    host = config.get('db', 'host')
    uid = config.get('db', 'uid')
    pwd = config.get('db', 'pwd')
    database = config.get('db', 'database')    
    if type == 'mssql':
        engine = create_engine('mssql://%s:%s@%s/%s' % (uid, pwd, host, database), echo=isEchoModeEnabled, pool_recycle = 1800)
    elif type == 'sqlite':
        engine = create_engine('sqlite:///%s' % (database), echo=isEchoModeEnabled, pool_recycle = 1800)
    elif type == 'mysql':
        engine = create_engine('mysql:///%s?charset=utf8&user=%s&passwd=%s&host=%s' % (database, uid, pwd, host), echo=isEchoModeEnabled, pool_recycle = 1800)



class HistoryLogger(MapperExtension):
    def populate_instance(self, mapper, selectcontext, row, instance, **flags):
        return EXT_CONTINUE
    
    def before_insert(self, mapper, connection, instance):
        #action = Changehistory('INSERT')    
        #orm().add(self.__createAction(action, instance))
        return EXT_CONTINUE        
    
    def before_update(self, mapper, connection, instance):
        #action = Changehistory('UPDATE')    
        #orm().add(self.__createAction(action, instance))
        return EXT_CONTINUE
    
    def before_delete(self, mapper, connection, instance):
        #action = Changehistory('DELETE')
        #orm().add(self.__createAction(action, instance))
        return EXT_CONTINUE
    
    def __createAction(self, action, instance):
        action.tablename = instance.getTableTitle()
        now = datetime.datetime.now()        
        action.date = now.date()
        action.time = now.time()
        action.title = unicode(instance)
        action.serialized = pickle.dumps(instance)
        return action
Base = declarative_base()

class Titled():
    def getTableTitle(self):
        if hasattr(self, '__tabletitle__'):
            return self.__tabletitle__
        return self.__tablename__

'''Заворачиваем все это singleton для возможности работать с единственной сессией sqlalchemy'''
class _Singleton(object):
    def __init__(self):        
        Session = sessionmaker(bind=engine)
        self.engine = engine
        self.session = Session()
_singleton = _Singleton()
def orm(): return _singleton.session
def engine(): return _singleton.engine




