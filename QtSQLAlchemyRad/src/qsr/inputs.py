# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from model import orm
from conf import iconPath
import re
import datetime

class QMyDateEdit(QDateEdit):
    '''поле для редактирования даты'''
    def __init__(self, parent=None):
        super(QMyDateEdit, self).__init__(parent)
        self.setCalendarPopup(True)
        self.setFixedWidth(200)
        self.setDate(datetime.date.today())
        
    def text(self):
        date = self.date()     
        return datetime.date(date.year(), date.month(), date.day())    
    
    def displaytext(self):
        return self.text()

   

class QMyComboBox(QComboBox):
    def __init__(self, parent=None):
        super(QMyComboBox, self).__init__(parent)
        self.setEditable(True)
        self.setAutoCompletion(True)
        self.words = QStringList()     
        self.setFixedWidth(200)         
    
    def text(self):
        id, bool = self.itemData(self.currentIndex()).toInt()  
        return id    
        
    def addItem(self, item, variant):
        super(QMyComboBox, self).addItem(item, variant)
        
        self.words.append(item)
        self.completer = QCompleter(self.words)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        #self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)
        
    def addItemsList(self, items):
        for i in range(0, len(items)):
            self.addItem(items[i], i)

class QMyCheckbox(QCheckBox):
    def text(self):
        return 1 if self.isChecked() else 0
        
class QMySqlAlchemyComboBox(QMyComboBox):
    '''Комбобокс с подгрузкой элементов из бд
    table - sqlalchemy модель
    parent_input - QMySqlAlchemyComboBox с которым есть зависимость'''
    def __init__(self, table, parent_input=None, parent=None):
        QMyComboBox.__init__(self, parent)
        self.table = table  
        self.parent_input = parent_input
        if self.parent_input:
            self.connect(self.parent_input, SIGNAL("currentIndexChanged(int)"), self.parentValueSelected)
            
    def parentValueSelected(self, index):
        self.loadElements()
    
    def loadElements(self, index=None):            
        self.clear()
        if self.parent_input:
            parent_id = self.parent_input.text()
            column = getattr(self.table, self.parent_input.parent_cname)
            items = orm().query(self.table).filter(column == parent_id).all()
        else:
            items = orm().query(self.table).all()
        i = 0
        for item in items: 
            self.addItem(unicode(item), QVariant(item.id))
            if index:
                if unicode(item) == index.data().toString():
                    self.setCurrentIndex(i)
            i += 1
     
class QMyLineEdit(QLineEdit):
    '''Обычное текстовое поле'''
    def __init__(self, text=''):
        QLineEdit.__init__(self, text)
        self.setFixedWidth(200)
    
    def text(self):
        return unicode(super(QMyLineEdit, self).text())
    
    def displaytext(self):
        return self.text()
    
class QMyTimeEdit(QWidget):
    '''Поле для ввода времени'''
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.setFixedWidth(200)
        
        self.hours = QMyComboBox()
        self.hours.setFixedWidth(50)
        for i in range(0, 24):
            self.hours.addItem("%0.2d" % i, QVariant(i))
            
        self.minutes = QMyComboBox()
        self.minutes.setFixedWidth(50)
        for i in range(0, 60):
            self.minutes.addItem("%0.2d" % i, QVariant(i))
        
        layout = QHBoxLayout()
        layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.hours)
        layout.addWidget(QLabel(":"))
        layout.addWidget(self.minutes)
        self.setLayout(layout)
        
    def setTime(self, value):
        pass
        
    def text(self):
        time = datetime.time(self.hours.text(), self.minutes.text())
        return time      
    
    def displaytext(self):
        return "%0.2d:%0.2d:00" % (self.hours.text(), self.minutes.text())

class QMyNumericLineEdit(QMyLineEdit):
    '''Поле для ввода денежных значений'''
    def __init__(self, parent=None):
        QMyLineEdit.__init__(self, parent)
        validator = QDoubleValidator(self)
        #validator = QRegExpValidator( QRegExp( r"^[-]?([1-9]{1}[0-9]{0,}(\.[0-9]{0,2})?|0(\.[0-9]{0,2})?|\.[0-9]{1,2})$" ), self )
        validator.setRange(-99999999999999.99, 99999999999999.99, 2)
        validator.setDecimals(20)          
        self.setValidator(validator)
        
    def text(self):
        text = str(QLineEdit.text(self))
        text = re.sub(r'[^0-9\,\.-]', r'', text)
        text = text.replace(',', '.')
        return text

class QMyTextEdit(QTextEdit):
    '''Форма для ввода текста'''
    def text(self):
        return unicode(self.toPlainText())
    
    def displaytext(self):
        return self.text()   
    
class QButtonExtendedActions(QWidget):
    def __init__(self, title, parent=None):
        QWidget.__init__(self, parent)
                
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.setSpacing(0)
        
        self.main = QPushButton(title)
        self.main.setFixedHeight(25)
        layout.addWidget(self.main)
        
        self.additional = QPushButton()
        self.additional.setIcon(QIcon(iconPath('cogwheel.png')))   
        self.additional.setFixedHeight(25)
        self.connect(self.additional, SIGNAL("clicked()"), self.openContextMenu)     
        layout.addWidget(self.additional)
        
        self.setLayout(layout)        
        self.menu = QMenu(self)
        
    def openContextMenu(self):
        #reportpackage = QAction(u'Составить заключение по рискам', self)
        #view = QAction(u'Просмотреть цены закрытия', self)
        
        #self.menu = QMenu(self)
        #self.menu.addAction(view)
        #self.menu.addAction(reportpackage)
        #self.menu.addSeparator()
        #menu.addAction(delete)
        self.menu.popup(QCursor.pos()) 