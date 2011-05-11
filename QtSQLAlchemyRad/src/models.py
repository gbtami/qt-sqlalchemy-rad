# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.orm import *
from qsr.model import Base, Titled, engine

class Genre(Base, Titled):
    __tablename__ = 'genre'
    __tabletitle__ = u'Жанры'
    id =  Column('id', Integer, primary_key=True, info={'title': u'#'})
    name = Column(Unicode(250), info={'title': u'Название жанра', 'minlength': 200})

    def __repr__(self):
        return self.name
    
class Review(Base, Titled):
    __tablename__ = 'review'
    __tabletitle__ = u'Рецензии'
    id =  Column('id', Integer, primary_key=True, info={'title': u'#'})
    movie_id = Column(Integer, ForeignKey('movie.id'))
    author = Column(Unicode(250), info={'title': u'Автор', 'minlength': 100})
    text = Column(UnicodeText, info={'title': u'Рецензия', 'minlength': 300})


class Movie(Base, Titled):
    __tablename__ = 'movie'
    __tabletitle__ = u'Фильмы'
    id =  Column('id', Integer, primary_key=True, info={'title': u'#'})
    name = Column(Unicode(250), info={'title': u'Название фильма', 'minlength': 200})
    date = Column(Date, info={'title': u'Дата выпуска'})
    imdb_rate = Column(Integer, info={'title': u'IMDB', 'minlength': 80})
    
    genre_id = Column(Integer, ForeignKey('genre.id'),  info={'title': u'Жанр', 'minlength': 150})
    genre = relation(Genre, backref=backref('genre', order_by=id))
    info = Column(UnicodeText, info={'title': u'Примечание', 'minlength': 500})
    
    def __repr__(self):
        return self.name

metadata = Base.metadata
metadata.create_all(engine()) 