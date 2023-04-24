from pandas import Series, DataFrame
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager

import time

logMgr = LogManager("Main.DM.Agent")
logger = logMgr.logger

class Agent:
    def __init__(self, strategy):
        self.strategy = strategy
        self.Market = None
        
    def Join(self, market):
        self.Market = market
    
    #virtual
    def GetStocksInAccount(self):
        return []
        
    #virtual
    #def GetO
        
