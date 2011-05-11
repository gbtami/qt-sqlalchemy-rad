# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtWebKit
from inputs import *
from changes import changes
from conf import iconPath, dataPath, getModels, i18n
from model import orm
import operator
import sqlalchemy.exc
import random
import time
import locale
import datetime
import win32clipboard


locale.setlocale( locale.LC_ALL, "" )

def setCliboardText(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text)
    win32clipboard.CloseClipboard()
    
    print text

def money_format(amount):
    try:
        integer, decimals = str(amount).split('.')
    except ValueError:
        return ''
    length = len(decimals)
    length = length - 1 if amount == int(amount) else length
    return locale.format('%0.'+str(length)+'f', amount, True).decode('windows-1251')

class OneTypeList(list):
    def __init__(self, type, *items):
        self.type = type
        list.__init__(self)
        for item in items:
            self.append(item)
    
    def append(self, item):
        if not isinstance(item, self.type):
            raise TypeError(u"Incompatible data type", item, type(item), self.type)
        list.append(self, item)
            
class ModelUpdateThread(QThread):
    '''Поток для обновления данных модели
    @warning: пока что не используется, в дальнейшем следует перейти на него
    '''
    def __init__(self, tableview, model):
        QThread.__init__(self)
        self.tableview = tableview
        self.model = model
        
    def run(self):
        try:
            for i in range(51, self.model.count(), 50):
                self.model.emit(SIGNAL("layoutAboutToBeChanged()"))
                result = self.model.query(offset=i, limit=50)
                for row in result:
                    r = []            
                    for column in self.model.display_columns:
                        if column.foreign_keys:
                            foreign_key = column.foreign_keys[0]
                            item = orm().query(getattr(getModels(), str(foreign_key.column.table).capitalize())).filter_by(id=getattr(row, column.name)).first()
                            r.append(unicode(item))
                        else:
                            value = getattr(row, column.name)
                            if str(column.type) == 'DATE' or str(column.type) == 'Date()':
                                try:
                                    r.append(value.strftime("%d.%m.%Y"))
                                except AttributeError:
                                    r.append('')                        
                            else:
                                r.append(value if value else '')
                    self.model.arraydata.append(r)        
                self.model.emit(SIGNAL("layoutChanged()"))
                time.sleep(0.4)
                #self.tableview.setModel(self.model)
        except AttributeError, error:
            print "thread model error", error
        
            

class ModelGeneral(QAbstractTableModel):
    '''Стандартная модель данных для TableView'а'''
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = []
        self.headerdata = []
        
    def getTableChilds(self):
        return []
    
    def getTableReferences(self):
        return []   
    
    def getHeaderdata(self):
        return self.headerdata
    
    def rowCount(self, parent): 
        return len(self.arraydata) 
 
    def columnCount(self, parent=None): 
        try:
            return len(self.arraydata[0])
        except IndexError:
            return 0; 
            
    def data(self, index, role):        
        value = self.getItemData(index.row(), index.column())
        if index.isValid and role == Qt.DisplayRole: 
            if type(value) == type(1.0):
                return money_format(value)
            return unicode(value)
        elif role == Qt.TextColorRole:
            if self.headerdata[index.column()].type == 'dateedit':
                return QVariant(QColor(155, 39, 136)) 
            elif type(value) == type(1.0) and value < 0:
                return QVariant(QColor(255, 8, 8))
            
    
    def getItemData(self, row, column):
        try:
            return self.arraydata[row][column]
        except IndexError:
            return ''
    
    def headerData(self, col, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                return unicode(self.headerdata[col])
            except IndexError, e:
                print e
        return 
    
    def headerObject(self, col):
        return self.headerdata[col]
    
    def flags(self, index):
        if index.column() > 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def sort(self, Ncol, order=Qt.AscendingOrder):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
         
        if self.getHeaderdata()[Ncol].type == 'dateedit':
            for row in self.arraydata:
                day, month, year = row[Ncol].split('.')
                row[Ncol] = datetime.date(int(year), int(month), int(day))     
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))           
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        if self.getHeaderdata()[Ncol].type == 'dateedit':
            for row in self.arraydata: row[Ncol] = row[Ncol].strftime("%d.%m.%Y")   
            
        self.emit(SIGNAL("layoutChanged()"))

class ModelSqlAlchemy(ModelGeneral):
    '''Автоматически подгружаемая модель данных для QTableView. В качестве параметра принимает класс SqlAlchemy
        пример: 
        fintoolModel = ModelSqlAlchemy(Fintool)
    '''
    def __init__(self, table, parent=None, *args): 
        ModelGeneral.__init__(self, parent, *args)
        self.table = table
        self.update()
        
    def __del__(self):
        self.updateTimer.stop()
        
    def getObjectData(self):
        pass
    
    def getColumnData(self, title):
        index = self._getColumnIndexByName(title)
        return self._getColumnDataByIndex(index)
    
    def _getColumnIndexByTitle(self, title):
        for i in range(0, len(self.headerdata)):
            column = self.headerdata[i]
            if column.title == title:
                return i
            
    def _getColumnIndexByName(self, name):
        for i in range(0, len(self.headerdata)):
            column = self.headerdata[i]
            if column.name == name:
                return i
    
    def _getColumnDataByIndex(self, index):
        return [row[index] for row in self.arraydata]
    
    def appendColumnData(self, column, data):        
        self.headerdata.append(column)
        self.emit(SIGNAL("layoutAboutToBeChanged()"))    
        for i in range(0, len(data)):
            self.arraydata[i].append(data[i])
        self.emit(SIGNAL("layoutChanged()"))
        
    def columns(self):
        self.headerdata, self.display_columns, self.tableReferences = OneTypeList(type=Column), [], []
        self.tableChilds = self.table.getChilds() if hasattr(self.table, 'getChilds') else []
        for column in self.table.__table__.c:
            if column.info:
                minlength = column.info['minlength'] if 'minlength' in column.info else 0
                c = Column(column.info['title'], column.name, minlength=minlength, sqltype=column.type)
                
                if column.foreign_keys:
                    foreign_key = column.foreign_keys[0]
                    c.table =  getattr(getModels(), str(foreign_key.column.table).capitalize())
                    c.type = 'combobox' 
                    self.tableReferences.append(c)
                elif str(column.type) == 'DATE' or str(column.type) == 'Date()':
                    c.type = 'dateedit'
                elif str(column.type) == 'TEXT' or str(column.type).find('Text') != -1:
                    c.type = 'longtextedit'
                elif str(column.type) == 'Float' or str(column.type) == 'FLOAT':
                    c.type = 'numericedit'
                elif str(column.type) == 'TIME' or str(column.type) == 'Time()':
                    c.type = 'timeedit'
                else:
                    c.type = 'textedit' 
                
                self.headerdata.append(c)
                self.display_columns.append(column)
        return self.display_columns
 
    def getTableReferences(self):
        return self.tableReferences
    
    def getTableChilds(self):
        return self.tableChilds
 
    def getColumns(self):
        return self.display_columns
    
    def getHeaderdata(self):
        return self.headerdata
 
    def update(self):
        '''Загрузка данных'''
        self.arraydata = []
        self.columns()
        
        count = self.count()
        self.offset = 0        
        def updateTick():
            if self.offset >= count:
                self.updateTimer.stop()
                return 
            self.emit(SIGNAL("layoutAboutToBeChanged()"))
            result = self.query(offset=self.offset, limit=self.getLimit())
            for row in result:
                r = []            
                for column in self.display_columns:
                    if column.foreign_keys:
                        foreign_key = column.foreign_keys[0]
                        item = orm().query(getattr(getModels(), str(foreign_key.column.table).capitalize())).filter_by(id=getattr(row, column.name)).first()
                        r.append(unicode(item))
                    else:
                        value = getattr(row, column.name)
                        if str(column.type) == 'DATE' or str(column.type) == 'Date()':
                            try:
                                r.append(value.strftime("%d.%m.%Y"))
                            except AttributeError:
                                r.append('')   
                        elif str(column.type) == 'BOOLEAN':
                            r.append(u'Да' if value else u'Нет')                     
                        else:
                            r.append(value if value else '')
                self.arraydata.append(r)
            self.offset += self.getLimit()
            self.emit(SIGNAL("layoutChanged()"))
        
        self.updateTimer = QTimer(self)
        
        updateTick()

        self.connect(self.updateTimer, SIGNAL("timeout()"), updateTick)
        self.updateTimer.start()

    def getLimit(self):
        return 2
             
    def query(self, offset=0, limit=10000):
        '''Запрос для получения данных.'''
        #return session.query(self.table).limit(10).offset(0).all()
        return orm().query(self.table).order_by(self.table.id).limit(limit).offset(offset).all()
    
    def count(self, session=orm()):
        '''Возвращает количество записей в таблице'''
        return session.query(self.table).count()
 
    def createItem(self, item):
        '''Необходимо не забыть переопределить если к примеру у элемента есть родитель. пример:
        item.parent_id = self.id'''
        return item
    
    def getRowIndex(self, id):
        i = 0
        for row in self.arraydata:
            if row[0] == id:
                return i
            i += 1
        return -1
 
    
class Column():
    def __init__(self, title, name=None, type='textedit', minlength=0, table=None, sqltype=None):
        self.title = title
        self.type = type
        self.name = name
        self.minlength = minlength
        self.table = table
        self.sqltype = sqltype
    
    def __repr__(self):
        return self.title    

class QStandartItemDelegate(QItemDelegate):
    '''Делегатор для pyqt. Возвращает редактор для ячейки в TableView'''
    def __init__(self, parent=None, *args):
        self.parent = parent
        QItemDelegate.__init__(self, parent, *args)
        
    def createEditor(self, parent, option, index): 
        qApp.setOverrideCursor(Qt.BusyCursor) 
        column = self.parent.model().headerObject(index.column())
        if column.type == 'combobox':        
            editor = QMySqlAlchemyComboBoxExtended(column.table, index, parent)
            editor.combobox.setMinimumHeight(30)
            editor.searchbutton.resize(QSize(30, 30))
        elif column.type == 'dateedit':
            value = index.data().toString()
            editor = QMyDateEdit(parent)
            id = self.parent.model().arraydata[index.row()][0]
            item = orm().query(self.parent.model().table).filter_by(id=id).first()
            if getattr(item, column.name):
                editor.setDate(getattr(item, column.name))
        elif column.type == 'timeedit':
            value = index.data().toString()
            editor = QMyTimeEdit(parent)
            editor.setTime(value)    
        elif column.type == 'longtextedit':
            value = index.data().toString()
            editor = QMyTextEdit(parent)
            editor.setText(value)
            self.parent.setRowHeight(index.row(), 150)
        elif column.type == 'numericedit':
            #value = str(self.parent.model().arraydata[index.row()][index.column()])
            value = index.data().toString()
            editor = QMyNumericLineEdit(parent)
            editor.setText(value)
        else:         
            value = index.data().toString()
            editor = QMyLineEdit(parent)
            editor.setText(value)
        qApp.restoreOverrideCursor()
        return editor

    def setEditorData(self, editor, index):
        pass

    def setModelData(self, editor, model, index):
        self.parent.setRowHeight(index.row(), 30)
        
        model = self.parent.model()
        arraydata = self.parent.model().arraydata
        
        id = arraydata[index.row()][0]
        if id:
            item = orm().query(model.table).filter_by(id=id).first()
            setattr(item, model.headerObject(index.column()).name, editor.text())
            
            item = self.parent.model().createItem(item)
            try:
                orm().commit()            
                arraydata[index.row()][index.column()] = editor.displaytext()
            except (ValueError, sqlalchemy.exc.IntegrityError), error:
                QMessageBox.critical(self.parent, u'Ошибка сохранения изменений', str(error))

        
class QGeneralTableView(QTableView):
    '''Вид для таблицы
    пример:
    viewtable = QGeneralTableView()
    viewtable.setModel(ModelSqlAlchemy(Fintool)'''
    def __init__(self, parent=None, *args): 
        QTableView.__init__(self, parent, *args) 
        self.setAlternatingRowColors(1) 
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        
        #self.setEditTriggers(QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed)
        
        
    
        self._delegate =  QStandartItemDelegate(self)
        self.setItemDelegate(self._delegate)
        
        #header = self.horizontalHeader()
        #header.setResizeMode(6)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openContextMenu)
    
       
    def getIds(self):
        '''Получаем id всех элементов в таблице'''
        ids = set()
        selected = self.selectedIndexes()
        for index in selected:
            id = self.model().arraydata[index.row()][0]
            ids.add(id)
        return ids
    
    def getSelectedIds(self):
        '''Получаем id выбранных элементов в таблице'''
        ids = set()
        selected = self.selectedIndexes()
        for index in selected:
            id = self.model().arraydata[index.row()][0]
            if id:
                ids.add(id)
        return ids
    
    def keyPressEvent(self, event):
        if event.key() == 67: #Ctrl + C
            pass
        QTableView.keyPressEvent(self, event)
    
    def getFirstSelectedId(self):
        ids = set()
        selected = self.selectedIndexes()
        for index in selected:
            id = self.model().arraydata[index.row()][0]
            if id:
                return id
        return False
    
    def openContextMenu(self, contextmenu=None):
        '''Создаем контекстное меню для таблицы'''
        if not hasattr(self.model(), 'table'):
            return               
        if type(contextmenu) != QMenu:
            contextmenu = QMenu(self)
        
        def show(title, windowClass):
            def wrap():
                id = self.getFirstSelectedId()
                if id:
                    self.window = windowClass(id, self)
                    self.window.setWindowTitle(title)
                    self.window.setWindowIcon(QIcon(iconPath('catalog.png')))
                    self.window.show()
            return wrap
        
        childs = self.model().getTableChilds()
        if childs:
            for title, windowClass in childs :
                action = QAction(title, self)
                contextmenu.addAction(action)
                self.connect(action, SIGNAL("triggered()"), show(title, windowClass))
            contextmenu.addSeparator()
        
        info = QAction(i18n(u"Подробная информация"), self)
        self.connect(info, SIGNAL("triggered()"), self.showInfoWindow)
        contextmenu.addAction(info)
        
        referencesMenuItem = self.referencesMenuItem()
        if referencesMenuItem:                    
            contextmenu.addAction(referencesMenuItem)
            
        copy = QAction(i18n(u"Копировать в буфер обмена"), self)
        self.connect(copy, SIGNAL("triggered()"), self.copyIntoClipboard)
        contextmenu.addAction(copy)
            
        contextmenu.popup(QCursor.pos())       
        
        
    
        width_list = []
        for i in range(0, len(self.model().getHeaderdata())):
            width_list.append([self.model().headerdata[i].name, self.columnWidth(i)])

        #logging.info('Columns width: %s' % str(width_list))
        #print 'Columns width: %s' % str(width_list)

    
    def referencesMenuItem(self):
        '''Меню отображающее связи с другими таблицами'''
        
        tableReferences = self.model().getTableReferences()
        if not tableReferences:
            return False
        
        references = QAction( i18n(u'Связи с другими таблицами'), self)    
        references_menu = QMenu(self)
        references_menu.setTitle(i18n(u"Связи с другими таблицами"))
        references.setMenu(references_menu)
        
        
        def openTableView(column, self):
            def wrap():
                id = self.getSelectedIds().pop()
                item = orm().query(self.model().table).filter_by(id=id).first()
                subid = getattr(item, column.name)                

                self.QSqlAlchemyTableWindow = QSqlAlchemyTableWindow(column.table, parent=self)
                self.QSqlAlchemyTableWindow.setWindowTitle(unicode(column))
                self.QSqlAlchemyTableWindow.setWindowIcon(QIcon(iconPath('catalog.png')))                
                self.QSqlAlchemyTableWindow.show()
                
                self.QSqlAlchemyTableWindow.selectRowById(subid)
            return wrap
                    
        for column in tableReferences:
            submenu = QAction(unicode(column), self)
            self.connect(submenu, SIGNAL("triggered()"), openTableView(column, self))
            references_menu.addAction(submenu)
        return references
    
    def copyIntoClipboard(self):
        ids = self.getSelectedIds()
        text = ''
        for i in range(len(self.model().arraydata)):
            row = self.model().arraydata[i]
            if row[0] not in ids:
                continue
            row = [unicode(k).encode('windows-1251') for k in row[1:]]
            string = '    '.join(row)
            text += string+"\r\n"       
        setCliboardText(text)
    
    def showInfoWindow(self):
        '''Отображаем окно с подробной информацией о записи в таблице'''
        id = self.getSelectedIds().pop()
        infoWindow = QInfoWindow(self.model().table, id, self)
        infoWindow.show()

    def resizeColumns(self, width=0):
        #self.resizeColumnsToContents()
        
        width = width if width > 0 else self.width()
        try:            
            try:
                columnCount = len(self.model().arraydata[0])
            except IndexError:
                columnCount = len(self.model().headerdata)       
        
            column = self.model().headerObject(0)
            first_column_width = 40 if 40 > column.minlength else column.minlength
            
            self.setColumnWidth(0, first_column_width)
            
            all_width = (width - first_column_width)
            for i in range(1, columnCount):
                column = self.model().headerObject(i)
                width = all_width / (columnCount - i)                
                #width = width if width > column.minlength else column.minlength
                width = column.minlength if column.minlength > 0 else 150
                self.setColumnWidth(i, width)
                all_width -= width
        except AttributeError, error:
            print error
            
    def columnsWidth(self):        
        count = self.model().columnCount()
        if count == 0:
            return 500
        return reduce( lambda x, y: x + y, [self.columnWidth(i) for i in range(0, count)] ) + 10
            
    def setModel(self, model):
        super(QGeneralTableView, self).setModel(model)      
        #self.updatethread = ModelUpdateThread(self, model)
        #self.updatethread.start()  
        self.hideColumn(0)
        self.resizeColumns()
    
    '''
    def __del__(self):
        while self.updatethread.isRunning() == True:
            pass
    '''
class QInfoWindow(QMainWindow):
    def __init__(self, modelClass, id, parent=None):
        super(QInfoWindow, self).__init__(parent)        
        
        self.setWindowTitle(u'Сведения')
        self.resize(QSize(700, 500))
        
        html = self.html(modelClass, id)                    
        view = QtWebKit.QWebView()
        view.setHtml(u'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8" lang="ru">          
<style type="text/css">
h3 {
background:#eeeeee none repeat scroll 0 0;
margin:0;
padding-top: 0px;
text-transform: none;
}
.sub {
margin-left: 55px;
padding: 3px;
float: left;
display: none;
width: auto;
}
a {
color: gray
}
body{
font-size: 13px;
}
div.field {
float: left;
width: 200px;
font-weight: bold;
padding: 3px;
}
div.value {
float: left;
width: 300px;
padding: 3px;
margin-left: 5px;
}
                  
</style>
</head>
<body>          
%s

<script>
function display(id){
    if (document.getElementById(id).style.display == 'block'){
        document.getElementById(id).style.display = 'none'
    } else {
        document.getElementById(id).style.display = 'block'
    }
}
</script>
</body></html>
''' % html);
        
        self.setCentralWidget(view)
      
    def html(self, modelClass, id):
        html = ''
        item = orm().query(modelClass).filter_by(id=id).first()
        for column in modelClass.__table__.c:
            if column.info and column.name != 'id':     
                value = ''
                cname = unicode(column.info['title'])                           
                if column.foreign_keys:
                    foreign_key = column.foreign_keys[0]
                    submodelClass =  getattr(getModels(), str(foreign_key.column.table).capitalize())
                    
                    subitem = orm().query(submodelClass).filter_by(id=getattr(item, column.name)).first()
                    
                    javascripid = random.random() 
                    value = '''
                    <div class="field"><a href="javascript:void(0);" onclick="display('%s')">%s:</a></div>
                    <div class="value">%s</div>   
                    <div style="clear:both;padding-top:4px;"></div>
                    <div class="sub" id="%s">%s</div>
                    <div style="clear:both"></div>
                     ''' % (javascripid, cname, unicode(subitem), javascripid, self.html(submodelClass, getattr(item, column.name)))          
                elif item:
                    if getattr(item, column.name):
                        value = '''
                        <div class="field">%s:</div> 
                        <div class="value">%s</div> 
                        <div style="clear:both;padding-bottom:4px;"></div>''' % (cname, unicode(getattr(item, column.name)))         
                
                  
                
                html += value
        return html
        
    def createBody(self):        
        innerWidget = QWidget(self)
        
        layout = QFormLayout()
        item = orm().query(self.modelClass).filter_by(id=self.id).first()
        for column in self.modelClass.__table__.c:
            if column.info:                                
                if column.foreign_keys:
                    foreign_key = column.foreign_keys[0]
                    modelClass =  getattr(getModels(), str(foreign_key.column.table).capitalize())
                    #subitem = orm().query(modelClass).filter_by(id=getattr(item, column.name)).first()
                    
                    value = QInfoWindow(modelClass, getattr(item, column.name), self)  
                    value.setStyleSheet("QWidget {background-color: #EEEEEE}")               
                else:
                    value = QLabel(unicode(getattr(item, column.name)))             
                
                title = QLabel("<b>%s</b>:" % unicode(column.info['title']))       
                layout.addRow(title, value)
                
        
        
        innerWidget.setLayout(layout)
        self.setCentralWidget(innerWidget)

class QWindowTriggerActiveAction():
    menus = []
    def setActiveAction(self, selectedaction):
        for menu in self.menus:
            for action in menu.actions():
                action.setIcon(QIcon())
        if selectedaction.icon().isNull():
            selectedaction.setIcon(QIcon(iconPath('black_circle.png')))
        else:
            selectedaction.setIcon(QIcon())
        
class QSqlAlchemyTableWindow(QMainWindow):
    '''Окно для редактирования таблицы 
    Пример:
    editTableCountry = QSqlAlchemyTableWindow(ClosingPrice)
    editTableCounrty.show()'''
    def __init__(self, model, tableview=QGeneralTableView, datatable=None, parent=None, flags=Qt.Window):
        self.tableview = tableview
        self.model = model      
        QMainWindow.__init__(self, parent, flags)
        self.datatable = datatable
        
        self.forms = []     
        
    def closeEvent(self, event):
        self.datatable.__del__()
        QMainWindow.closeEvent(self, event)
                
    def activateWindow(self):
        self.createBody()
        self.createToolbar()
        QMainWindow.activateWindow(self)
        
    def show(self):
        self.createBody()
        self.createToolbar()
        
        width = self.table.columnsWidth()
        width = width if width <= 1024 else 1024
        width = width if width > 600 else 600
        #self.resize(QSize(width, 600))
        QMainWindow.show(self)
        
    def setTableView(self, tableview):
        self.tableview = tableview     
    
    def setDatatable(self, datatable):
        self.datatable = datatable
        if hasattr(self, 'table'):
            self.table.setModel(self.datatable)   
        
    def selectRowById(self, id):
        '''Выбираем запись в таблице по id'''
        self.selectId = id
        def select():
            index = self.table.model().getRowIndex(self.selectId)
            if index != -1:                
                self.table.selectRow(index)
                self.selectTimer.stop()
        
        self.selectTimer = QTimer(self)
        self.connect(self.selectTimer, SIGNAL("timeout()"), select)
        self.selectTimer.start()
        
    def createToolbar(self):
        add = QAction(QIcon(iconPath('Add.png')), i18n(u'Добавить элемент'), self)        
        self.connect(add, SIGNAL('triggered()'), self.showAddWidget)
      
        delete = QAction(QIcon(iconPath('Delete.png')), i18n(u'Удалить выбранные элементы'), self)
        delete.setShortcut("Delete")
        self.connect(delete, SIGNAL('triggered()'), self.deleteItems)
                
        refresh = QAction(QIcon(iconPath('refresh.png')), i18n(u"Обновить"), self)
        self.connect(refresh, SIGNAL("triggered()"), self.updateTableView)
        
        #_importOneS = QAction(QIcon(iconPath('oneslogo.png')), u"Иморт из 1C", self)
        #self.connect(_importOneS, SIGNAL("triggered()"), self._importOneS)
        
         
                
        self.tabletoolbar = self.addToolBar(i18n(u'Управление элементами'))        
        self.tabletoolbar.setMovable(False)
        self.tabletoolbar.setIconSize(QSize(32, 32))
        
        
        self.tabletoolbar.addAction(add)
        self.tabletoolbar.addAction(delete)
        self.tabletoolbar.addAction(refresh)
        #if Guard().isAdmin():
            #self.tabletoolbar.addAction(_importOneS)
        
        self.createFilterToolbar()
    
    def _importOneS(self):
        pass
        #window = QOneSImportWindow(self.model, parent=self)
        #window.show()
    
    def createFilterToolbar(self):
        self.searchinput = QFilterInput(self.table)       
        self.searchtoolbar = QToolBar(i18n(u"Поиск"))
        self.searchtoolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.searchtoolbar)        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.searchtoolbar.addWidget(spacer)         
        self.searchtoolbar.addWidget(self.searchinput)
        
        filter = QAction(QIcon(iconPath('Search.png')), i18n(u'Расширенный поиск'), self)
        filter.setShortcut(self.tr("Ctrl+F"))
        self.connect(filter, SIGNAL('triggered()'), self.showFilterWidget)
        self.searchtoolbar.addAction(filter)
                  
    def createBody(self):
        self.datatable = self.datatable if self.datatable else ModelSqlAlchemy(self.model)
        self.table = self.tableview(parent=self.parent())
        self.table.setModel(self.datatable)

        widget = QWidget()
        widget.setContentsMargins(0, 0, 0, 0)        

        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setMargin(0)        
        self.layout.setRowStretch(0, 0)
        
        self.layout.addWidget(self.table, 1, 0)
        
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.setCentralWidget(widget)
        
    def deleteItems(self):
        class QDeleteDialog(QDialog):
            def __init__(self, parent=None):
                QDialog.__init__(self, parent)
                self.setWindowIcon(QIcon(iconPath('Delete.png')))
                self.setWindowTitle(i18n(u"Потверждение удаления"))
                layout = QGridLayout()
                ok = QPushButton(i18n(u"Удалить"))
                self.connect(ok, SIGNAL("clicked()"), self.accept)
                cancel = QPushButton(i18n(u"Отмена"))
                self.connect(cancel, SIGNAL("clicked()"), self.reject)
                layout.addWidget(QLabel(i18n(u"Вы действительно хотите удалить выбранные элементы?")), 0, 0)
                butlayout = QHBoxLayout()
                butlayout.addWidget(ok)
                butlayout.addWidget(cancel)
                layout.addLayout(butlayout, 1, 0)
                self.setLayout(layout)   
        
        self.deleted = []
        ids = self.table.getSelectedIds()
        self.i = 0
        def delete():
            def stop():
                timer.stop()
                self.progress.close()
                self.updateTableView()
                changes().addDeleteAction(self.deleted)
            
            if not ids or self.progress.wasCanceled():                
                return stop()
            item_id = ids.pop()     
            item = orm().query(self.model).filter_by(id=item_id).first()                      
            orm().delete(item)
            
            restoreitem = item.__class__()
            for name, value in vars(item).iteritems():
                if not name.startswith('_'):
                    setattr(restoreitem, name, value)                  
            self.deleted.append(restoreitem)
            
            try:
                orm().commit()
            except sqlalchemy.exc.IntegrityError, error:
                QMessageBox.warning(self, i18n(u"Не удалось удалить объект"), 
                                    i18n(u"Сначала удалите элементы родителем которы является данный объект."))
                orm().rollback()
                return stop()
            self.i += 1
            self.progress.setValue(self.i)
        
        
        
                
        timer = QTimer(self)
        self.connect(timer, SIGNAL("timeout()"), delete)
        if QDeleteDialog(self).exec_():
            self.progress = QProgressDialog(i18n(u"Удаление данных"), i18n(u"Отмена"), 0, len(ids), parent=self)
            self.progress.setWindowTitle(i18n(u"Удаление..."))
            self.progress.setFixedWidth(300)
            self.progress.show()
            timer.start()  
        
    
    def showAddWidget(self):
        self.showWidget('formAdd', QSqlAlchemyTableWindowWidgetAdd, self.model, self)
            
    def showFilterWidget(self):
        self.filterForm = QSqlAlchemyTableWindowWidgetFilterExtentded(self.table, self.datatable, parent=self)
        self.filterForm.show()
        
        #self.showWidget('formFilterExtentded', QSqlAlchemyTableWindowWidgetFilterExtentded, self.table, self.datatable)
        
    def showWidget(self, instance, widgetclass, *args):
        if not hasattr(self, instance):
            if args:
                setattr(self, instance, widgetclass(*args))
            else:
                setattr(self, instance, widgetclass(self))
            self.forms.append(getattr(self, instance))
            self.layout.addWidget(getattr(self, instance), 0, 0)  
        if not getattr(self, instance).isVisible():
            for form in self.forms:
                form.hide()
            getattr(self, instance).show()
        else:
            getattr(self, instance).hide()
        
    def createItem(self):
        try:
            item = self.formAdd.getForm()
            item = self.datatable.createItem(item)
            orm().add(item)
            orm().commit()          
        except sqlalchemy.exc.IntegrityError, e:
            QMessageBox.information(self, i18n(u'Ошибка sqlalchemy.'), str(e))
            orm().rollback()        
        except ValueError, e:
            QMessageBox.information(self, i18n(u'Неправильное значение'), str(e))
            orm().rollback()        
    
        self.updateTableView()
        
    def updateTableView(self):
        self.datatable.update()  
        self.table.setModel(None)
        self.table.setModel(self.datatable)
        self.table.resizeColumns()
    
class QSqlAlchemyTableWindowWidgetAdd(QWidget):
    '''Виджет-форма для добавление элемента. В качестве параметра принимает ModelSqlAlchemy'''
    def __init__(self, modelClass, parent, okButton=None):
        QWidget.__init__(self, parent, Qt.WindowCloseButtonHint)
        self.modelClass = modelClass

        self.setWindowTitle(i18n(u'Добавление элемента'))
        self.setWindowIcon(QIcon(iconPath('Add.png')))
        self.setMinimumWidth(400)
        
        self.inputfields = self.createFields()        

        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetFixedSize)  
            
        layout = QFormLayout()
        layout.setSizeConstraint(QLayout.SetFixedSize)  
        for column, field in self.inputfields[:len(self.inputfields) / 2 + 1]:
            layout.addRow(QLabel(column.info['title'] + ':'), field)
        self.layout.addLayout(layout, 0, 0)
            
        layout = QFormLayout()
        self.formlayout = layout
        layout.setSizeConstraint(QLayout.SetFixedSize)
        for column, field in self.inputfields[len(self.inputfields) / 2 + 1:]:
            layout.addRow(QLabel(column.info['title'] + ':'), field)
        
        if not okButton:
            self.ok = QPushButton(i18n(u'Добавить элемент'))
            self.connect(self.ok, SIGNAL("clicked()"), parent.createItem)
        else:
            self.ok = okButton
        layout.addRow(QWidget(), self.ok)
        
        self.layout.addLayout(layout, 0, 1)    
        
        self.setLayout(self.layout)
        
    def createFields(self):
        inputfields = []
        def getField(cname):
            for c, field in inputfields:
                if c.name == cname:
                    return field
            return False
        
        for column in self.modelClass.__table__.c:
            if column.info:
                if 'isAutoField' in column.info:
                    continue
                if column.name == 'id':
                    continue
                
                if column.foreign_keys:
                    foreign_key = column.foreign_keys[0]               
                    if 'parent' in column.info:
                        parent_column = column.info['parent']
                        combobox = getField(parent_column).combobox
                        combobox.parent_cname = parent_column 
                        item = QMySqlAlchemyComboBoxExtended(table=getattr(getModels(), str(foreign_key.column.table).capitalize()), 
                                                     parent_input=combobox)                      
                    else:
                        item = QMySqlAlchemyComboBoxExtended(table=getattr(getModels(), str(foreign_key.column.table).capitalize()))
                else:
                    if str(column.type) == 'DATE' or str(column.type) == 'Date()':
                        item = QMyDateEdit()
                    elif str(column.type) == 'TIME' or str(column.type) == 'Time()':
                        item = QMyTimeEdit()
                    elif str(column.type) == 'Float' or str(column.type) == 'FLOAT':
                        item = QMyNumericLineEdit()
                    elif str(column.type) == 'Boolean' or str(column.type) == 'BOOLEAN':
                        item = QMyCheckbox()
                    else:
                        item = QMyLineEdit()
                
                inputfields.append([column, item])
        return inputfields
        
    def getForm(self):
        item = self.modelClass()
        for column, field in self.inputfields:
            text = field.text()
            if text:
                setattr(item, column.name, text)
        return item
    
    
class QSqlAlchemyTableWindowWidgetFilterExtentded(QMainWindow):
    '''Виджет для фильтрации таблицы'''
    def __init__(self, table, datatable, parent=None):
        super(QSqlAlchemyTableWindowWidgetFilterExtentded, self).__init__(parent, Qt.Tool | Qt.Dialog)        
        self.setWindowTitle(i18n(u"Расширенный поиск"))
        self.setWindowIcon(QIcon(iconPath('Search.png')))
        self.table = table
        self.datatable = datatable
        fields = self.createFields()
        
        def filterwrap(editor, columnum): 
            '''Замыкание, здесь используется для передачи самого editor'а'''                      
            def filter(event):                   
                '''Фильтруем данные какого-либо столбца. Если находим запись похожую на нашу то показываем ее
                иначе скрываем'''
                searchtext = editor.text()
                i = 0        
                for row in self.table.model().arraydata:
                    if str(row[columnum]).find(searchtext) == -1:
                        self.table.setRowHidden(i, True)
                    else:
                        self.table.setRowHidden(i, False)
                    i += 1
                                    
            return filter
        
        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetFixedSize)
        i = 0      
        for index, label, f in fields: 
            if i % 2 == 0: 
                sublayout = QHBoxLayout()  
                sublayout.setSizeConstraint(QLayout.SetFixedSize)
                layout.addLayout(sublayout)  
            cleft = self.table.columnViewportPosition(index)
            cwidth = self.table.columnWidth(index)               
            
            label = QLabel(label + ":")
            label.setFixedWidth(120)
            sublayout.addWidget(label)
            sublayout.addWidget(f)
            sublayout.setAlignment(Qt.AlignLeft)            
            
            f.table = self.table
            f.keyReleaseEvent = filterwrap(f, index)
                                     
            i += 1
            
          
        #layout.addWidget(QLabel(u"<b>Фильтрация данных:</b>"))
        
        
        layoutWidget = QWidget()
        layoutWidget.setLayout(layout)
        self.setCentralWidget(layoutWidget) 
        
    def createFields(self):
        '''Создание полей для схемы в бд'''
        fields, index = [], 0
        for c in self.datatable.getColumns():
            if 'title' in c.info:
                field = QMyLineEdit()
                label = c.info['title']            
                
                fields.append([index, label, field])
                index += 1 
        return fields
    
    
class QFilterInput(QMyLineEdit):
    '''Поле поиска по таблице'''
    def __init__(self, table, parent=None):
        super(QFilterInput, self).__init__(parent)
        self.table = table
        self.setFixedWidth(125)
    
    def keyReleaseEvent(self, event):
        searchtext = self.text().lower()
        i = 0        
        for row in self.table.model().arraydata:
            isFound = False
            for item in row:
                isFound = False if unicode(item).lower().find(searchtext) == -1 else True
                if isFound:
                    break
            
            if not isFound:
                self.table.setRowHidden(i, True)
            else:
                self.table.setRowHidden(i, False)
            i += 1
    
    
class QWorkspaceItem():
    '''Класс-форма имеющая кнопки навигации. Использовать как родитель.
    Пример: 
    class FinancialStateQSqlAlchemyTableWindow(QSqlAlchemyTableWindow, QWorkspaceItem):
        pass'''
    def createNavigationToolbar(self, workspace):
        self.workspace = workspace
        
        #Кнопки перемещения вперед, назад по рабочей области
        '''
        back = QAction(QIcon(iconPath('Back.png')), u'Предыдущее окно', self)
        back.setShortcut("Backspace")
        self.connect(back, SIGNAL('triggered()'), self.backAction)
        
        next = QAction(QIcon(iconPath('Next.png')), u'Следующее окно', self)
        self.connect(next, SIGNAL('triggered()'), self.nextAction)
        
        toolbar = self.addToolBar(u'Навигация')
        toolbar.setIconSize(QSize(32, 32))
        toolbar.addAction(back)
        toolbar.addAction(next)
        toolbar.setMovable(False)
        '''
        
    def backAction(self):
        self.workspace.activatePreviousWindow()
        
    def nextAction(self):
        self.workspace.activateNextWindow()
        
        

class QTableSelectFormTableView(QGeneralTableView):
    '''TableView для формы выбора элемента'''
    def __init__(self, parent=None):
        super(QTableSelectFormTableView, self).__init__(parent)
    
    def mouseDoubleClickEvent(self, event):
        #@todo rewrite!!! parent().parent().parent() is ass!!!        
        self.parent().parent().parent().setText(self.getFirstSelectedId())
        self.parent().parent().close()
    


class QTableSelectForm(QSqlAlchemyTableWindow):
    '''Форма для выбора элемента'''
    def __init__(self, model, parent=None):
        super(QTableSelectForm, self).__init__(model, tableview=QTableSelectFormTableView, parent=parent, flags=Qt.WindowStaysOnTopHint)
        self.setWindowTitle(i18n(u"Выберите элемент"))
        self.resize(QSize(1100, 600))        
        
        
class QMySqlAlchemyComboBoxExtended(QWidget):
    '''автоматически подгружаемый комбо бокс из sqlalchemy модели'''
    def __init__(self, table, index=None, parent=None, parent_input=None):
        super(QMySqlAlchemyComboBoxExtended, self).__init__(parent)
        self.table = table
        self.index = index
        
        self.combobox = QMySqlAlchemyComboBox(self.table, parent_input=parent_input, parent=self)
        self.combobox.loadElements(index=self.index)
        self.combobox.setMaxVisibleItems(30)
        
        self.searchbutton = QPushButton(QIcon(iconPath('Search.png')), u"")
        self.searchbutton.resize(QSize(20, 20))
        self.searchbutton.setMaximumWidth(30)
        self.connect(self.searchbutton, SIGNAL("clicked()"), self.showTableSelectForm)
            
        layout = QHBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.combobox)
        layout.addWidget(self.searchbutton)
        self.setLayout(layout)
        
    def showTableSelectForm(self):
        qApp.setOverrideCursor(Qt.BusyCursor) 
        self.tableSelectForm = QTableSelectForm(self.table, parent=self)
        self.tableSelectForm.show()
        qApp.restoreOverrideCursor() 
        
    def setText(self, selectedId):
        self.combobox.loadElements(self.index)
        for i in range(0, self.combobox.count()):
            id, bool = self.combobox.itemData(i).toInt()
            if selectedId == id:
                self.combobox.setCurrentIndex(i)
                break
        
    def setEnabled(self, enabled):
        self.combobox.setEnabled(enabled)
        self.searchbutton.setEnabled(enabled)
        
    def setCurrentIndex(self, index):
        self.combobox.setCurrentIndex(index)
    
    def text(self):
        return self.combobox.text()
    
    def displaytext(self):
        return unicode(orm().query(self.table).filter_by(id=self.text()).first())
    
class QTableViewSimple(QGeneralTableView):
    def __init__(self, parent=None, *args): 
        QTableView.__init__(self, parent, *args) 
        self.setAlternatingRowColors(1) 
        self.setShowGrid(False)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
    
    def openContextMenu(self):
        pass
    
    def setModel(self, model):
        super(QGeneralTableView, self).setModel(model)
        self.resizeColumns()
        