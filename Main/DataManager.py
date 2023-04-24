import subprocess
import threading
import time, os, signal
import math
from pandas import Series, DataFrame
import mmap
import struct, psutil
import sys
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Common.Command import Command, SyncCommand, WaitingCommands
from Common.SearchLine import SearchLine

from sqlMgr import SQLManager
from multiprocessing.managers import BaseManager, SyncManager
import inspect


from DataManagement import *

from Common.ThreadPool import ThreadPoolExecutorStackTraced as ThreadPoolExecutor

from Common.GlobalLogging import LogManager

logMgr = LogManager("Main.DM")
logger = logMgr.logger
class ChannelReceiver:
    def __init__(self, name, memName,blockSize, maxCount, memLength, memFormat):
        self.name = name
        self.blockSize = blockSize
        self.maxCount = maxCount
        self.memName = memName
        self.mem = mmap.mmap(-1, memLength, memName)
        self.mem.seek(0)
        self.dataList = []
        self.handlers = []
        self.memFormat = memFormat
        
    def Release(self):
    
        
        self.mem.close()
        self.mem = None
    
    
    def Receive(self, index):
    
        memStartPos = index * self.blockSize
        memCurPos = self.mem.tell()
        
        if memCurPos != memStartPos:
            self.mem.seek(memStartPos)
        
        rawBytes = self.mem.read(self.blockSize)
        unpackedData = struct.unpack(self.memFormat, rawBytes)
        
        for handler in self.handlers:
            handler(unpackedData)

        #print("(Receive)", unpackedData[0].decode(encoding='utf-8'))

class DataManager:
    DayPriceTableFormat = "Price_Day_{0}"
    DayPriceSearchTableFormat = "Search_Price_Day_{0}"
    
    def __init__(self):       
        self.serverConnectedCallback = None
        self.connectingServer = False
        self.serverConnected = False
        
    
        self.OpenManager()
        
        
        self.StartXingProcess()
        
        self.InitFinishCallback = []
        self.Inited = False
        self.isClosing = False
        
        
        self.AccInfoUpdatingTimer = None
        self.OnLoadAccountStocksEvent = []
        self.Input_AccPass = ""
        self.AccInfo = None
        self.AccStocks = None
        self.AccNo = ""
        
        
        self.messageHandlers = {}
        self.ChannelReceivers = {}
        
        self.OrderManager = OrderManager(self)
        self.TimeManager = TimeManager(self)
        self.GroupManager = GroupManager(self)
        self.ReportManager = ReportManager(self)
        self.StockEvaluater = StockEvaluater(self, self.ReportManager)
        self.PriceManager = PriceManager(self)
        
        self.OnDisableEventHandlers = []
        self.OnEnableEventHandlers = []
        self.Enable = False
        
        self.MessageThreadPool = ThreadPoolExecutor(None, thread_name_prefix='DM.Message')
        self.HandlerThreadPool = ThreadPoolExecutor(None, thread_name_prefix='DM.Handler')
    def Close(self):
        
        if self.AccInfoUpdatingTimer is not None:
            self.AccInfoUpdatingTimer.cancel()
            self.AccInfoUpdatingTimer = None
        self.TimeManager.StopUpdate()
        self.isClosing = True
        self.manager_serverObject.stop_event.set()
        SyncCommand.EndAll()
        #stop_timer = threading.Timer(1, lambda:self.manager_serverObject.stop_event.set())
        #stop_timer.start()
        self.sqlMgr.Close()
        
        
    def OnXingProcessDown(self, reason):
        self.Enable = False  
        
        for handler in self.OnDisableEventHandlers:
            handler()
            
        SyncCommand.EndAll()
        
        if self.AccInfoUpdatingTimer is not None:
            self.AccInfoUpdatingTimer.cancel()
            self.AccInfoUpdatingTimer = None
            
        self.TimeManager.StopUpdate()
        
            
        self.RemoveAllChannel()
        self.serverConnected = False
        self.connectingServer = False
        self.Inited = False
        self.isClosing = False

        
        logger.info("Xing process will be starting in 1 minutes")
        time.sleep(60)
        if not self.isClosing:
            self.StartXingProcess()
    
    
    
    def StartXingProcess(self):
        ip = self.manager_serverObject.address[0]
        port = self.manager_serverObject.address[1]

        self.subP = subprocess.Popen(r'activate py36_32 && cd C:\Users\OHS\Desktop\SystemTrading\XingManager && python main.py ' +  ip + " " + str(port) +r' && conda deactivate', 
        shell=True)
        
        def checkSubP():
            while True:
                result = self.subP.poll()
                if result is not None:
                    logger.info("Xing process is down, reason :{0}".format(result))
                    self.OnXingProcessDown(result)
                    break
                time.sleep(1)
                
                if self.isClosing :
                    logger.info("Watcher closing..")
                    break
        
        self.Watcher = threading.Thread(target = checkSubP, name="Watcher")
        self.Watcher.start()
        
        

        
    def Init(self):
        pass
        
    def Release(self):
        pass
        
    def ConnectToDB(self):
        self.sqlMgr = SQLManager("./DB/test.db")
        
    def ConnectToServer(self, ID, PASS, CERT_PASS, DART_KEY):
        self.connectingServer = True      
        
        self.ReportManager.ConnectToDart(DART_KEY)
        
        self.SendMessageToManager("Login", (ID, PASS, CERT_PASS))
     
    def GetAvailableDates(self, startDate, endDate):
        prices, _a, _b = self.PriceManager.StaticPriceCollector.GetPrice_Day('005930', startDate, endDate)
        transformedList = []
        for idx, value in prices['date'].items():
            transformedList.append(datetime.strptime (value, "%Y%m%d"))
        
        return transformedList
    def UpdateAccInfo(self, interval):
     
        continueTimer = True
        self.AccInfoUpdatingTimer = threading.Timer(interval, self.UpdateAccInfo, args=(interval,))
        self.AccInfoUpdatingTimer.name = "AccountUpdating"
        accNo = None
        accPass = self.Input_AccPass
        
        if accPass != "":
            try:
                self.SendMessageToManagerAsync("GetAccountInfo", (accNo, accPass))
            except:
                continueTimer = False
        if continueTimer:
            self.AccInfoUpdatingTimer.start() 
    
    def AddMessageHandler(self, name, handler):
        if name in self.messageHandlers:
            if not(handler in self.messageHandlers[name]):
                self.messageHandlers[name].append(handler)
        else:
            self.messageHandlers[name] = [handler]
            
    def OnChannel(self, name, index):    
        logger.debug("on channel {0}".format(name))
        targetReceiver = self.ChannelReceivers[name]
        targetReceiver.Receive(index)
        
        return True
    def GetChannel(self, name):
        if name in self.ChannelReceivers:
            return self.ChannelReceivers[name]
        return None
    def RemoveAllChannel(self):
        for key, value in self.ChannelReceivers.items():
            value.Release()
        self.ChannelReceivers = {}
    def OnMessage(self, name, args):
        self.messageProcessing = True
        
        if name == "RealtimeChannel":
            chName = args[0]
            chMemName = args[1]
            chBlockSize = args[2]
            chCount = args[3]
            chMemLength = args[4]
            chMemFormat = args[5]
            
            newReceiver = ChannelReceiver(chName, chMemName,chBlockSize,chCount,chMemLength, chMemFormat)
            self.ChannelReceivers[chName] = newReceiver
            
        elif name == "IPC_CON" :
            ip = args[0]
            port = args[1]
            self.ConnectManager(ip, port)
            
        elif name == "InitFinish":          
            self.Inited = True
            for cb in self.InitFinishCallback:
                cb()
                
        elif name == "LoginResult" :

            self.connectingServer = False
            
            result = args[0]
            code = args[1]
            reason = args[2]
            
            if result :
                self.serverConnected = True
                self.TimeManager.UpdateTime(60 * 5)
                self.UpdateAccInfo(60)
            self.HandlerThreadPool.submit(self.serverConnectedCallback, result, code, reason)

               
        elif name == "GetAllStock_Result" :
            metadata = args[0]
            print("[DataManager] 종목 데이터 읽는 중... (길이:", metadata['Length'],")(종목수:", metadata['Count'],")")
            mm = mmap.mmap(-1, metadata['Length'], metadata['MemName'])
            mm.seek(0)
            bytesOfStocks = mm.read(metadata['Length'])
            self.ReleaseMem(metadata['MemName'])
            print("[DataManager] 종목 데이터 읽기 완료")
            
            
            df = self.ReadByteByFormat(metadata, bytesOfStocks)
            #print(df)
            params = "name text, shcode text  PRIMARY KEY, expcode text , etf text, groupType text, spac text"
            creationQuery = self.sqlMgr.CreateTable("Stocks", params, True)
            
            if not self.sqlMgr.IsTableExists("Stocks"):
                self.sqlMgr.CreateTable("Stocks", params)
                self.sqlMgr.CreateIndex("Stocks_Index", "Stocks(expcode)")
            else:
                if self.sqlMgr.GetTableStructure("Stocks") != creationQuery:
                    print("새로운 구조의 [주식 특징] 테이블을 생성중입니다. 이전의 데이터들은 모두 사라집니다.")
                    if self.sqlMgr.IsIndexExists("Stocks_Index"):
                        self.sqlMgr.RemoveIndex("Stocks_Index")
                    self.sqlMgr.RemoveTable("Stocks")
                    self.sqlMgr.CreateTable("Stocks", params)
                    self.sqlMgr.CreateIndex("Stocks_Index", "Stocks(expcode)")
            
            self.sqlMgr.insert_conflict_ignore(df, "Stocks")
            
        
                
        elif name == "GetStockInfo_Result" :
            print("[DataManager] 주식 정보 가져오기 완료 ", args[1])
            print("상장일 :", args[2], " 결산월:", args[3])
            
            command = Command.Get(args[0])
            command.settleMonth = args[3]
            
            command.End()
        elif name == "GetAccountInfo_Result":

            
            
            metadata = args[-1]
            if not metadata['Result']:
                logger.warning("계좌 정보 불러오기 실패 {0}".format(metadata['Message'][2]))
                return True
                
                
            logger.debug("계좌 정보 업데이트 완료 ")
            self.AccInfo = tuple(args)
            self.AccNo = metadata["AccountNo"]
            logger.debug("[DataManager] 잔고 데이터 읽는 중... (길이:{0})(종목 수:{1})".format(metadata['Length'], metadata['Count']))
            
            df = None
            if metadata['Length'] > 0:
                mm = mmap.mmap(-1, metadata['Length'], metadata['MemName'])
                mm.seek(0)
                bytesOfStocks = mm.read(metadata['Length'])
                self.ReleaseMem(metadata['MemName'])
                df = self.ReadByteByFormat(metadata, bytesOfStocks)
                
            logger.debug("잔고 데이터 읽기 완료 ")
                
            self.AccStocks = df
            for handler in self.OnLoadAccountStocksEvent:
                handler()

            
        elif name == "GetStocksByState_Result" or name == "GetStocksByState2_Result"or name == "GetStocksByState3_Result":
            #print("[DataManager] 특정 상태 종목 가져오기 완료")
            logger.debug("[DataManager] 특정 상태 종목 가져오기 완료")
            metadata = args[-1]
            
            df = None
            #print("[DataManager] 종목 데이터 읽는 중... (길이:", metadata['Length'],")(종목 수:", metadata['Count'],")")
            logger.debug("[DataManager]  종목 데이터 읽는 중... (길이:{0})(종목 수:{1})".format(metadata['Length'],metadata['Count']))
            if metadata['Length'] > 0:
                mm = mmap.mmap(-1, metadata['Length'], metadata['MemName'])
                mm.seek(0)
                bytesOfStocks = mm.read(metadata['Length'])
                self.ReleaseMem(metadata['MemName'])
                df = self.ReadByteByFormat(metadata, bytesOfStocks)
            logger.debug("[DataManager] 종목 데이터 읽기 완료")
            
            
            
            #print(df)
            
            command = Command.Get(args[0])
            command.stocks = df
            
            command.End()
            
        if name in self.messageHandlers:
            handlers = self.messageHandlers[name]
            for handler in handlers:
                handler(args)
            
        self.messageProcessing = False
        return True
    def OpenManager(self):

        #print(inspect.getfile(SyncManager))

        SyncManager.register('OnMessageFromXing', self.OnMessage)
        SyncManager.register('RealtimeChannel', self.OnChannel)
        self.manager_server = SyncManager(address=('127.0.0.1', 0), authkey= b'123') # setting the port to 0 allows the OS to choose.
        self.manager_serverObject =  self.manager_server.get_server()
        #queue_manager.address
        #rint("start server : " , self.manager_serverObject.address)
        
        
        def serving():
            self.manager_serverObject.serve_forever()
            print("exit@@") #모듈 내부적으로 sys.exit가 호출된 상태이기 대문에 호출되지 않는다.
        
        thread = threading.Thread(target = serving, name="DM.Server")
        thread.start()
    
    def GetAccountStocks(self):
        return self.AccStocks['expcode'].tolist()
    
    def GetAccountStockRows(self):
        headers = ["종목코드", "등급" ,"종목명", "매입금액","평균단가", "수량" ,"평가손익", "수익률"]
        rows = []
        for idx, row in self.AccStocks.iterrows():
            grade = self.sqlMgr.GetAllRow("StocksGrade", selectQuery = "grade, reason", whereQuery= " shcode =='{0}'".format(row['expcode']))
            if len(grade) == 0:
                gradeText = " "
            else:
                gradeText = "{0} - {1}".format(grade[0][0], grade[0][1])
            rows.append((row['expcode'], gradeText,row['hname'],row['mamt'],row['pamt'] , row['janqty'] ,row['dtsunik'], row['sunikrt']))
        return (headers, rows)
    
    
    
    def ConnectManager(self, ip, port):    

    

        SyncManager.register('OnMessageFromMain')

        self.manager = SyncManager(address=(ip, port), authkey=b'XingManager')
        self.manager.connect()

        
          
    def SendMessageToManagerAsync(self, name, args):
        def AsyncSending():
            try:
                self.manager.OnMessageFromMain(name, args)
            except Exception as e:
                logger.error("sending error: {0}".format(e))               
        #threading.Thread(target = AsyncSending).start()
        self.MessageThreadPool.submit(AsyncSending)
        
    def SendMessageToManager(self, name, args):
        
        if self.messageProcessing :
            def AsyncSending():
                try:
                    self.manager.OnMessageFromMain(name, args)
                except Exception as e:
                    logger.error("sending error2: {0}".format(e))
            #threading.Thread(target = AsyncSending).start()
            self.MessageThreadPool.submit(AsyncSending)
            return
        
        self.manager.OnMessageFromMain(name, args)
        
    def SendMessageToManagerSync(self, name, args):
        try:
            self.manager.OnMessageFromMain(name, args)
        except Exception as e:
            logger.error("sending error3: {0}".format(e))
        
    def GetStocksByState(self, jongchk, stateType = 1):
        Command_GSBS = SyncCommand()
        if stateType == 2:
            if not(1 <= jongchk and jongchk <= 9):
                jongchk = 1
            self.SendMessageToManagerAsync("GetStocksByState2", (Command_GSBS.ID, jongchk))
        elif stateType == 3:
            self.SendMessageToManagerAsync("GetStocksByState3", (Command_GSBS.ID, jongchk))
        else:
            if not(1 <= jongchk and jongchk <= 4):
                jongchk = 1
            self.SendMessageToManagerAsync("GetStocksByState", (Command_GSBS.ID, jongchk))
        Command_GSBS.stocks = None
        #print("command start")
        Command_GSBS.Start()
        return Command_GSBS.stocks
    def GetStocksByGrade(self, grade):
        tableName = "StocksGrade"
        recentYQ = self.StockEvaluater.GetRecentYearQuater(self.TimeManager.GetServerDate(True))
        result = self.sqlMgr.GetAllRow(tableName, selectQuery = "shcode", whereQuery= " year == {0} and quater == '{1}' and grade == '{2}' ".format(recentYQ[0], recentYQ[1], grade))
        transformed = []
        for el in result:
            transformed.append(el[0])
        return transformed
    
    def GetBlackList(self, targetyear, quater, interval = 3600 * 24 * 7, targetList = None):
        #UpdateSettleMonth
        #UpdateAbnormal
        
        targetSet = None
        if targetList is not None:
            targetSet = set(targetList)
        
        quaterToMonth = {'1Q':3, '2Q':6, '3Q':9, '4Q':12}
        settleMonth = quaterToMonth[quater]
        
        params = "shcode text PRIMARY KEY, year integer, quater text, grade text, reason text, timestamp integer default -1"
        tableName = "StocksGrade"
        creationQuery = self.sqlMgr.CreateTable(tableName, params, True)
               
        if not self.sqlMgr.IsTableExists(tableName):
            self.sqlMgr.CreateTable(tableName, params)
  
        else:
            if self.sqlMgr.GetTableStructure(tableName) != creationQuery:
                print("새로운 구조의 [주식 등급] 테이블을 생성중입니다. 이전의 데이터들은 모두 사라집니다.")
                self.sqlMgr.RemoveTable(tableName)
                self.sqlMgr.CreateTable(tableName, params)
                
                
        
        
        curTime = int(time.time())
        expiredTime = curTime - int(interval)
        
        
        allCodeSet = None
        if targetSet is not None:
            allCodeSet = targetSet
        else:       
            allCode = self.GetGeneralStockList()
            allCodeSet = set(allCode)
        
        tableName = "StocksState"
        result = self.sqlMgr.GetAllRow(tableName, selectQuery = "shcode", whereQuery= " settleMonth !='{0}' or abnormal > 0".format(settleMonth))
        badStockList = []
        for st in result:
            badStockList.append(st[0])
        badStockSet = set(badStockList)
        
        tableName = "StocksGrade"
        result = self.sqlMgr.GetAllRow(tableName, selectQuery = "shcode", whereQuery= "( year == {0} and quater == '{1}') and timestamp > {2}".format(targetyear, quater, expiredTime))
        omitStockList = []
        for st in result:
            omitStockList.append(st[0])
        omitStockSet = set(omitStockList)
        if targetSet is not None:
            omitStockSet = omitStockSet - targetSet
        
        curYear = targetyear

        aliveStockSet = allCodeSet - (badStockSet.union( omitStockSet))
        
        blackList = list(badStockSet)
        blackTupleList = []

        for blackStock in blackList:
            blackTupleList.append((blackStock, targetyear, quater, 'B', '기본 조건 미달', curTime))
            
        self.sqlMgr.UpsertRowList( "StocksGrade(shcode, year, quater, grade, reason, timestamp)", "shcode" , blackTupleList) 
        blackList2 = []
        blackList3 = []

        
        
        

        
         
        
        print("업데이트 대상:", len(aliveStockSet))        
        for aStock in aliveStockSet:  
            print("Updating grade...", aStock)
            evaluatedResult = self.StockEvaluater.Evaluate(aStock,curYear,quater)         
            self.sqlMgr.UpsertRowList( "StocksGrade(shcode, year, quater, grade, reason, timestamp)", "shcode" , [(aStock, targetyear, quater, evaluatedResult['grade'], evaluatedResult['reason'], curTime)]) 
        
        '''
        headers = ["종목코드", "사유"]
        rows = []
        for shcode in blackList:
            rows.append((shcode, "기본 조건 미달"))           
        for shcode in blackList2:
            rows.append((shcode, "보고서 누락"))
        for shcode in blackList3:
            rows.append((shcode, "재무 위험 요인"))
        return (headers, rows)
        '''
            
            
    
    def UpdateSettleMonth(self, targetMonth, interval):
        params = "shcode text PRIMARY KEY, abnormal integer, settleMonth text default '', abnormal_Timestamp integer default -1, settleMonth_Timestamp integer default -1"
        tableName = "StocksState"
        creationQuery = self.sqlMgr.CreateTable(tableName, params, True)
               
        if not self.sqlMgr.IsTableExists(tableName):
            self.sqlMgr.CreateTable(tableName, params)
  
        else:
            if self.sqlMgr.GetTableStructure(tableName) != creationQuery:
                print("새로운 구조의 [주식 상태] 테이블을 생성중입니다. 이전의 데이터들은 모두 사라집니다.")
                self.sqlMgr.RemoveTable(tableName)
                self.sqlMgr.CreateTable(tableName, params)
            
    
        curTime = int(time.time())
        expiredTime = curTime - int(interval)
        result = self.sqlMgr.GetAllRow(tableName, selectQuery = "shcode", whereQuery= " settleMonth=='{0}' or settleMonth_Timestamp > {1}".format(targetMonth, expiredTime))
        finishedStockList = []
        for st in result:
            finishedStockList.append(st[0])
        finishedStockSet = set(finishedStockList)
        print("기존에 갱신된 종목들 : ", len(finishedStockSet))
        allCode = self.GetGeneralStockList()
        allCodeSet = set(allCode)
        
        unfinishedSet = allCodeSet - finishedStockSet
        
        Command_GSBS = SyncCommand()

        
        for st in unfinishedSet:
            Command_GSBS.settleMonth = None
            self.SendMessageToManagerAsync("GetStockInfo", (Command_GSBS.ID, st))
            result = Command_GSBS.Start()
            if result:
                self.sqlMgr.UpsertRowList( "StocksState(shcode, settleMonth, settleMonth_Timestamp)", "shcode" , [(st, Command_GSBS.settleMonth, curTime)])
        
        
        
        '''
        
        generalStockSet = set()
        abnormalSet = set()
        targetStockSet = generalStockSet - abnormalSet
        expiredStockSet = #from tableName
        requestStockSet = targetStockSet and expiredStockSet
        '''
        
   
    
    

    def UpdateStockStates(self): # 비정상 상태를 체크함.
        #테이블 생성 후(or Clear), 문제있는 종목 추가.
        result = self.GetGeneralStockList()
        #print(result)
        #if True:
        #    return
        
        params = "shcode text PRIMARY KEY, abnormal integer, settleMonth text default '', abnormal_Timestamp integer default -1, settleMonth_Timestamp integer default -1"
        tableName = "StocksState"
        creationQuery = self.sqlMgr.CreateTable(tableName, params, True)
        
        if not self.sqlMgr.IsTableExists(tableName):
            self.sqlMgr.CreateTable(tableName, params)
  
        else:
            if self.sqlMgr.GetTableStructure(tableName) != creationQuery:
                print("새로운 구조의 [주식 상태] 테이블을 생성중입니다. 이전의 데이터들은 모두 사라집니다.")
                self.sqlMgr.RemoveTable(tableName)
                self.sqlMgr.CreateTable(tableName, params)
            
    
        curTime = int(time.time())
    
        allCode = self.GetGeneralStockList()
        allCodeSet = set(allCode)
        
        #비정상 종목 구하기
        abnormalCounts = {}
        allStocks = []
        jongchkRanges = [4,9,1]
        for i in range(0, 3):
            stateType = i + 1
            for jongchk in range(1, jongchkRanges[i]+1):
                #print(stateType, jongchk)
                stocks = self.GetStocksByState(jongchk, stateType)
                if not(stocks is None):
                    allStocks.extend(stocks['shcode'].tolist())
        
        for abStock in allStocks:
            if abStock in abnormalCounts:
                abnormalCounts[abStock] = abnormalCounts[abStock] + 1
            else:
                abnormalCounts[abStock] = 1
        
        abnormalSet = set(allStocks)
        abnormalList = []
        for abnormalStock in abnormalSet:
            abnormalList.append((abnormalStock, abnormalCounts[abnormalStock], curTime))
        self.sqlMgr.UpsertRowList( "StocksState(shcode, abnormal, abnormal_Timestamp)", "shcode" , abnormalList)
        
        normalSet = allCodeSet - abnormalSet
        normalList = []
        for normalStock in normalSet:
            normalList.append((normalStock, 0, curTime))
        self.sqlMgr.UpsertRowList( "StocksState(shcode, abnormal, abnormal_Timestamp)", "shcode" , normalList)
        #stocksPossible = self.GetStocks("etf='0' groupType = '01' spac = 'N'")
        #
        '''
        for st in stocksSet:
            self.SendMessageToManagerAsync("GetStockInfo", (-1, st))
        '''
        
        
        
        
        
        
        
        
        # Gray 리스트 대상으로 결산일 업데이트
        # White 리스트 업데이트.
        #print(len(allStocks))
    def ReadByteByFormat(self, metadata, buffer):
        #print("RBBF", metadata)
        #print(metadata['Format'] * metadata['Count'])
        #print(struct.calcsize(metadata['Format'] * metadata['Count']))
        #unpackedData = struct.unpack(metadata['Format'] * metadata['Count'], buffer)
        #unpackedData = struct.iter_unpack(metadata['Format'], buffer)
        #for unpacked in struct.iter_unpack(metadata['Format'], buffer):
        #    print(unpacked)
        memberCount = len(metadata['MemberFormat'])
    
        subIndex = 0
        rows = []
        oneRow = []
        def strCasting(byteValue):
            byteValue = byteValue.rstrip(b'\x00')
            return byteValue.decode(encoding='utf-8')     
        def nothing(byteValue):
            return byteValue
        # str(b'sfsdfa') 의 출력 결과는 "b'sfsdfa'" 가 된다. 앞의 b가 문자로 포함되어버림.
        typeMapping = {"string": strCasting, "long":nothing, 'double':nothing ,"int":nothing}
        for unpacked in struct.iter_unpack(metadata['Format'], buffer):
            for element in unpacked:
                memFormat = metadata['MemberFormat'][subIndex % memberCount]
                try:
                    #oneRow[memFormat[0]] = typeMapping[memFormat[1]](element)   
                    if memFormat[1]:
                        oneRow.append( typeMapping[memFormat[1]](element))
                    else:
                        oneRow.append( element)
                except:
                    oneRow.append(None)
                    print("casting 오류")
                if subIndex % memberCount == memberCount - 1:
                    rows.append(oneRow)
                    oneRow = []
                subIndex = subIndex + 1
                       
        columnss = []
        for col in metadata['MemberFormat']:
            columnss.append(col[0])

        df = DataFrame(data = rows, columns = columnss)
        return df
    
    
    def GetStocks(self):
        pass
    
    
    
    
    
     
    def CheckTable(self, tableName, params):            
        creationQuery = self.sqlMgr.CreateTable(tableName, params, True)
        if not self.sqlMgr.IsTableExists(tableName):
            self.sqlMgr.CreateTable(tableName, params)
            return 0
        else:
            if self.sqlMgr.GetTableStructure(tableName) != creationQuery:
                logger.info("새로운 구조의 {0} 을 생성중입니다. 이전의 데이터들은 모두 사라집니다.".format(tableName))
                self.sqlMgr.RemoveTable(tableName)
                self.sqlMgr.CreateTable(tableName, params)
                return -1
        return 1
    
    def GetAccountInfo(self, accNo, accPass):
        self.SendMessageToManagerAsync("GetAccountInfo", (accNo, accPass))
    
   
    def IsCodeAvailable(self, shcode):
        result = self.sqlMgr.GetAllRow("Stocks", "shcode='{0}'".format(shcode))
        if len(result) > 0:
            return True
            
        return False
    
    def GetGeneralStockList(self):
        result = self.sqlMgr.GetAllRow("Stocks", selectQuery = "shcode", whereQuery= " etf=='0' and groupType == '01' and spac == 'N' and shcode LIKE '%0'")
        allStocks = []
        for stock in result:
            allStocks.append(stock[0])
        return allStocks

    
    def GetStocks(self, whereCondition):
        result = self.sqlMgr.GetAllRow("Stocks", whereCondition)
        return result
        
    def GetAllStockCode(self):

    
        result = self.sqlMgr.GetAllRow("Stocks", selectQuery = "shcode")
        allStocks = []
        for stock in result:
            allStocks.append(stock[0])
            

        
        return allStocks
      
    def GetAllStockName(self):
        result = self.sqlMgr.GetAllRow("Stocks", selectQuery = "name")
        allStocks = []
        for stock in result:
            allStocks.append(stock[0])
        return allStocks
      
      
    def GetStockInfo(self, shcode):
        result = self.sqlMgr.GetAllRow("Stocks", "shcode='{0}'".format(shcode))
        if len(result) <= 0:
            return None

        df = DataFrame(result, columns=self.sqlMgr.GetTableColumnNames("Stocks"))

        return df.iloc[0]
    
    
    
    def ReleaseMem(self, name):
        self.SendMessageToManagerAsync("System", ("ReleaseMem", name))
        
    



