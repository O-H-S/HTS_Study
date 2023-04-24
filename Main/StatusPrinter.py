
import threading
from Common.GlobalLogging import LogManager

logMgr = LogManager("Main.StatusPrinter")
logger = logMgr.logger



def PrintStatus( dataMgr):

    targetDF = dataMgr.AccStocks
    
    stocksSum = 0
    sunikSum = 0
    sunikSum2 = 0
    
    if targetDF is not None :
        sunikList = targetDF["dtsunik"].tolist() 
        for sunik in sunikList:
            stocksSum = stocksSum+1
            if sunik > 0:
                sunikSum = sunikSum + sunik
            else:
                sunikSum2 = sunikSum2 + sunik            
    
    dataMgrStatus = "<DataManager\t\t>: [Account Stocks<{0}> : {1} | {2}]".format(stocksSum, sunikSum, sunikSum2)

    timeMgr = dataMgr.TimeManager
    #timeMgrStatus = "<TimeManager\t\t>: [Active COrders : {0}]".format(len(orderMgr.GetActiveCOrders()))

    orderMgr = dataMgr.OrderManager
    orderMgrStatus = "<OrderManager\t\t>: [Active COrders : {0}]".format(len(orderMgr.GetActiveCOrders()))

    priceMgr = dataMgr.PriceManager 
    priceMgrStatus = "<PriceManager\t\t>: [Realtime({1}) : {0}]".format(priceMgr.RealtimeCollector.GetAllPackageSize(), priceMgr.RealtimeCollector.UpdatingCurPrices.is_alive())


    allThreadsName = []
    for thread in threading.enumerate():
        allThreadsName.append(thread.name)
    threadStatus = "<Threads : {0}>".format(" | ".join(allThreadsName))
 


    logger.info("--------------------------[Status]-----------------------------")
    
    logger.info(dataMgrStatus)
    logger.info(priceMgrStatus)
    logger.info(orderMgrStatus)
    
    logger.info(threadStatus)
    
    logger.info("----------------------------------------------------------------")