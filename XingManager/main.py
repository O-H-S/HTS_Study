import win32com.client
import sys

import pythoncom
import time, signal, struct

from multiprocessing import freeze_support
from multiprocessing.managers import BaseManager, SyncManager
from ipcMgr import IPCManager, RealtimeChannel
from apiMgr import APIManager


from TR import *


import threading
import random

from Common.GlobalLogging import LogManager

logMgr = LogManager("XingManager")
logger = logMgr.logger

logger.debug("Starting Process")



ipcMgr = None
apiMgr = None

def onMsg(name, args):
    global ipcMgr, apiMgr
    try:
        if name == "Login":
            apiMgr.Login(args[0], args[1], args[2])
        elif name == "GetAllStock":
            apiMgr.PushCommand(Command_XAQueryT8430.Create(args[0], args[1]))
        elif name == "GetPrice_Day":
            apiMgr.PushCommand(Command_XAQueryT8413.Create(args[3], args[0], args[1], args[2]))
        elif name == "GetServerTime":
            apiMgr.PushCommand(Command_XAQueryT0167.Create(-1))
        elif name == "GetAccountInfo":  
            account = args[0]
            if account is None:
                account = apiMgr.GetAccounts()[0]
                
            accPass = args[1]
            apiMgr.PushCommand(Command_XAQueryT0424.Create(-1, account, accPass))
            #apiMgr.PushCommand(Command_XAQueryCSPAQ13700.Create(-1, account, accPass, 'KR7206640005'))
            
            
           
            
        elif name == "GetStocksByState":  
            apiMgr.PushCommand(Command_XAQueryT1404.Create(args[0], args[1])) #0 commandID, 1 jongchk
        elif name == "GetStocksByState2":  
            apiMgr.PushCommand(Command_XAQueryT1405.Create(args[0], args[1])) #0 commandID, 1 jongchk   
        elif name == "GetStocksByState3":  
            apiMgr.PushCommand(Command_XAQueryT1410.Create(args[0])) #0 commandID, 1 jongchk 
        elif name == "GetStockInfo":
            apiMgr.PushCommand(Command_XAQueryT1102.Create(args[0], args[1])) #0 commandID, 1 shcode
        elif name == "GetOrderData":
            account = args[1]
            if account is None:
                account = apiMgr.GetAccounts()[0]           
            accPass = args[2]
            timestamp = args[3]
            apiMgr.PushCommand(Command_XAQueryCSPAQ13700.Create(args[0], account, accPass, timestamp)) #0 commandID, 
        elif name == "GetCurPrice":
            apiMgr.PushCommand(Command_XAQueryT8407.Create(args[0], args[1], args[2])) #0 commandID, 1 shcodeList, 2packedString
        elif name == "Order":
            account = args[1]
            if account is None:
                account = apiMgr.GetAccounts()[0]           
            accPass = args[2]
            
            cm = Command_XAQueryCSPAT00600.Create(args[0], accno = account, passwd = accPass, shcode = args[3], quantity=args[4], price=args[5], buyORsell=args[6])
            apiMgr.PushCommand(cm) 
        elif name == "GetSectorPrice_Tick":
        
            # shcode,   ncnt,   qrycnt,   nday,   edate
            # args[1], args[2], args[3],  0,     ,99999999
            apiMgr.PushCommand(Command_XAQueryT8417.Create(args[0], args[1], args[2], args[3], '0', '99999999'))
         
    except Exception as e:
            
        logger.error("error : {0}".format(e))
        raise


import mmap
def onFinishCommand(command, result):

    try:
        if type(command) is Command_XAQueryT8430:
            result = command.ToBytes()
            metadata = result[0]
            resultBytes = result[1]
            metadata["MemName"] = "AllStocks" + str(random.random())
            writeResult = ipcMgr.WriteToMem(metadata["MemName"], resultBytes, metadata["Length"])
            # 할당후 메모리 헤제를 해야함. close -> del enrty(in dictionary)
            ipcMgr.SendMessageToMain("GetAllStock_Result", (metadata, 3))
            
        elif type(command) is Command_XAQueryT8413:
            tr = command.inst
            result = command.ToBytes()
            metadata = result[0]
            resultBytes = result[1]
            metadata["MemName"] = "Price_Day" + str(random.random())
            writeResult = ipcMgr.WriteToMem(metadata["MemName"], resultBytes, metadata["Length"])

            ipcMgr.SendMessageToMain("GetPrice_Day_Result", (metadata, command.input_shcode, command.parent, command.complete))
            
        elif type(command) is Command_XAQueryT0167:
            tr = command.inst
            ipcMgr.SendMessageToMain("GetServerTime_Result", (command.startHearTime, command.endHearTime, command.date, command.time,command.parent))
        
        elif type(command) is Command_XAQueryT0424:
            tr = command.inst       
            resultFromCommand = command.ToBytes()
            metadata = resultFromCommand[0]
            resultByteList = resultFromCommand[1]
            
            

            def dataCheck(data):
                for element in data:
                    if element == '':
                        return False
                        
                return True
            if result and dataCheck([command.sunamt, command.dtsunik ,command.mamt ,command.tappamt ,command.tdtsunik]):     
                metadata["Result"] = True    
                metadata["MemName"] = "AccountInfo" + str(random.random())
                metadata["AccountNo"] = apiMgr.account_list[0]
                ipcMgr.WriteToMem(metadata["MemName"], resultByteList, metadata["Length"])
            else:
                metadata["Result"] = False
                metadata["Message"] = tr.resultMessage
            ipcMgr.SendMessageToMain("GetAccountInfo_Result", (command.sunamt, command.dtsunik ,command.mamt ,command.tappamt ,command.tdtsunik ,metadata ))
            
        elif type(command) is Command_XAQueryT1404:
            tr = command.inst       
            result = command.ToBytes()
            metadata = result[0]
            resultByteList = result[1]
            metadata["MemName"] = "GetStocksByState" + str(random.random())
            ipcMgr.WriteToMem(metadata["MemName"], resultByteList, metadata["Length"])
            ipcMgr.SendMessageToMain("GetStocksByState_Result", (command.parent, metadata ))
            
        elif type(command) is Command_XAQueryT1405:
            tr = command.inst       
            result = command.ToBytes()
            metadata = result[0]
            resultByteList = result[1]
            metadata["MemName"] = "GetStocksByState2" + str(random.random())
            ipcMgr.WriteToMem(metadata["MemName"], resultByteList, metadata["Length"])
            ipcMgr.SendMessageToMain("GetStocksByState2_Result", (command.parent, metadata ))
            
        elif type(command) is Command_XAQueryT1410:
            tr = command.inst       
            result = command.ToBytes()
            metadata = result[0]
            resultByteList = result[1]
            metadata["MemName"] = "GetStocksByState3" + str(random.random())
            ipcMgr.WriteToMem(metadata["MemName"], resultByteList, metadata["Length"])
            ipcMgr.SendMessageToMain("GetStocksByState3_Result", (command.parent, metadata ))
            
        elif type(command) is Command_XAQueryT1102:
            tr = command.inst
            ipcMgr.SendMessageToMain("GetStockInfo_Result", (command.parent, command.Input_shcode, command.listdate, command.gsmm))
        
        elif type(command) is Command_XAQueryCSPAQ13700:
            tr = command.inst       
            result = command.ToBytes()
            metadata = result[0]
            resultByteList = result[1]
            metadata["MemName"] = "GetOrderData_Result" + str(random.random())
            ipcMgr.WriteToMem(metadata["MemName"], resultByteList, metadata["Length"])
            ipcMgr.SendMessageToMain("GetOrderData_Result", (command.parent, metadata))
            
        elif type(command) is Command_XAQueryT8407:
            tr = command.inst       
            result = command.ToBytes()

            metadata = result[0]
            resultByteList = result[1]
            metadata["MemName"] = "GetCurPrice_Result" + str(random.random())
            ipcMgr.WriteToMem(metadata["MemName"], resultByteList, metadata["Length"])
            ipcMgr.SendMessageToMain("GetCurPrice_Result", (command.parent, metadata))
            
        elif type(command) is Command_XAQueryT8417:
            tr = command.inst       
            result = command.ToBytes()

            metadata = result[0]
            resultByteList = result[1]
            metadata["MemName"] = "GetSectorPrice_Tick_Result" + str(random.random())
            ipcMgr.WriteToMem(metadata["MemName"], resultByteList, metadata["Length"])
            ipcMgr.SendMessageToMain("GetSectorPrice_Tick_Result", (command.parent, metadata))
            
        elif type(command) is Command_XAQueryCSPAT00600:
            tr = command.inst
            if result:
                ipcMgr.SendMessageToMain("Order_Result", (command.parent, command.input_shcode))
            else:
                ipcMgr.SendMessageToMain("Order_Result", (command.parent, command.input_shcode))
    except Exception as e:
        logger.error("result error")
        logger.error("result error : {0}".format(e))
    
''' 
def exit_gracefully(signum, stack):
    print("signaled")
    #apiMgr.Close()
    #ipcMgr.Close()

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)   
#signal.signal(signal.SIGKILL, exit_gracefully)   
'''

import os
if __name__ == '__main__': 
    
 
    try:
        #print("myid2",os.getpid(), os.getppid())
        TargetData = {}
        
        
        ipcMgr = IPCManager(onMsg)
        ipcMgr.ConnectToManager(sys.argv[1], int(sys.argv[2]))
        
        TargetData["ipcMgr"] = ipcMgr

        apiMgr = APIManager(TargetData)
        apiMgr.CommandFinishHandler = onFinishCommand
        apiMgr.InitFinishEvent.wait()
        
        
        #============= 장운영정보 =============#
        
        MarketState_Command = Command_XARealJIF.Create(-1)
        chName = "JIF"
        JIF_Ch = RealtimeChannel(chName, 12, 10, '4s8s')
        def JIF_handler(data):   
            trans = struct.pack('4s8s', data[0].encode('utf-8').ljust(4, b'\0'), data[1].encode('utf-8').ljust(8, b'\0'))
            idx = JIF_Ch.Write(trans)
            #ipcMgr.SendToChannel(chName, idx) 
        MarketState_Command.handler = JIF_handler
        ipcMgr.RegisterChannel(JIF_Ch)
        apiMgr.PushCommand(MarketState_Command)
        
        #================================#
        
        
        ipcMgr.SendMessageToMain("InitFinish", None)
        #apiMgr.PushCommand(Command_XARealNWS.Create(-1))
       
        '''
        NWS_Command = Command_XARealNWS.Create(-1)
                     
        chName = "NWS"+ str(random.random())
        NWS_Ch = RealtimeChannel(chName, 100, 3, '100s')                   
        def nwsHandler(data):
            #print('handler]',data)
            idx = NWS_Ch.Write(data)
            #print('handler2]')
            ipcMgr.SendToChannel(chName, idx)     
            #print('handler3]')
        NWS_Command.handler = nwsHandler
        ipcMgr.RegisterChannel(NWS_Ch)
        apiMgr.PushCommand(NWS_Command)
        '''
        #apiMgr.PushCommand(NWS_Command)

        exiting = False
        # 고의적으로 크래쉬 일으키기
        '''
        time.sleep(8)
        def crash():
            try:
                crash()
            except:
                crash()

        crash()
        '''
        while not exiting :
            time.sleep(10)
            
            if not ipcMgr.thread.is_alive():
                logger.warning("ipcMgr thread is dead")
            
            #print(type(ipcMgr.SendMessageToMain("Ping", None)))
            try:
                ipcMgr.manager.OnMessageFromXing("Ping", None)._getvalue()
            except Exception as e:
                logger.warning("Ping exception: {0}".format(e))
                ipcMgr.Close()# 종료시 오류 발생, 차후에 서버 프로세스와 연결하지 않고 차근차근 오류 찾아보기.          
                apiMgr.close()
                #sys.exit(0)
                exiting = True
    except Exception as e:
        logger.error("main error")
        logger.error("main error : {0}".format(e))
                
        
        '''
        if ipcMgr.manager.Ping() != True:
            print("exiting")
            #sys.exit()
            print("exiting2")
            #apiMgr.Close()
        '''

    #print("all existed")
    
    

        



