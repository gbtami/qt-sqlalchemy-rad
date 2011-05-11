# -*- coding: utf-8 -*-
import os.path
import models

FOLDER_DATA = 'data'
FOLDER_TMP= os.path.join(FOLDER_DATA, 'tmp')
FOLDER_ICO = os.path.join(FOLDER_DATA, 'ico')
FOLDER_EXCEL_TEMPLATES = 'data/templates'

MIMEFileName = 'application/x-qt-windows-mime;value="FileName"'

def dataPath(path):
    return os.path.join(FOLDER_DATA, path)

def iconPath(icon):
    return os.path.join(FOLDER_ICO, icon)

def tmpPath(path):
    return os.path.join(FOLDER_TMP, path)

def getModels(): 
    return models

def i18n(text):
    return text