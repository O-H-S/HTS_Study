from datetime import datetime, timedelta
import time, threading
from Common.GlobalLogging import LogManager

logMgr = LogManager("Main.DM.TM")
logger = logMgr.logger

class TimeManager:
    def __init__(self, dataMgr):
        self.dataMgr = dataMgr
           
        self.TimeSync_BaseHereTime = time.time()
        self.TimeSync_ServerDate = datetime.now()
        self.TimeSync_ServerTime = datetime.now()
        self.TimeSync_ServerDateTime = datetime.now()
        
        self.Timer = None
        self.dataMgr.AddMessageHandler("GetServerTime_Result", self.OnArriveResult)
        
    def UpdateTime(self, interval):
        self.Timer = threading.Timer(interval, self.UpdateTime, args=(interval,))    
        self.Timer.name = "TimeUpdating"
        self.Timer.start()
        self.dataMgr.SendMessageToManagerAsync("GetServerTime", (None, None))   
    
    def StopUpdate(self):
        if self.Timer is not None:
            self.Timer.cancel()
            self.Timer = None
     
    def GetServerTimeRaw(self):
        elapsedTime = time.time() - self.TimeSync_BaseHereTime
        return datetime.timestamp(self.TimeSync_ServerTime.time()) + elapsedTime
        
    def GetServerTime(self):
        elapsedTime = time.time() - self.TimeSync_BaseHereTime
        return (self.TimeSync_ServerTime + timedelta(seconds=elapsedTime)).time()
        
    def GetServerDate(self, includeTime = False):
        elapsedTime = time.time() - self.TimeSync_BaseHereTime
        if includeTime :
            return self.TimeSync_ServerDateTime + timedelta(seconds=elapsedTime)
            
        return self.TimeSync_ServerDate
    
    

    
    def OnArriveResult(self, args):

        print("[DataManager] 서버 시간 업데이트 완료 ", args[0],  args[1], args[2], args[3])
        self.TimeSync_BaseHereTime = args[0] + ((args[1] - args[0]) / 2)
        self.TimeSync_ServerDate = datetime.strptime (args[2], "%Y%m%d")
        self.TimeSync_ServerTime = datetime.strptime (args[3], "%H%M%S%f")
        self.TimeSync_ServerDateTime = datetime(self.TimeSync_ServerDate.year, self.TimeSync_ServerDate.month, self.TimeSync_ServerDate.day, self.TimeSync_ServerTime.hour, self.TimeSync_ServerTime.minute, self.TimeSync_ServerTime.second)
        
        #print(self.TimeSync_ServerDate, self.TimeSync_ServerTime)