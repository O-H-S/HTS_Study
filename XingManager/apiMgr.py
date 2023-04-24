import win32com.client
import sys
import pythoncom
import time
import threading

import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Common.Command import Command


from Common.GlobalLogging import LogManager

logMgr = LogManager("XingManager.API")
logger = logMgr.logger

class XASessionEventHandler:
    login_state = 0
    def OnLogin(self, code, msg):
        XASessionEventHandler.login_state = 1
        logger.debug("OnLogin {0} {1}".format(code, msg))
        result = False
        if code == "0000":
            result = True          
        else:
            print(msg)
        self.result = result
        self.code = code
        self.msg = msg
        self.resultHandler((result, code, msg))

    def Disconnect(self):
        logger.warning("OnDisconnect")
        logger.warning("lasterror {0}".format(self.GetLastError()))
        
    def OnDisconnect(self):
        logger.warning("OnDisconnect2")
        logger.warning("lasterror {0}".format(self.GetLastError()))
        


class APIManager:
    def __init__(self, _targetData):   
        self.TargetData = _targetData
        self.XASession = None     
        self.Logged = False
        
        self.Commands = []
        self.mainThread =  threading.Thread(target = self.main, name="APIManager")
        self.mainThread.start()
        
        self.LoginLock = threading.Lock()      
        self.LoginLock.acquire()
        
        
        self.InitFinishEvent = threading.Event()
        
        self.CommandsLock = threading.Lock()
        self.CommandInEvent = threading.Event()
        self.CurrentCommand = None
        self.CommandFinishHandler = None
      
        self.RealCommandsOnStart = []
      
        self.account_list = None
    
    def close(self):

        self.unblock()
        '''
        if self.Logged:
            self.Logout()
            self.DisconnectServer()
        '''
    def isBlocked(self):
        if self.LoginLock.locked() :
            return True
        if not self.CommandInEvent.is_set():
            return True
        return False
            
    def unblock(self):
        if self.isBlocked():
            if self.LoginLock.locked() :
                self.LoginLock.release()
            if not self.CommandInEvent.is_set():
                self.CommandInEvent.set()
            
    def main(self):
        
        
        
        
        #Command 추출/ 수행 Loop
        try:
            pythoncom.CoInitialize()
            logger.info("로그인 대기 중..")
            
            self.InitFinishEvent.set()
            self.LoginLock.acquire()
            
            instXASession = win32com.client.DispatchWithEvents("XA_Session.XASession", XASessionEventHandler)
            instXASession.ConnectServer("hts.ebestsec.co.kr", 20001)
            instXASession.Login(self.LoginInput_ID, self.LoginInput_PASS, self.LoginInput_CERTPASS, 0, 0)
            instXASession.resultHandler = self.OnLoginResult
            self.XASession = instXASession
            
            
            logger.info("로그인 중..")
            
            
            while XASessionEventHandler.login_state == 0:
                pythoncom.PumpWaitingMessages()      
            # 로그인이 완료되면, 위의 루프를 빠져나온다.
            self.LoginLock.release()
            self.GetAccounts(True)
            
            def DoCommand(targetCommand, threading):
                
                if threading:    
                    pythoncom.CoInitialize()
                    self.RealCommandsOnStart.append(targetCommand)
                    logger.debug(" 리얼 커맨드 수행 :{0}".format(type(targetCommand)))
                else:
                    logger.debug(" 커맨드 수행 :{0}".format(type(targetCommand)))

                
                commandDoneResult = targetCommand.Do()
                logger.debug(" 커맨드 완료 :{0}".format(commandDoneResult))
                
                targetCommand.OnFinish(commandDoneResult)
                self.CommandFinishHandler(targetCommand, commandDoneResult)
                
                if threading:    
                    self.RealCommandsOnStart.remove(targetCommand)
                    pythoncom.CoUninitialize()
            
            while True:
                self.CommandsLock.acquire()
                if len(self.Commands) == 0:
                    logger.debug("수행할 커맨드를 기다리는 중 입니다.")

                    self.CommandsLock.release()
                    self.CommandInEvent.clear()
                    self.CommandInEvent.wait() 
                             
                if self.CommandsLock.locked() == False:
                    self.CommandsLock.acquire()     
                if len(self.Commands) == 0:
                    logger.debug("쓰레드 종료 중..")
                    break
                self.CurrentCommand = self.Commands.pop(0)
                self.CommandsLock.release()
                if self.CurrentCommand.IsReal():
                    
                    realThread = threading.Thread(target = DoCommand, args=[self.CurrentCommand, True],name="Command_Real")
                    realThread.start()
                else:
                    DoCommand(self.CurrentCommand, False)
                self.CurrentCommand = None
        except Exception as e:
            #print(e
            logger.error("Command 처리 예외 발생")
            logger.error("Command 처리 예외 발생 : {0}".format(e))
            raise
        finally:
        
            for rCommand in self.RealCommandsOnStart:
                logger.debug("리얼 커맨드 종료 : {0}".format(type(rCommand).__name__))
                rCommand.Stop()
            
            if self.Logged:
                self.XASession.Logout()
                self.XASession.DisconnectServer()
                logger.debug("로그아웃 /연결해제")
                
            
            
        
        pythoncom.CoUninitialize()
        
    def Login(self, ID, PASS, CERTPASS):
        
        self.LoginInput_ID = ID
        self.LoginInput_PASS = PASS
        self.LoginInput_CERTPASS = CERTPASS
        
        self.LoginLock.release()
        
    def OnLoginResult(self, result):
        if result[0]:
            self.Logged = True
        self.TargetData["ipcMgr"].SendMessageToMain("LoginResult", (result[0], result[1], result[2]))
    
    def GetAccounts(self, forceUpdate = False):
        if (self.account_list is None) or forceUpdate:
            self.account_list = []
            count = self.XASession.GetAccountListCount()
            for i in range(count):
                account = self.XASession.GetAccountList(i)
                self.account_list.append((account))
        
        return self.account_list
    
    def PushCommand(self, command):
        invokeEvent = False
        command.manager = self
        self.CommandsLock.acquire()
        
        if len(self.Commands) == 0:
            invokeEvent = True           
        self.Commands.append(command)
        command.OnPush()
        self.CommandsLock.release()
        if invokeEvent :
            self.CommandInEvent.set()
    
