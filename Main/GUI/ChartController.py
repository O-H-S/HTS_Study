from PyQt5.QtCore import QDate
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager

import re, time
from pandas import Series, DataFrame
import math

logMgr = LogManager("Main.GUI.ChartCtrl")
logger = logMgr.logger


class ChartController:
    def __init__(self, targetView, dataMgr, targetChart):
        self.dataMgr = dataMgr
        self.PriceManager = dataMgr.PriceManager
        self.targetView = targetView
    
        self.CurCode = None
        self.CurStartDate = None
        self.CurEndDate = None
        self.CurRatedDate = None
        
        
        self.TargetChart = targetChart
        self.TargetChart.OnMovedEventHandlers.append(self.__OnChartMoved)
        self.TargetChart.OnCreateCOMarkHandlers.append(self.__OnCreateCOMark)
        self.TargetChart.OnSaveCOMarkHandlers.append(self.__OnSaveCOMark)
        self.TargetChart.OnStartCOMarkHandlers.append(self.__OnStartCOMark)
    
    def Init(self, shcode, startDate, endDate):
        if self.CurCode is not None:
            self.Clear()
        
        self.TargetChart.Init()
        self.CurCode = shcode
        self.CurStartDate = startDate
        self.CurEndDate = endDate
        
        stockInfo = self.dataMgr.GetStockInfo(shcode)
        nameString = "{0}({1})".format(stockInfo['name'], shcode)
        self.TargetChart.SetName(nameString)
        self.TargetChart.SetPeriod(startDate, endDate)
        
        prices, self.CurRatedDate, _ = self.PriceManager.StaticPriceCollector.GetPrice_Day(shcode, startDate, endDate)
        
        self.TargetChart.AddPricesRight(prices)
        self.TargetChart.Axes.set_xlim([0, self.TargetChart.RightID])
        self.TargetChart.RelimY()
        
        '''
        self.TargetChart.Axes.relim(visible_only=True)
        
        self.TargetChart.Canvas.draw()
        '''
        orders = self.dataMgr.OrderManager.GetOrderDataFromStock(shcode)
        if orders is not None:
            self.TargetChart.AddOrders(orders)
        
        cOrders = self.dataMgr.OrderManager.GetCOrderFromCode(shcode)
        for co in cOrders:
            xIndex = self.TargetChart.DateToX[co.baseDate.strftime('%Y%m%d')] + co.offsetDays
            yValue = co.basePrice      

            mappedMark = self.TargetChart.createConditionOrderMark(xIndex, yValue, self)
            mappedMark.SetID(co.ID)
            mappedMark.SetDirty(False)
            mappedMark.SetBuyOrSell(co.buyORsell)
            mappedMark.SetStarted(co.started)
   
        self.TargetChart.Canvas.draw()    
        self.TargetChart.Canvas.setFocus()
            
            
    def __OnStartCOMark(self, mark, started):
        
        mappedCOrder, cr = self.dataMgr.OrderManager.GetCOrder(mark.ID)
        if mappedCOrder.started == started:
            return
        
        print(mark.ID,"] GUI trying to change started ->", started)
        print("(cur corder ",mappedCOrder.started,")")
        
        self.__OnSaveCOMark(mark)
        mappedCOrder.started = started
        if started :
            self.dataMgr.OrderManager.CheckCOrderActivation(mappedCOrder)
            mark.SetStarted(started)
        else:
            pass
            
        
    def __OnSaveCOMark(self, mark):
        #print("saved")
        mappedCOrder, cr = self.dataMgr.OrderManager.GetCOrder(mark.ID)
        basePrice = mark.GetPrice()
        rateDate = self.CurRatedDate
        mappedCOrder.SetPrice(basePrice, rateDate)
        
        pos = mark.GetPosition()
        baseDateIndex = self.TargetChart.RightID - 1
        baseDate = datetime.strptime (self.TargetChart.XToDate[baseDateIndex], "%Y%m%d")
        offsetDays = int(pos[0] - baseDateIndex)
        mappedCOrder.SetDate(baseDate, offsetDays)
        
        mappedCOrder.buyORsell = mark.buyORsell
        #mappedCOrder.started = mark.started
        
        self.dataMgr.OrderManager.ApplyConditionOrder(mappedCOrder)

    def __OnCreateCOMark(self, mark, caller):
        if caller == self.TargetChart:
            newOrder = self.dataMgr.OrderManager.CreateConditionOrder()
            newOrder.shcode = self.CurCode
            mark.SetID(newOrder.ID)
        elif caller == self:
            pass

    def __OnChartMoved(self,  old, new, delta):

        if delta < 0 and new[0] < self.TargetChart.LeftID:
            
            gap = self.TargetChart.LeftID - new[0]
            newSectionStart = self.CurStartDate - timedelta(days= int(gap * 1.2))
            newSectionEnd = self.CurStartDate - timedelta(days=1)
            
            prices, _, _v = self.PriceManager.StaticPriceCollector.GetPrice_Day(self.CurCode, newSectionStart, newSectionEnd)  

            if len(prices) > 0:
                self.TargetChart.AddPricesLeft(prices)
            self.CurStartDate = newSectionStart
            
            

    def Clear(self):
        self.TargetChart.Clear()