from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QWidget, QMainWindow, QApplication, QCompleter
import os


path = os.path.dirname(os.path.abspath(__file__))
form_class, base_class = uic.loadUiType( os.path.join(path, 'empty.ui'))



class TestUI:
    def __init__(self, parent):
        rawForm = RawForm()
        self.mainWidget = rawForm.MainWidget
        
        if parent is not None:
            self.mainWidget.setParent(None)
        self.mainWidget.show()


class RawForm(base_class, form_class):
    def __init__(self):
        super().__init__()
       
        self.setupUi(self)