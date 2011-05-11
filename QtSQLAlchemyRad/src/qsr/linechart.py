from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtWebKit
from conf import iconPath, dataPath
import ImageGrab

class QChartDataHeader():
    isVisible = True
    def __init__(self, name):
        self.name = name
        
    def __repr__(self):
        return self.name 
    
class QChartData():
    def __init__(self, dates=None):
        if type(dates) == type([]):
            self.headerdata = [QChartDataHeader(u'Date')]
            self.arraydata = [[self._toDate(item)] for item in dates]
        else:
            self.headerdata = [QChartDataHeader(u'#')]
            self.arraydata = [[i] for i in range(1, dates+1)]
         
    def getDataToDisplay(self):
        data = list()
        for i in range(len(self.arraydata)):
            row = [self.arraydata[i][j] for j in range(len(self.headerdata)) if self.headerdata[j].isVisible]
            data.append('"'+','.join([str(k) for k in row])+'\\n"')
        return '+'.join(data)
        #return '+'.join(['"'+','.join([str(k) for k in row])+'\\n"' for row in self.arraydata])
    
    def getX(self):
        return [row[0] for row in self.arraydata]
    
    def __iter__(self):
        for i in range(1, len(self.headerdata)):
            data = [row[i] for row in self.arraydata]
            yield self.headerdata[i].__repr__(), data
    
    def getLinesNames(self):
        return [c.__repr__() for c in self.headerdata]
            
    def getLinesNamesToDisplay(self):
        for c in self.headerdata:
            if c.isVisible:
                yield c.__repr__()
        
    def addLine(self, title, data):
        self.headerdata.append(QChartDataHeader(title))
        #if len(self.arraydata) != len(data): raise NameError("Length of data not equals")
        
        for i in range(min(len(self.arraydata), len(data))):
            self.arraydata[i].append(data[i])
        
    def _toDate(self, date):        
        day, month, year = date.split('.')
        return "%s-%s-%s" % (year, month, day)

     
class QChartWinsRegister():
    def __init__(self):
        self.wins = list()
        
    def register(self, chartWin):    
        self.wins.append(chartWin)
        
    def unregister(self, chartWin):
        for i in range(len(self.wins)):
            try:
                if self.wins[i] == chartWin:
                    del self.wins[i]
            except IndexError:
                break
        
    def getChartsWins(self):
        return self.wins

_chartWinsRegister = QChartWinsRegister()
def chartWinsRegister(): return _chartWinsRegister

class QChart(QMainWindow):
    '''Абстрактный класс для составления линейных графиков''' 
    dwidth, dheight = 440, 220   
    def __init__(self, title, qdata, parent=None):
        QMainWindow.__init__(self, parent)      
        chartWinsRegister().register(self)
        
        self.qdata = qdata
        self.setWindowIcon(QIcon(iconPath('LineChart.png')))
        self.setWindowTitle(title)
        
        
        self.resize(QSize(self.dwidth, self.dheight))                
        self.drawChart()
                        
                        
        menubar = self.menuBar()
        menu_file = menubar.addMenu(u'&Файл')
        _print = QAction(QIcon(iconPath('Print.png')), u'Печать', self)
        _print.setShortcut('Ctrl+P')
        self.connect(_print, SIGNAL("triggered()"), self._print)
        menu_file.addAction(_print)
        
        saveAsImage = QAction(QIcon(iconPath('Save.png')), u'Сохранить как изображение', self)
        self.connect(saveAsImage, SIGNAL("triggered()"), self.saveAsImage)
        saveAsImage.setShortcut('Ctrl+S')
        menu_file.addAction(saveAsImage)
                
        menu_file.addSeparator()
                
        exit = QAction(QIcon(iconPath('Exit.png')), u'Закрыть', self)
        exit.setShortcut('Ctrl+Q')
        self.connect(exit, SIGNAL('triggered()'), self.close)
        menu_file.addAction(exit)
                
        def loadPlotMenu(actionJoin, self):
            def wrapper():
                menu = QMenu(self)
                for win in chartWinsRegister().getChartsWins():
                    if win == self or len(self.qdata.arraydata) > len(win.qdata.arraydata): continue
                    action = QAction(win.windowTitle(), self)
                    self.connect(action, SIGNAL("triggered()"), self.linkWithChart(win))
                    menu.addAction(action)
                actionJoin.setMenu(menu)
            return wrapper
                
        menu_plot = menubar.addMenu(u'&График')
        join = QAction(u'Связать с', self)
        self.connect(join, SIGNAL("hovered()"), loadPlotMenu(join, self))
        menu_plot.addAction(join)
        
        
        self.menu_display = menubar.addMenu(u'&Отображать')
        self._menuToggle()
            
    def _menuToggle(self):
        def togglePlot(index, chartWin):
            def wrapper():
                c = chartWin.qdata.headerdata[index]
                c.isVisible = not c.isVisible 
                chartWin.drawChart()
                pass
            return wrapper
        
        self.menu_display.clear()
        i = 0
        for lineName in self.qdata.getLinesNames():
            action = QAction(lineName, self)
            action.setCheckable(True)
            action.setChecked(True)
            self.connect(action, SIGNAL("triggered()"), togglePlot(i, self))
            self.menu_display.addAction(action)
            
            i += 1
        
        
    def linkWithChart(self, chartWin):            
        def wrapper():              
            lineNames = self.qdata.getLinesNames()
            def makeLineName(lineName):
                if lineName in lineNames:
                    i = 1
                    while (lineName + " %d" % i) in lineNames: i += 1
                    lineName += " %d" % i
                return lineName
              
            def find(a, row):
                for i in range(len(a)):
                    if a[i][0] == row[0]:
                        return i
            a, b = self.qdata.arraydata, chartWin.qdata.arraydata
            aDates = [row[0] for row in a]
            for i in range(len(b)):
                j = find(a, b[i])
                if j is not None:
                    b[i] = b[i] + [a[j][k] for k in range(1, len(a[0]))]
                else:
                    
                    b[i] = b[i] + ['' for k in range(1, len(a[0]))]
            
            bDates = [row[0] for row in b]  
            for row in a:
                if row[0] not in bDates:
                    b.append([row[0]]\
                             +['' for i in range(1, len(b[0]))]\
                             +[row[i] for i in range(1, len(a[0]))])
            headerData = self.qdata.headerdata        
            self.qdata = QChartData(len(b))
            self.qdata.arraydata = b
            for h in chartWin.qdata.getLinesNames()[1:]:
                headerData.append(QChartDataHeader(makeLineName(h)))
            self.qdata.headerdata = headerData
            for h in self.qdata.headerdata:
                h.isVisible = True
            
            self.drawChart()
            self._menuToggle()
        return wrapper
        
    def resizeEvent(self, event):
        size = event.size()
        self.dwidth, self.dheight = size.width(), size.height()
        self.drawChart()
                    
    def drawChart(self):
        self.webview = QtWebKit.QWebView() 
        headerdata = '"'+','.join([title[2:len(title)-1] for title 
                                   in [repr(title) for title in self.qdata.getLinesNamesToDisplay()]])+'\\n"'
        
        html = u'''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<script type="text/javascript" src="dygraph-combined.js"></script>
</head>
<body>
          <div id="graphdiv" style="position:absolute;"></div>
          <script type="text/javascript">
            g = new Dygraph(
              document.getElementById("graphdiv"),
              %s+%s,
              {width: %s, height:%s}
            );
          </script>
</script>
</body>
</html>
''' % (headerdata, self.qdata.getDataToDisplay(), self.dwidth - 30, self.dheight - 50)
        file = open(dataPath('dygraph.html'), 'w')
        file.write(html)
        file.close()
        self.webview.setUrl(QUrl(dataPath('dygraph.html')))
        self.setCentralWidget(self.webview)
            
    def _print(self):
        dialog = QPrintDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            printer = dialog.printer()
            self.webview.print_(printer)   
            
    def saveAsImage(self):
        #import win32api, win32con
        #win32api.keybd_event(win32con.VK_SNAPSHOT, 1)
        
        path = unicode(QFileDialog.getSaveFileName(self, 
                    u'Сохранить файл',
                    "c:/temp/chart.jpg", # blabla.png is lost
                    "JPG (*.jpg)"))
             
        if path:
            rect = self.geometry()
            img = ImageGrab.grab([rect.left(), rect.top()+25, rect.right(), rect.bottom()])
            img.save(path,'JPEG')
        
    def closeEvent(self, e):
        chartWinsRegister().unregister(self)
        e.accept()