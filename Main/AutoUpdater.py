import threading, time, random
from Common.GlobalLogging import LogManager
from DataManager import DataManager

from datetime import datetime, date, timedelta
logMgr = LogManager("Main.AutoUpdater")
logger = logMgr.logger


class AutoUpdater(threading.Thread):

    

    def __init__(self, dataMgr ):
        threading.Thread.__init__(self)
        self.name = "AutoUpdater"
        self.dataManager = dataMgr
        self.PriceManager = dataMgr.PriceManager 
        
        self.qReportListLock = threading.Lock()
        self.accountStocksInserted = False
        dataMgr.OnLoadAccountStocksEvent.append(self.__OnLoadAccountStocksHandler)      
        self.quaterReportUpdateList = []
        
        self.AutoPriceCollector = threading.Thread(target = self.__collectStockPrices, name="AutoPriceCollector")
    
    def __OnLoadAccountStocksHandler(self):
        self.dataManager.OnLoadAccountStocksEvent.remove(self.__OnLoadAccountStocksHandler)
        
        
        #accStockList=  self.dataManager.AccStocks['expcode'].values.to_list()
        accStockList=  self.dataManager.AccStocks['expcode'].to_list()
        self.qReportListLock.acquire()
        self.quaterReportUpdateList.extend(accStockList)

        self.qReportListLock.release()
      
    def __collectStockPrices(self):
        generalSet = set()
        collectedSet = set()
        
        #targetSet = generalSet - collectedSet의 결과는 uncollectedSet과 같다
        #for targetCode in targetSet:
        #   collectPrice(2015 ~ 2022):
        #   적당한 딜레이가 필요하다.(쉴새없이하면, xingprocess에서 다른 xingcommand를 실행할수없다)
        
        allCode = self.dataManager.GetGeneralStockList()
        random.shuffle(allCode)
        startDate = datetime(2013, 1, 1)
        endDate = self.dataManager.TimeManager.GetServerDate()
        endDate = endDate.replace(day = 1)   
        for targetCode in allCode:
            try:
                _a, _b, collected = self.PriceManager.StaticPriceCollector.GetPrice_Day(targetCode, startDate, endDate, returnPrices = False)
                if collected:
                    time.sleep(3)
                else:
                    time.sleep(0.5)
                    
            except:              
                print("AutoPriceCollector exited")
                break
            
        
      
    def CollectOrderData(self, startDatetime):
        orderMgr = self.dataManager.OrderManager
        
        holes = orderMgr.GetOrderDataHoles(startDatetime)
        #print(holes)
        
        def daterange(start_date, end_date):
            for n in range(int((end_date - start_date).days) + 1):
                yield start_date + timedelta(n)

        
        for hole in holes:
            startDatetime = datetime.fromtimestamp(hole[0])
            endDatetime = datetime.fromtimestamp(hole[1])
            start_date = startDatetime.date()
            end_date = endDatetime.date()
            for single_date in daterange(start_date, end_date):
                #print(single_date)
                orderMgr.GetOrderData(datetime(single_date.year, single_date.month, single_date.day))
                #dateString = single_date.strftime("%Y%m%d")
        
        
    
    def run(self):
        global logger
        try:
            logger.debug("Starting")
        
            oneHour = 60* 60
            oneDay = oneHour * 24
            oneMonth = oneDay * 30
        
            curTime = time.time()
            curTime_Int = int(curTime)
            orderMgr = self.dataManager.OrderManager

            self.CollectOrderData(datetime(2021, 11, 1))
            
            
            #비정상 종목 업데이트
            lastAbnormalUpdateTime = self.dataManager.sqlMgr.GetMetaData("LastAbnormalsUpdateTime")
            if lastAbnormalUpdateTime is None or int(lastAbnormalUpdateTime) + oneDay*7 < curTime_Int:
                logger.info("Updating abnormals...")
                self.dataManager.UpdateStockStates()
                self.dataManager.sqlMgr.SetMetaData("LastAbnormalsUpdateTime", curTime_Int)
                logger.info("Abnormals Updated!")
                
            allCode = self.dataManager.GetGeneralStockList()
            allCode.extend(self.quaterReportUpdateList)
            self.quaterReportUpdateList = allCode
            
            
            
            # 주식 등급 업데이트
            recentYQ = self.dataManager.StockEvaluater.GetRecentYearQuater(self.dataManager.TimeManager.GetServerDate(True))
            self.dataManager.GetBlackList(recentYQ[0], recentYQ[1])
            
            
            
            #분기보고서 업데이트
            #lastDartCallTime = 0
            reportManager = self.dataManager.ReportManager
            print("분기보고 업데이트 대상:", len(self.quaterReportUpdateList), recentYQ[0])
            while True:
                self.qReportListLock.acquire()
                count = len(self.quaterReportUpdateList)
                if count == 0 or reportManager.DartReader is None:
                    self.qReportListLock.release()
                    break
                    
                lastStock = self.quaterReportUpdateList.pop(-1)
                self.qReportListLock.release()
                logger.debug("분기보고서 업데이트 중.. {0}".format(lastStock))             
                reportManager.UpdateQuaterReport(lastStock, 2015, recentYQ[0], True) #연결 
                curTime = time.time()
                if reportManager.lastDartCallTime + 120.0 > curTime:                  
                    time.sleep((reportManager.lastDartCallTime + 120.0) - curTime)
                reportManager.UpdateQuaterReport(lastStock, 2015, recentYQ[0], False)# 별도
                curTime = time.time()
                if reportManager.lastDartCallTime + 120.0 > curTime:                 
                    time.sleep((reportManager.lastDartCallTime + 120.0) - curTime)
                    
                    
                    
        except Exception as e:
            logger.error("{0}".format( e))
            #raise

        

        
        
    def startUpdate(self, args):

        if not self.is_alive():
            self.start()
            self.AutoPriceCollector.start()
        