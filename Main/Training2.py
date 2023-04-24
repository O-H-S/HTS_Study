import random
from datetime import datetime, time, timedelta
import threading
import matplotlib.ticker as ticker
import StrategyPack
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class Scenario:
    TimeTick = timedelta(hours=1)
    def __init__(self, startDate, endDate, traderCount = 1, name = None, dataMgr = None):
        
        self.OnFinishEvent = []
        
        self._availableDates = dataMgr.GetAvailableDates(startDate, endDate)
        self.StartDateTime = datetime.combine(self._availableDates[0].date(), Market.StartTime)
        self.EndDateTime = datetime.combine(self._availableDates[-1].date(), Market.EndTime)
        
        
        self.CurDateIndex = 0
        self.CurDateTime = self.StartDateTime
        self.Market = Market(self.CurDateTime, dataMgr)
        
        self.Traders = []
        
        if name is None:
            name = random.randint(0, 1000000)
        self.Name = name
        self.isRunning = False
        self.runningThread =  threading.Thread(target = self.__running, name="Scenario_{0}".format(self.Name))
        
        for i in range(traderCount):
            newTrader = Trader(10000000, StrategyPack.DefaultPack, dataMgr)
            self.AddTrader(newTrader)
            
        
        
        
    def GetProgress(self):
        stTimestamp = datetime.timestamp(self.StartDateTime)
        gap = datetime.timestamp(self.EndDateTime) - stTimestamp
        return (datetime.timestamp(self.CurDateTime)- stTimestamp) / gap
        
    def AddTrader(self, trader):
        self.Traders.append(trader)
        trader.joinToMarket(self.Market)

    def Run(self):
        if not self.isRunning:
            self.runningThread.start()
            self.isRunning = True
            return True
        return False
    

    
    def __running(self):

        print("running scenario...")
        timeStep = timedelta(hours = 6)
        
        
        self.Market.OnEnable()
        for td in self.Traders:
            td.OnEnable()
        
        while True:
            #print(self.CurDateTime)
            today_date = self.CurDateTime.date()
            curID = self.CurDateIndex
            
            
            self.Market.Open(self.CurDateTime)
            
            closeDatetime_Today = datetime.combine(today_date, Market.EndTime)
            while True:
                self.CurDateTime = self.CurDateTime + timeStep
                if self.CurDateTime >= closeDatetime_Today:
                    self.CurDateTime = closeDatetime_Today
                    break
                self.Market.Update(self.CurDateTime)
            
            
            self.CurDateIndex = self.CurDateIndex + 1
            if self.CurDateIndex == len(self._availableDates):             
                self.CurDateTime = self.EndDateTime
                self.Market.Close(self.CurDateTime) 
                break
                
            
            self.Market.Close(self.CurDateTime) 
            self.CurDateTime = datetime.combine(self._availableDates[self.CurDateIndex].date(),Market.StartTime)
            
        for td in self.Traders:
            td.OnDisable()    
            
        self.Market.OnDisable()    
            
        print("scenario finished!!")   
       
        for hand in self.OnFinishEvent:
            hand()
            
        
class Market: #거래소를 추상화함
    StartTime = time(9, 0)
    EndTime = time(15, 30)
    def __init__(self, lastDateTime, dataMgr):
        self.LastDateTime = lastDateTime
        self.onOpenEvent = []
        self.onCloseEvent = []
        self.onElapseTimeEvent = []
        
        self.CurPrices = {}
        self.AllStockCode = []
        self.AllStockSet = None
    
        self.dataMgr = dataMgr
        self.PriceManager = dataMgr.PriceManager
    
        self.Rates = self.PriceManager.StaticPriceCollector.GetRates(lastDateTime)

    
    def OnEnable(self):
        pass
    
    def OnDisable(self):
        pass
    
    #def ElapseTime(self, p
    
    def Update(self, marketDatetime):
        print("- (update)", marketDatetime)
        self.LastDateTime = marketDatetime
        for handler in self.onElapseTimeEvent:
            handler(marketDatetime)
        
    
    def Open(self, marketDatetime):
        print("[Open]", marketDatetime)
        # 해당 날짜의 가격들을 모두 불러온다.
        self.CurDateString = marketDatetime.strftime('%Y%m%d')
        self.CurPrices = self.PriceManager.StaticPriceCollector.GetPricesFromDate_Day(marketDatetime, marketDatetime) # timedelta(days = 2)
        self.AllStockCode =  self.CurPrices.index.get_level_values(0).tolist()
        self.AllStockSet = set(self.AllStockCode)
        self.LastDateTime = marketDatetime
              
        for handler in self.onOpenEvent:
            handler(marketDatetime)
    
    def Close(self, marketDatetime):
        print("[Close]", marketDatetime)
        self.LastDateTime = marketDatetime
        
        for handler in self.onCloseEvent:
            handler(marketDatetime)
    
    def IsStockTradable(self, shcode):
        targetPrice = self.CurPrices.loc[(shcode,self.CurDateString)]

        if targetPrice["high"] == targetPrice["low"]:
            return False
        return True
    
    def GetStockPrice(self, shcode):
        #a=self.CurPrices.loc[(shcode, self.CurDateString)]
        #b=self.Rates[shcode]
        if shcode in self.Rates:      
            return self.PriceManager.StaticPriceCollector.AdjustPrice(self.CurPrices.loc[(shcode, self.CurDateString)], self.CurDateString, self.Rates[shcode])
        return self.CurPrices.loc[(shcode, self.CurDateString)]   
    
    def GetRandomStock(self):      
        randID =  random.randint(0, len(self.AllStockCode)-1) #randint 함수는 마지막 값을 포함한다.
        return self.AllStockCode[randID]
        
''' 연산자 오버로딩 비용 많이 들듯, 보류
class Price:
    def __init__(self, price, baseDate):
        self.price = price
       self.baseDate = baseDate
'''
    
class Trader:
    수수료_세금 = 0.0033
    class Stock:
        def __init__(self, shcode, count, price):
            self.shcode = shcode
            self.count = count
            self.price = price
           
    def __init__(self, fund, rootStrategyClass, *strategyArgs, **strategyKargs):
        self.InitFund = fund # 초기 자금
        self.CurrentFund = fund # 현재의 자금, 이 값이 현재 가지고 있는 현금과 같다.
        
        self.RootStrategy = rootStrategyClass(self, *strategyArgs, **strategyKargs) # 전략은 tree 형식으로 연결되므로 root 전략만 가지면 된다.
        
        self.Stocks = {} 
        self.AveragePrice = {}
        self.GrossRealizedFund = 0   
        self.Market = None
        
        self.Profit_Date = []
        self.Profit_EstimatedFund = []
     
    def OnEnable(self):
        self.RootStrategy.OnEnable()
    
    def OnDisable(self):
        self.RootStrategy.OnDisable()
        

     
    def joinToMarket(self, market):
        self.Market = market
        market.onOpenEvent.append(self.onMarketOpen)
        market.onCloseEvent.append(self.onMarketClose)
        market.onElapseTimeEvent.append(self.onMarketTimeElapse)
    
    def BuyStock(self, shcode, price, count):
        needMoney = price*count
        if needMoney > self.CurrentFund:
            return False, 0
    
        newStock = Trader.Stock(shcode, count, price)
        if not( shcode in self.Stocks):
            self.Stocks[shcode] = [] 
            self.AveragePrice[shcode] = price
        else:
            allCount = self.GetStockCount(shcode)
            self.AveragePrice[shcode] =((price * count) + (self.AveragePrice[shcode] * allCount))/(allCount + count)
        self.Stocks[shcode].append(newStock)
        self.CurrentFund = self.CurrentFund - needMoney
        return True, needMoney
    
    def BuyStockByMoney(self, shcode, price, money):
        count = int(money/price)
        if count == 0:
            return False, 0, 0
            
        result, usedMoney = self.BuyStock(shcode, price, count)    
        return result, usedMoney, count
            
            
    def ShowProfits(self):  
        print("result porif")
        
        fig, ax = plt.subplots()
        
        #ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.xaxis.set_major_locator(ticker.AutoLocator())
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.plot(self.Profit_Date, self.Profit_EstimatedFund)
        ax.axhline(y=self.InitFund, color='r', linestyle='-')
        #ax.plot([1, 2, 3])
        fig.show()

        
    def hasStock(self, shcode):
        if shcode in self.Stocks:
            return True           
        return False
    
    def SellStock(self, shcode, price, count):
    
        removeList = []
        targetStocks = self.Stocks[shcode]
        curCount = 0
        for idx, stock in enumerate(targetStocks):
            if curCount + stock.count > count:              
                removeList.append((idx, stock, count - curCount))
                curCount = count               
            else:               
                removeList.append((idx, stock, stock.count))
                curCount = curCount + stock.count
                
            if curCount == count:
                break
                
        takenMoney = 0
        for rStock in removeList:
            targetStock = rStock[1]
            removingCount= rStock[2]
            
            targetStock.count = targetStock.count - removingCount
            if targetStock.count == 0:
                targetStocks.remove(targetStock)
            elif targetStock.count < 0:
                print("error sellstock")
            
        
        if len(targetStocks) == 0:
            del self.Stocks[shcode]

        
        
        #if curCount != count:
        #    print("warning")
        self.RealizedProfit = self.RealizedProfit + ((price-self.AveragePrice[shcode])*curCount *(1.0 - Trader.수수료_세금))
        self.CurrentFund = self.CurrentFund + ((price*curCount)*(1.0 - Trader.수수료_세금))
        return True, (price*curCount), curCount
    
    def SellStockByMoney(self, shcode, price, money):
        avePrice = self.GetAveragePrice(shcode)
        count = int(money/avePrice)
        if count == 0:
            return False, 0, 0
            
        result, takenMoney, soldCount = self.SellStock(shcode, price, count)    
        return result, takenMoney, soldCount

    
    
    def GetProfit(self, shcode):
        boughtPrice = self.GetStockBoughtPriceSum(shcode)        
        estimatedPrice = self.GetEstimatedStocks(shcode)
        ratio = (estimatedPrice/boughtPrice) - 1.0
              
        return ratio, estimatedPrice - boughtPrice
    
    def GetProfitByPrice(self, shcode, price):
        boughtPrice = self.GetStockBoughtPriceSum(shcode)
        estimatedPrice = self.GetEstimatedStocksByPrice(shcode, price)
        ratio = (estimatedPrice/boughtPrice) - 1.0
              
        return ratio, estimatedPrice - boughtPrice
    
    def GetStockCount(self, shcode):
        if shcode in self.Stocks:
            countSum = 0
            
            for stock in self.Stocks[shcode]:
                countSum = countSum + stock.count

            return countSum
        return 0 
    
    def GetAveragePrice(self, shcode):
        if shcode in self.Stocks:
            return self.AveragePrice[shcode]
        return 0        
      
    def GetEstimatedStocks(self, shcode):
        if shcode in self.Stocks:
            priceSum = 0          
            curPrice = self.Market.GetStockPrice(shcode)['close']
            for stock in self.Stocks[shcode]:
                priceSum = priceSum + (curPrice * stock.count)             
            return priceSum
        return 0   
        
    def GetEstimatedStocksByPrice(self, shcode, price):
        if shcode in self.Stocks:
            priceSum = 0          
            curPrice = price
            for stock in self.Stocks[shcode]:
                priceSum = priceSum + (curPrice * stock.count)             
            return priceSum
        return 0 
    
        
    def PrintStocks(self):
        stockManager = self.RootStrategy.StockManager
    
        print("_____[trader stocks]_____")
        boughtSum = 0
        for shcode in self.Stocks.keys():
            ratio, profit = self.GetProfit(shcode)
            boughtStock = self.GetStockBoughtPriceSum(shcode)
            boughtSum = boughtSum  + boughtStock
            avegPrice = self.GetAveragePrice(shcode)
            countSum = self.GetStockCount(shcode)
            curPrice = int(self.Market.GetStockPrice(shcode)['close'])
            firstBuyDate = stockManager.StocksData[shcode].FirstBuyDate.date()
            firstBuyPrice = int(stockManager.StocksData[shcode].FirstBuyPrice)
            print("[",shcode,"]", int(boughtStock),"|",int(self.GetEstimatedStocks(shcode)),"|",round(ratio*100, 2),"%, ",int(profit),"|",round(stockManager.GetStockPositionSize(shcode),2),'p|',int(avegPrice),"->",curPrice,"|",countSum,"주|",
            firstBuyDate,",", firstBuyPrice)
        print("총계 : ", int(boughtSum),",",int(self.CurrentFund),"/",int(self.GetEstimatedFund()), " 실현손익 :", int(self.RealizedProfit), "/",int(self.GrossRealizedFund))
        print("___________________________")
        
    def GetStockBoughtPriceSum(self, shcode):
        if shcode in self.Stocks:
            priceSum = 0          
            for stock in self.Stocks[shcode]:
                priceSum = priceSum + (stock.price * stock.count)             
            return priceSum
        return 0  
    
    def GetEstimatedFund(self):
        
        stocks = self.Stocks.keys()
        
        priceSum  = 0      
        for stock in stocks:
            priceSum = priceSum  + self.GetEstimatedStocks(stock)     
        return self.CurrentFund + priceSum
        
    def GetOriginalFund(self):
        stocks = self.Stocks.keys()     
        priceSum  = 0      
        for stock in stocks:
            priceSum = priceSum  + self.GetStockBoughtPriceSum(stock)     
        return self.CurrentFund + priceSum
    
    def onMarketOpen(self, openDateTime):
        self.RealizedProfit = 0
        self.RootStrategy.Start()
        
    def onMarketClose(self, closeDateTime):
        self.RootStrategy.End()
        self.GrossRealizedFund = self.GrossRealizedFund + self.RealizedProfit
        
        self.Profit_Date.append(self.Market.CurDateString)
        self.Profit_EstimatedFund.append(self.GetEstimatedFund())
        self.PrintStocks()
        
        
    def onMarketTimeElapse(self, dateTime):
        self.RootStrategy.Propagate()
        
class TransationRecord: # 트레이더의 각 주문 기록을 추상화한다. DB 저장시 트레이더 id를 외래키로 가진다.
# 트레이더 id, 주문 번호(각 트레이더 기준의 시간 순서) 쌍으로 식별한다.
    def __init__(self):
        pass
        




        
