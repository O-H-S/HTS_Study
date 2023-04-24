from Common.Command import Command, SyncCommand
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager
from pandas import Series, DataFrame
import DataManagement.SearchLineController as SLC
import time
import mmap
from DataManagement.ConditionOrder import ConditionOrder
from Trading.Market import MarketState
logMgr = LogManager("Main.DM.OM")
logger = logMgr.logger

class OrderManager:
    def __init__(self, dataMgr):
        self.dataMgr = dataMgr
        self.dataMgr.AddMessageHandler("GetOrderData_Result", self.OnArriveResult)
        self.searchLine = None
        
        self.EnabledCOrders = {}
    
    def SetMarket(self, market):
        
    
        self.Market = market
        self.Market.OnMarketStateChange.append(self.__OnMarketStateChange)
        
        
        if self.Market.State == MarketState.OPEN:
            self.__CheckAllCOrderActivation()
        else:
            self.__CheckAllCOrderDeactivation()
    
    def __OnMarketStateChange(self, prev, current, isEvent):
        if current == MarketState.OPEN:
            self.__CheckAllCOrderActivation()
        else:
            self.__CheckAllCOrderDeactivation()
    
    def __CheckAllCOrderActivation(self):
        possibleOrders = self.__GetActivableCOrders() # Test code
        for pOrder in possibleOrders:  
            if pOrder.active:
                continue
            pOrder.Activate(self.Market)
            
    def CheckCOrderActivation(self, cOrder):
        print(cOrder.ID,"]CCA before active:", cOrder.active)
        if cOrder.active:
            return False
            
        curDate = self.dataMgr.TimeManager.GetServerDate()
        if self.Market.State == MarketState.OPEN:
            if cOrder.TestActivable(0, curDate):
                cOrder.Activate(self.Market)
    
    def __CheckAllCOrderDeactivation(self):
        # 현재 활동중인 모든 COrder을 구해옴
        for enabledOrder in self.EnabledCOrders.values():
            if enabledOrder.active:
                enabledOrder.Deactivate()
        
        
        
        
    def __GetActivableCOrders(self):
        self.CheckConditionOrderTable()
        
        curDate = self.dataMgr.TimeManager.GetServerDate()
        
        startedOrder = set()
        
        for enabledOrder in self.EnabledCOrders.values():
            if enabledOrder.TestActivable(0, curDate): # 임시 파라미터 설정됨
                startedOrder.add(enabledOrder)
        
        
        items = self.dataMgr.sqlMgr.GetAllRow("StockConditionOrder", whereQuery= " started == 1")
        df = DataFrame(items, columns=self.dataMgr.sqlMgr.GetTableColumnNames('StockConditionOrder'))
        for index, row in df.iterrows():
            enabled, creation = self.GetCOrder(row['ID'], row)
            if creation and enabled.TestActivable(0, curDate):
                startedOrder.add(enabled)
        return startedOrder
    
    def GetActiveCOrders(self):
        corders = []
        for enabledOrder in self.EnabledCOrders.values():
            if enabledOrder.active:
                corders.append(enabledOrder)
                
                
        return corders
    
    def CheckOrderTable(self):
        tableName = "StockOrder"
        params = "orderNo text, date text, orderTime text, execTime text, parentOrderNo text , buyORsell int, orderPrice real, orderQuantity int, execPrice real, execQuantity int, allExecQuantity int ,shcode text, primary key(orderNo, date)"
        self.dataMgr.CheckTable(tableName, params) 
        
    def CheckConditionOrderTable(self):
        tableName = "StockConditionOrder"
        params = "ID integer primary key, shcode text, started int, buyORsell int, basePrice real, ratedDate text, baseDate text, offsetDays int, limitWeight real"
        self.dataMgr.CheckTable(tableName, params) 

        # 해당 ID의 COrder row를 찾음.
        
        
    def CreateConditionOrder(self):

        self.CheckConditionOrderTable()
        # 테이블에 새로운 row를 추가함.     
        iparams = "shcode, started, buyORsell, basePrice, ratedDate, baseDate, offsetDays, limitWeight"              
        newID = self.dataMgr.sqlMgr.InsertOneRow( "StockConditionOrder", iparams, ['000000', 0, 0,0, '0' ,'0', 0, 0.0])       
        # 마지막에 추가된 rowid를 구해옴
        # 해당 rowid를 가지는 ConditionOrder 객체를 생성하고 활성화 상태로 변경함.
        newCO = ConditionOrder()
        newCO.Init(newID)
        self.EnabledCOrders[newID] = newCO
        return newCO
    
    def GetCOrder(self, ID, dataForEnable = None): # 새롭게 만들어졌다면 두번째 반환 값으로 True
        if ID in self.EnabledCOrders:
            return self.EnabledCOrders[ID], False
            
        if dataForEnable is not None:
            newCO = ConditionOrder()
            newCO.InitByRowData(dataForEnable)
            self.EnabledCOrders[dataForEnable['ID']] = newCO    
            return newCO, True
        return None, False
    
    def GetCOrderFromCode(self, shcode):
        self.CheckConditionOrderTable()
        orders = []
        items = self.dataMgr.sqlMgr.GetAllRow("StockConditionOrder", whereQuery= " shcode =='{0}'".format(shcode))

        df = DataFrame(items, columns=self.dataMgr.sqlMgr.GetTableColumnNames('StockConditionOrder'))
        for index, row in df.iterrows():
            orders.append(self.GetCOrder(row['ID'], row)[0])            
        return orders  
        #df['buyORsell'].replace({2:True, 1:False}, inplace=True)
    
    def ApplyConditionOrder(self, cOrder):
        
        iparams = "ID, shcode, started, buyORsell, basePrice, ratedDate, baseDate, offsetDays, limitWeight"     

        reatedDateValue = None
        if cOrder.ratedDate is not None:
            reatedDateValue = cOrder.ratedDate.strftime('%Y%m%d')
        started_int = int(cOrder.started == True)
        self.dataMgr.sqlMgr.UpsertRowList( "StockConditionOrder({0})".format(iparams), "ID", 
        [[cOrder.ID, cOrder.shcode, started_int, cOrder.buyORsell, cOrder.basePrice, reatedDateValue, cOrder.baseDate.strftime('%Y%m%d'), cOrder.offsetDays, 0.0]])
    
    def OrderStocks(self, shcode, buyORSell , price, quantity):
        accNo = None
        accPass = self.dataMgr.Input_AccPass

        self.dataMgr.SendMessageToManagerAsync("Order", (-1, accNo, accPass, shcode, quantity, price, buyORSell))
    
    def GetSearchLine(self):
        if self.searchLine is None:
            self.dataMgr.CheckTable("OrderData_SL", SLC.TableParams) 
            self.searchLine = SLC.LoadFromDB(self.dataMgr.sqlMgr, "OrderData_SL", 1)
        return self.searchLine
        
    def GetOrderDataHoles(self, startDatetime):

        orderDataSearchLine = self.GetSearchLine()
        
        rootTimestamp = datetime.timestamp(startDatetime)
        
        curTimestamp = time.time()
        curDatetime = datetime.fromtimestamp(curTimestamp)

        searchSection = (rootTimestamp, curTimestamp)
        holes = orderDataSearchLine.getHolesBySection(searchSection) 
        return holes
      
    def GetOrderDataFromStock(self, code):
    
        self.CheckOrderTable()
        items = self.dataMgr.sqlMgr.GetAllRow("StockOrder", whereQuery= " shcode =='{0}'".format(code))
        #print(code)
        #print(items)
        if len(items) == 0:
            return None
        df = DataFrame(items, columns=self.dataMgr.sqlMgr.GetTableColumnNames('StockOrder'))
        df['buyORsell'].replace({2:True, 1:False}, inplace=True)
        return df
    
    def GetOrderData(self, targetDatetime, commandProps = None):
              
        fromDB = self._getFromDB(targetDatetime)
        if fromDB is not None:
            return fromDB
        
        Command_GOD = SyncCommand()
        Command_GOD.Props = commandProps
        accNo = None
        accPass = self.dataMgr.Input_AccPass
        timestamp = datetime.timestamp(targetDatetime)
        self.dataMgr.SendMessageToManagerAsync("GetOrderData", (Command_GOD.ID, accNo, accPass, timestamp))

        result = Command_GOD.Start()
        
        if result:
            sl = self.GetSearchLine()
            today = datetime.now()
            current_dt = datetime.timestamp(today)
            if targetDatetime.year == today.year and targetDatetime.month == today.month and targetDatetime.day == today.day:
                sl.addSection((timestamp, current_dt))
            else: # 오늘이 아니면(과거이면)
                sl.addSection((timestamp, timestamp+86400 - 1))
                
            SLC.SaveToDB(self.dataMgr.sqlMgr, "OrderData_SL", sl)
        return self._getFromDB(targetDatetime)
    def _getFromDB(self, targetDatetime):

        self.CheckOrderTable()      
        return None
    def OnArriveResult(self, args):
        logger.debug("[DataManager] 주문 내역 메세지 결과 수신")
        metadata = args[-1]
        
        df = None
        logger.debug("[DataManager]  주문 데이터 읽는 중... (길이:{0})(주문 수:{1})".format(metadata['Length'],metadata['Count']))
        if  metadata["Result"] and metadata['Length'] > 0:
            mm = mmap.mmap(-1, metadata['Length'], metadata['MemName'])
            mm.seek(0)
            bytesOfStocks = mm.read(metadata['Length'])
            self.dataMgr.ReleaseMem(metadata['MemName'])
            df = self.dataMgr.ReadByteByFormat(metadata, bytesOfStocks)
        if metadata["Result"] :
            logger.debug("[DataManager] 주문 데이터 읽기 완료")
        else:
            logger.debug("[DataManager] 주문 데이터 읽기 실패")
        
        #print(df)
        #print(df)
        
        command = Command.Get(args[0])
        command.orders = df
        command.result = metadata["Result"]
        '''
        ("OrdDt", "string", 8*4), 
        ("OrdNo", "string", 10*4), 
        ("OrgOrdNo", "string", 10*4), 
        ("IsuNo", "string", 12*4), 
        ("BnsTpCode", "string", 1*4), 
        ("BnsTpNm", "string", 10*4), 
        ("OrdQty", "long", 4),
        ("OrdPrc", "double", 8),
        ("ExecQty", "long", 4),
        ("ExecPrc", "double", 8),
        ("ExecTrxTime", "string", 9*4), 
        ("LastExecTime", "string", 9*4), 
        ("AllExecQty", "long", 4),
        ("OrdTime", "string", 9*4)]
        '''
        if df is not None:
            orderList = []
            iparams = "orderNo, date, orderTime, execTime, parentOrderNo , buyORsell, orderPrice, orderQuantity, execPrice, execQuantity, allExecQuantity ,shcode"
            for idx, row in df.iterrows():
                orderList.append([row['OrdNo'],row['OrdDt'],row['OrdTime'],row['ExecTrxTime'],row['OrgOrdNo'],
                row['BnsTpCode'],row['OrdPrc'],row['OrdQty'],row['ExecPrc'],row['ExecQty'],row['AllExecQty'],row['IsuNo'][1:]])
                
            self.dataMgr.sqlMgr.UpsertRowList( "StockOrder({0})".format(iparams), "orderNo, date" , orderList)
        
        
        
            
        
        #print(df)
        command.End(metadata["Result"])
    