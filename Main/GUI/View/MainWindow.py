from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QWidget, QMainWindow, QApplication, QCompleter

import os

path = os.path.dirname(os.path.abspath(__file__))
form_class = uic.loadUiType( os.path.join(path, 'main.ui'))[0]


class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        
        #print(self.findChild(QWidget, "ConnectBtn"))
       
    def slot1(self):
        pass
    
   
    def onClickNewGroup(self):
        pass
    
    def setOnline(self, online):
        if online :
            self.ConnectionStat.setText("Online")
            self.Btn_ShowChart.setEnabled(True)
            self.ConnectBtn.setDisabled(True)
            self.Training_Btn.setEnabled(True)
        else :
            self.ConnectionStat.setText("Offline")
            self.Btn_ShowChart.setDisabled(True)
            self.ConnectBtn.setEnabled(True)
            self.Training_Btn.setDisabled(True)