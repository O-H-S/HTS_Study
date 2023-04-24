from pandas import Series, DataFrame
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager
from enum import Enum

import time

logMgr = LogManager("Main.DM.Market")
logger = logMgr.logger


class MarketState(Enum):
    UNKNOWN = 0
    CLOSE = 1
    OPEN = 2

class PriceListener:
    def __init__(self, shcode, client):
        self.targetCode = shcode
        self.client = client
        self.server = None
    
    def SetCode(self, code):    
        if self.server is not None:
            self.server.ChangeListenerCode(self, code)    
        self.targetCode = code

class Market:

    def __init__(self):
        self.State = MarketState.UNKNOWN
        self.Inited = False
        self.OnMarketStateChange = []
        self.OnMarketRelease = []
        
        
        self.OnPriceUpdate = []
        self.PriceListeners = {}
  
        self._PriceTable = None
        

    #virtual
    def Init(self):
        if self.Inited:
            logger.error("이미 초기화 되어 있음")

        self.State = MarketState.UNKNOWN
     
        self.Inited = True
    
    
        
    #virtual
    def Release(self):
        if not self.Inited:
            logger.error("이미 릴리즈 되어 있음")
    
    
        
        self.OnMarketStateChange = []
        self.OnPriceUpdate = []
        self.OnListenerChange = []
        for listener in self.PriceListeners.values():
            listener.server = None
        
        self.PriceListeners = {}
        
        for handler in self.OnMarketRelease:
            handler()       
        self.OnMarketRelease = []
        
        
        self.Inited = False
    #protected
    def _SetState(self, marketState, isEvent = True): # isEvent : 변화된 순간이면 True, 이전에 변화되었으나 시스템이 변화 시점을 놓쳐서 늦게 바꾼 경우에는 False 
        if self.State == marketState:
            return False
        #print("State changed : {0} -> {1}".format( self.State,marketState))
        logger.info("State changed : {0} -> {1} (event {2})".format( self.State, marketState, isEvent))
    
        for handler in self.OnMarketStateChange:
            handler(self.State, marketState, isEvent)
        self.State = marketState
        return True
    
    #virtual
    def GetTime(self):
        return None
    
    #virtual
    def GetCurrentPrices(self, shcodeList):
        return []
        
        
    def AddPriceListener(self, listner):
        targetCode = listner.targetCode
        if not(targetCode in self.PriceListeners):
            self.PriceListeners[targetCode] = []
        self.PriceListeners[targetCode].append(listner.client)
        listner.server = self
        
        self._OnListenerChange(listner, targetCode, True)
        
    def ChangeListenerCode(self, listener, newCode):
        oldCode = listener.targetCode
        self.PriceListeners[oldCode].remove(listner.client)
        if not(newCode in self.PriceListeners):
            self.PriceListeners[newCode] = []
        self.PriceListeners[newCode].append(listner.client)
        
        self._OnListenerChange(listner, oldCode, False)
        self._OnListenerChange(listner, newCode, True)
    
    def RemovePriceListener(self, listner):
        targetCode = listner.targetCode
        self.PriceListeners[targetCode].remove(listner.client)
        listner.server = None
        
        self._OnListenerChange(listner, targetCode, False)
            
    #protected 
    def _OnListenerChange(self, lister, inOrOut):
        pass
        
    #protected
    def _UpdatePrices(self, prices):

        updatedCodes = prices['shcode']
        
        for idx, code in updatedCodes.items():
            if code in self.PriceListeners:
                codePrice = 0
                targetRow = prices.loc[[idx]].iloc[0]
                for handler in self.PriceListeners[code]:                   
                    handler(targetRow)
        '''
        prices
    
        for handler in self.OnPriceUpdate:
       '''     
        
    
  
