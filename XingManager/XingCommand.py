import win32com.client
import pythoncom
import time
import threading
import struct
import sys
from pathlib import Path
from pandas import Series, DataFrame
import numpy, chardet

from Common.Command import Command
from Common.GlobalLogging import LogManager

logMgr = LogManager("XingManager.XingCommand")
logger = logMgr.logger


class XingCommand(Command):
    #def __init__(self, parentID = None):
    #    super.__init__(self, parentID, None)
    
    def IsReal(self):
        return False
    
    def OnPush(self):
        pass

    def Do(self):
        pass
        
    def OnFinish(self, result):
        pass

class XARealEventHandlerForCommand:
    # Proxy Method
    def OnReceiveRealData(self, code):       
        logger.debug('ReceiveRealData {0}'.format(code))
        #title= self.GetFieldData("OutBlock", "title")
        #print(title)

        result = self.callBack(code)
        self.handler(result)


class XAQueryEventHandlerForCommand:
    # Proxy Method
    def OnReceiveData(self, code):       
        
        logger.debug('OnReceiveData {0}'.format(code))
        self.callBack(code)
        
        self.pump = False      
        self.originClass.query_state = 1    
        self.resultCode = code
        self.resultData = True
       
        
    # Proxy Method
    def OnReceiveMessage(self, error, nMessageCode, szMessage):
        
        logger.debug('OnReceiveMessage {0} {1} {2}'.format(error, nMessageCode, szMessage))
        self.resultMessage = (error, nMessageCode, szMessage)
        #self.resultData = False      
        #self.pump = False      
        
class XingRealCommand(XingCommand):
    ResFileName = "Undefined"
    query_states = {}

    def IsReal(self):
        return True

    #override
    def OnPush(self):
        self.session = self.manager.XASession
      
    #override  
    def Do(self):
    
        originFileName = self.__class__.ResFileName
 
        self.inst = win32com.client.DispatchWithEvents("XA_DataSet.XAReal", XARealEventHandlerForCommand)

        
        self.inst.ResFileName = originFileName
        self.inst.originClass = self.__class__
        self.inst.pump = True
        self.inst.callBack = self.OnReceiveRealData
        self.inst.handler = self.handler
        self.inst.resultData = False
        
        self.Init()
        
        
        self.inst.AdviseRealData()

        
        while self.inst.pump :
            pythoncom.PumpWaitingMessages()
            #timeout 코드 추가 예정 return False
        
        self.inst.UnadviseRealData()

        return True
    
    def Stop(self):
        self.inst.pump = False
    
    #virtual 
    def Init(self):      
        pass
    
    #virtual
    def ToBytes(self):
        pass
        

    #virtual
    def OnReceiveRealData(self, code):
        pass

    def GetTRName(self):
        originFileName = self.__class__.ResFileName
        path = Path(originFileName)
        return path.stem    # test        




class XingQueryCommand(XingCommand):
    ResFileName = "Undefined"
    query_states = {}
    lastRequestTimes = {}
    #override
    def OnPush(self):
        self.session = self.manager.XASession
      
    #override  
    def Do(self):
        global logger
        try:

            originFileName = self.__class__.ResFileName
            __class__.query_state = 0
     
            self.inst = win32com.client.DispatchWithEvents("XA_DataSet.XAQuery", XAQueryEventHandlerForCommand)

            
            self.inst.ResFileName = originFileName
            self.inst.originClass = self.__class__
            self.inst.pump = True
            self.inst.callBack = self.OnReceiveData
            self.inst.resultData = False
            
            self.Init()
            
            self.WaitByLimit()
            
            #if requestCountsInTenMins
            
            reqResult, reqID = self.RequestSync(self.session)
            if not reqResult:
                return False
            
            timeout = False
            startingTime = time.time()

            self.SliceTimes()
            while self.inst.pump :
                #time.sleep(1000)
                pythoncom.PumpWaitingMessages()
                if startingTime + 10.0 < time.time():                 
                    timeout = True
                    break
                #timeout 코드 추가 예정 return False
            
            if timeout:
                logger.debug("tr timeout (reqID : {0})".format(str(reqID)))
                return False
            
            if self.inst.resultData and (self.inst.resultMessage[0] != 0 or self.inst.resultMessage[1][0:2] != '00'):
                return False
            
            
            while self.IsContinuous():
                self.inst.resultData = False
                self.inst.pump = True
                self.InitForContinuation()
                self.WaitByLimit()
                reqResult_Con, reqID_Con = self.RequestSync(self.session, True)
                if not reqResult_Con :
                    return False
                timeout = False
                startingTime = time.time()
                while self.inst.pump :
                    pythoncom.PumpWaitingMessages()
                    if startingTime + 10.0 < time.time():
                        logger.warning("tr timeout")
                        timeout = True
                        break
                
                if timeout:
                    return False
                if self.inst.resultData and (self.inst.resultMessage[0] != 0 or self.inst.resultMessage[1][0:2] != '00'):
                    return False
            
            return True
        except Exception as e:
            
            logger.error("tr do error : {0}".format(e))
            raise
            return False
     
    def WaitByLimit(self):
        '''
        print("TR NAME", self.GetTRName())
        print("GetTRCountPerSec ", self.inst.GetTRCountPerSec(self.GetTRName()))
        print("GetTRCountBaseSec ", self.inst.GetTRCountBaseSec(self.GetTRName()))
        print("GetTRCountRequest ", self.inst.GetTRCountRequest(self.GetTRName()))
        print("GetTRCountLimit ", self.inst.GetTRCountLimit(self.GetTRName()))
        '''
        
        trName = self.GetTRName()
        lastTime = self.GetLastRequestTime()
        
        
        delayPerRequest = self.inst.GetTRCountBaseSec(trName)
        #print("delayPerRequest", delayPerRequest)
        #delayPerRequest = 5
        
        
        countPerSec = self.inst.GetTRCountPerSec(trName)
        limitInTenMins = self.inst.GetTRCountLimit(trName)
        #limitInTenMins = 5
        
        #print("lastTime :" , lastTime)
        #print("custom, api : ", len(lastTimesInTenMins), requestCountsInTenMins)
        
        
        # sleep 함수 아래에서는 시간에 민감한 함수 배치에 유의해야한다.
        if lastTime + delayPerRequest >= time.time():
            needTime = (lastTime + delayPerRequest) - time.time() + 0.1
            #print("case 1) waiting... ", needTime)
            logger.debug("case 1) waiting... {0} ".format( needTime))
            #if trName != "t1102":
            time.sleep(needTime)
        
        lastTimesInSec = self.GetRequestsCountWithin(1)
        if countPerSec > 0 and len(lastTimesInSec) + 1 > countPerSec:
            needTime = lastTimesInSec[-1] - (time.time() - 1.0)  + 0.1
            logger.debug("case 2) waiting... {0} ".format( needTime))
            time.sleep(needTime)
        
        lastTimesInTenMins = self.GetRequestsCountWithin(60*10)  
        requestCountsInTenMins = self.inst.GetTRCountRequest(trName)
        if limitInTenMins > 0 and requestCountsInTenMins+1 > limitInTenMins:
            needTime = lastTimesInTenMins[-1] - (time.time() - 60*10)  + 0.1
            logger.debug("case 3) waiting... {0} ".format( needTime))
            #print(lastTimesInTenMins[-1], time.time())
            time.sleep(needTime)
            
        logger.debug("{0} wating info : {1} {2} {3} {4}".format(trName,
        countPerSec, delayPerRequest, limitInTenMins, requestCountsInTenMins))    
            
    #virtual 
    def Init(self):      
        pass
    
    #virtual
    def ToBytes(self):
        pass
        
    #virtual, 연속조회 구현시
    def IsContinuous(self):
        return False
    #virtual, 연속조회 구현시
    def InitForContinuation(self):
        pass
    #virtual 
    def CheckMessageResult(self, first, last):
        return True
       
    #virtual
    def OnReceiveData(self, code):
        pass

    def GetTRName(self):
        originFileName = self.__class__.ResFileName
        path = Path(originFileName)
        return path.stem    # test
        
    def RequestSync(self, session, continuation = False):
    

      
        # self.myself 로 지정하여 Request를 호출하는 이유
        # 이 클래스의 객체는 Proxy 타입으로 변환되어 사용된다.
        # 이때 이 메소드 정의에서 self.Request를 직접 입력하면, 이 클래스 타입의 Request 메소드를 호출하게됨. (하지만 정의되어 있지 않으므로 정상적인 동작 x)
        # self는 BaseTR 타입으로 간주하고, self.myself는 Proxy 타입으로 간주하여 동작의 차이가 발생됨.

        errcode =  self.inst.Request(continuation)
        self.PushRequestTime()
        if errcode < 0:

            logger.error("request err : {0} {1} ".format(errcode , session.GetErrorMessage(errcode)))
            return False
        
        return True, errcode
    def GetLastRequestTime(self):
        #print(type(self))
        
        if type(self) in XingQueryCommand.lastRequestTimes:
            requestTimes = XingQueryCommand.lastRequestTimes[type(self)]
            if len(requestTimes) == 0:
                return -1
            return requestTimes[-1]
        else:
            return -1
            
    def GetRequestsCountWithin(self, seconds):
        curTime = time.time()
        
        inTimes = []
        times = None
        if type(self) in XingQueryCommand.lastRequestTimes:
            times = XingQueryCommand.lastRequestTimes[type(self)]
            
        if not times:
            return inTimes
        
        count = 0
        
        for req in reversed(times):
            if curTime - seconds <= req:
                count = count + 1
                inTimes.append(req)
        return inTimes
        
    def SliceTimes(self):
        allCount = len(XingQueryCommand.lastRequestTimes[type(self)])
        if allCount > 1000:
            XingQueryCommand.lastRequestTimes[type(self)] = XingQueryCommand.lastRequestTimes[type(self)][-600:]
        
        
    def PushRequestTime(self):
        if type(self) in XingQueryCommand.lastRequestTimes:
            XingQueryCommand.lastRequestTimes[type(self)].append(time.time())
        else:
            XingQueryCommand.lastRequestTimes[type(self)] = [time.time()]