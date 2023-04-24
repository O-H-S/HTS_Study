
from PyQt5.QtCore import QDate
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager

import re, time
from pandas import Series, DataFrame
import math

logMgr = LogManager("Main.GUI.ChartSettingCtrl")
logger = logMgr.logger



class ChartSettingController:
    def __init__(self, targetView, dataMgr, completerList):
        self.dataMgr = dataMgr
        self.targetView = targetView
        
        
        RecentSearch_Code = dataMgr.sqlMgr.GetMetaData("RecentSearch_Code")
        RecentSearch_StartDate = dataMgr.sqlMgr.GetMetaData("RecentSearch_StartDate")
        RecentSearch_EndDate = dataMgr.sqlMgr.GetMetaData("RecentSearch_EndDate")
        
        if RecentSearch_Code != None:
            targetView.Input_shcode.setText(RecentSearch_Code)
         
        targetView.Input_StartDate.setDate(QDate.currentDate().addYears(-3))
        targetView.Input_EndDate.setDate(QDate.currentDate())
        
        
        targetView.Btn_ShowChart.clicked.connect(self.__onPushShowPrice)
        
        
        self.OnSubmitEventHandlers = []
    
    def __getPriceInputs(self):
       return (self.targetView.Input_shcode.text(), self.targetView.Input_StartDate.dateTime().date(), self.targetView.Input_EndDate.dateTime().date()) 
    
    def __onPushShowPrice(self):       
        inputs = self.__getPriceInputs()
        shcode = inputs[0]
        startDate =  datetime(inputs[1].year(), inputs[1].month(), inputs[1].day())
        endDate = datetime(inputs[2].year(), inputs[2].month(), inputs[2].day())
        
        if not self.dataMgr.IsCodeAvailable(shcode):
            return
        
        for handler in self.OnSubmitEventHandlers:
            handler(shcode, startDate, endDate)
        
        self.dataMgr.sqlMgr.SetMetaData("RecentSearch_Code", shcode)
        self.dataMgr.sqlMgr.SetMetaData("RecentSearch_StartDate", startDate.strftime('%Y%m%d'))
        self.dataMgr.sqlMgr.SetMetaData("RecentSearch_EndDate", endDate.strftime('%Y%m%d'))
        
        
        
        
        
    
