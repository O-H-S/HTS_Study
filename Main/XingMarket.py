from Trading.Market import Market, MarketState
from Common.GlobalLogging import LogManager
import struct
import time
from datetime import datetime
import datetime as dt
logMgr = LogManager("Main.DM.XingMarket")
logger = logMgr.logger

class XingMarket(Market):
    def __init__(self, xingController): #임시로 xingController는 datamanager가 된다
        super().__init__()
        self.Controller = xingController
        self.TimeManager = self.Controller.TimeManager # 여기서 timemanger은 동기화 되어있다고 전제함.
        

        self.PriceManager = self.Controller.PriceManager

        self._PriceTable = self.PriceManager.RealtimeCollector.CurPrices

        self.PriceManager.RealtimeCollector.OnUpdatePricesHandlers.append(self.__OnUpdatePricesFromManager)
        
        self.OrderManager = self.Controller.OrderManager
        

        self.MarketStartTime = dt.time(9,1,0) # 약간의 딜레이 필요
        self.MarketEndTime = dt.time(15,30,0)

        
        
    #override
    def Init(self):    
        super().Init()

        CH = self.Controller.GetChannel('JIF')
        CH.handlers.append(self.__changeState)
        
        self.__checkState()
    
    #override
    def Release(self):
    
    
        CH = self.Controller.GetChannel('JIF')
        CH.handlers.remove(self.__changeState)
    
        super().Release()
        
    #override
    def GetTime(self):
        return self.TimeManager.GetServerTime()
    
    #override, 수정 필요
    def GetCurrentPrices(self, shcodeList):
        return self.PriceManager.GetRecentPrice(shcodeList)
    
    
    def __OnUpdatePricesFromManager(self, prices):
        self._UpdatePrices(prices)

    #override 
    def _OnListenerChange(self, listener, targetCode, inOrOut):
        if targetCode is None:
            return
        if inOrOut:
            self.PriceManager.RealtimeCollector.Register(targetCode)
        else:
            self.PriceManager.RealtimeCollector.Unregister(targetCode)

    def __checkState(self): # 프로그램이 장 중간에 켜질 경우에 대한 처리

        curTime = self.TimeManager.GetServerTime()
        curDate = self.TimeManager.GetServerDate()
        if not(self.MarketStartTime <= curTime and curTime < self.MarketEndTime):
            self._SetState(MarketState.CLOSE, False)                   
        else:
            lastPriceKospi = self.PriceManager.GetSectorPrice_Tick('001', 1, 1)

            dateString = lastPriceKospi.iloc[0]['date']

            lastDate = datetime.strptime (dateString, "%Y%m%d")

            if lastDate.day == curDate.day and lastDate.month == curDate.month:
                self._SetState(MarketState.OPEN, False)
            else:
                self._SetState(MarketState.CLOSE, False)
    
    def __changeState(self, data):

        def strCasting(byteValue):
            byteValue = byteValue.rstrip(b'\x00')
            return byteValue.decode(encoding='utf-8') 
            
        gubun = strCasting(data[0])
        state = strCasting(data[1])
        
        if gubun == '1' or gubun == '2':
            if state == '21':
                self._SetState(MarketState.OPEN)
                #self.OrderManager.OrderStocks('293480', True , 19500, 1)
            elif state == '41':
                self._SetState(MarketState.CLOSE)
