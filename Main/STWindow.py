import sys
import threading
import math
import numpy as np

from datetime import datetime, timedelta, date, time
import random


from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout
from PyQt5 import uic 
from PyQt5.QtCore import *
from PyQt5.QtCore import QThread, QBasicTimer, QTimer


from GUI.ChartSettingController import ChartSettingController
from GUI.ChartController import ChartController
from GUI.View.MainWindow import MainWindow
from GUI.View.TrainingWindow import TrainingWindow
from GUI.View.Chart import Chart

from CheckGroup import CheckGroupManager
from PossessedGroup import PossessedGroup

from Common.GlobalLogging import LogManager
logMgr = LogManager("Main.MainWindowController")
logger = logMgr.logger

class Worker(QThread):
    def run(self):
        #threading.current_thread().name = "UIUpdator"
        self.sleep(10)
        while True:
            if self.exiting :
                break
            self.callBack()
            self.sleep(1)


class STWindowManager():
    def __init__(self, onDraw, onExit, CompleterList, dataMgr):
        self.trainingMgr = None
        self.dataMgr = dataMgr
        
        self.app = QApplication(sys.argv)
  
        self.CompleterList = CompleterList
        
        self.AccountStocksList = None
        
        
        self.testWindow = MainWindow()
        self.testWindow.show()
        self.exitHandler = onExit
             
        self.CheckGroupManager = CheckGroupManager(self.testWindow.StockGroupComboBox , dataMgr, CompleterList)
        
        self.ChartSettingController = ChartSettingController(self.testWindow, dataMgr, CompleterList)
        self.ChartSettingController.OnSubmitEventHandlers.append(self.__OnSubmitChartSetting)
        self.Chart = Chart(self.testWindow)
        self.ChartController = ChartController(self.testWindow, dataMgr, self.Chart)
        
        self.PossessedGroup = None
        
        
        self.timer = QTimer(self.testWindow)
        
        self.timer.setInterval(1000)
        self.timer.timeout.connect(onDraw)
        self.testWindow.drawCallback = onDraw

    def __OnSubmitChartSetting(self,shcode, startDate, endDate):      
        self.ChartController.Init(shcode, startDate, endDate)

    def openPossessedGroup(self, targetStocks):
        if self.PossessedGroup is None:
            self.PossessedGroup = PossessedGroup(self.testWindow, self.dataMgr)
        self.PossessedGroup.Init(targetStocks)
        
    
    def openTrainingMgr(self):
        if not self.trainingMgr :
            self.trainingMgr = TrainingWindow(self.dataMgr)
        self.trainingMgr.show()      
        #self.resultUI.show()
        #QWidget 객체 역시 레퍼런스 카운터가 0이면 삭제된다. (창이 생겼다가 바로 꺼짐)

    def run(self):
        #self.worker.start()
        self.timer.start()
        exeResult = self.app.exec_()   
        
        #self.worker.exiting = True
        self.exitHandler()
        sys.exit(exeResult)
