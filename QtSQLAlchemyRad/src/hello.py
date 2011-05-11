# -*- coding: utf-8 -*-
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
import locale
locale.setlocale( locale.LC_ALL, "" )

from sqlalchemy import desc
from qsr.window import QSqlAlchemyTableWindow, QGeneralTableView, ModelSqlAlchemy
from qsr.model import orm
from qsr.conf import iconPath

from models import Movie, Review

class ReviewModel(ModelSqlAlchemy):
    def __init__(self, id, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.table = Review
        self.parent = parent
        self.parent_id = id
        self.update()  
    
    def query(self, offset=0, limit=10000):
        return orm().query(self.table).filter_by(movie_id=self.parent_id)\
            .limit(limit).offset(offset).all()
            
    def createItem(self, item):
        item.movie_id = self.parent_id
        return item
    

class MovieTableview(QGeneralTableView):
    def openContextMenu(self):
        menu = QMenu(self)
        reviews = QAction(u'Рецензии', self)        
        self.connect(reviews, SIGNAL("triggered()"), self.showReviews)
        menu.addAction(reviews)
        menu.addSeparator()
        
        QGeneralTableView.openContextMenu(self, menu)
        
    def showReviews(self):
        self.reviewsWindow = QSqlAlchemyTableWindow(Review, parent=self)
        self.reviewsWindow.setDatatable(ReviewModel(self.getFirstSelectedId(), self))
        movie = orm().query(Movie).filter_by(id=self.getFirstSelectedId()).one()
        self.reviewsWindow.setWindowTitle(str(movie))
        self.reviewsWindow.resize(QSize(500, 400))
        self.reviewsWindow.show()

QApplication.setStyle(QStyleFactory.create('Plastique'))
app = QApplication(sys.argv)

window = QSqlAlchemyTableWindow(Movie)
window.setTableView(MovieTableview)
window.setWindowIcon(QIcon(iconPath('catalog.png')))
window.show()
window.showMaximized()
window.setWindowTitle("Hello Movie Catalog Application")

sys.exit(app.exec_())