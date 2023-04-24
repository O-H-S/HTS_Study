
from .Strategy import Strategy

from datetime import datetime, time, timedelta
from enum import Enum


class StockState(Enum):
    SEA = 0
    GROUND = 1
    SKY = 2

class StockManager(Strategy):

    class StockData:
        def __init__(self, shcode, price, priceBaseDate, count ):
            self.shcode = shcode
            self.BuyCount = 1
            self.FirstBuyPrice = price
            self.FirstBuyDate = priceBaseDate
            self.FirstBuyCount = count
            self.LastBuyPrice = price
            self.LastBuyDate = None

            self.prevMaxPrice = 1
            self.prevLowPrice = price
            self.SellCount = 0
            self.LastSellPrice = None
            self.LastSellDate = None
            
            self.State = StockState.GROUND
            self.RepurchaseForProfit_Today = False
            self.LossCut_Today = False
        
        
        def InitByStart(self):
            self.RepurchaseForProfit_Today = False
            self.LossCut_Today = False
            #self.Cache_ProfitByClosePrice
        
        def GetCurrentProfitFromFirst(self, currentPrice):
            return ((currentPrice/self.FirstBuyPrice) - 1.0)
                   

    def __init__(self, trader, maxWeightPerStock = 0.05, maxPositionPerBuy = 0.2, evaluator = None):
        super().__init__(trader)

        self.maxPositionPerBuy = maxPositionPerBuy
        self.maxWeightPerStock = maxWeightPerStock
        
        self.Evaluator = evaluator
        
        self.maxPositionSize = 3.0
        self.maxLoss = 0.60
        self.firstPositionSize = 0.7
        
        
        
        
        self.sellRatioByProfits = 0.2 # 이익중인 평가금액 중 매도할 비율
        
        self.StocksData = {}

    def Start(self, buyFundLimit, sellFundLimit):
        self.Evaluator.Start()
    
        self.boughtFund = 0     
        self.soldFund = 0
        self.BuyFundLimit = buyFundLimit
        self.SellFundLimit = sellFundLimit
        
        self.CurOriginalFund = self.Trader.GetOriginalFund()
        self.FundPerPosition = (self.CurOriginalFund * self.maxWeightPerStock) / self.maxPositionSize
        self.maxBuyFund = self.FundPerPosition * self.maxPositionPerBuy
        
        self.targetStocks = []
        
        self.Cache_EstimatedFund = self.Trader.GetEstimatedFund()
        
        for sData in self.StocksData.values():
            sData.InitByStart()
        
        #self.needToSellProfits =  * self.sellRatioByProfits 
        
        print("StockManager Start)", int(self.maxBuyFund), int(self.FundPerPosition))
        print("limits ", buyFundLimit)
    
    def OnDisable(self):
        self.Evaluator.OnDisable()
    
    def __getPossiblePrice(self, shcode):
        pass
    
    def __getProperPositionSize(self, curLoss):
        if curLoss > self.maxLoss:
            return self.maxPositionSize
    
        b = self.firstPositionSize
        a = (self.maxPositionSize - self.firstPositionSize) / self.maxLoss       
        return (a * curLoss) + b
    
    def GetStockPositionSize(self, shcode):
        estimated = self.Trader.GetStockBoughtPriceSum(shcode)
        return estimated / self.FundPerPosition
    
    def End(self):
        self.Evaluator.End()
        #print("BuyManager End)", self.Fund, self.positionSize)
    
    def __resolveStrategy(self):
        pass
        
        
    # ======================================[차익 실현 로직]======================================================  
    def __Logic_TakingProfit(self):
        market = self.Trader.Market
        trader = self.Trader
        possibles = {}
        for possibleStockData in self.StocksData.values():
            shcode = possibleStockData.shcode
            
            
            if not market.IsStockTradable(shcode):
                continue
                
            curPrice = market.GetStockPrice(shcode)
            price_close = curPrice['close']
            curProfitRatio, curProfitFund  = trader.GetProfit(shcode)
            
            if possibleStockData.State == StockState.SKY: # 이미 sky인 종목들은 
                if not possibleStockData.RepurchaseForProfit_Today: #불타기 하지 않은 종목만이 차익 실현 대상이다.
                    possibles[shcode]= curProfitFund
                continue
    
            if curProfitRatio > 0.05:
                possibleStockData.State = StockState.SKY
                possibles[shcode]= curProfitFund              
                

        sorted_dict = sorted(possibles.items(), key = lambda item: item[1])
        print(sorted_dict)
        #-----
        for sPair in reversed(sorted_dict):   
            shcode = sPair[0]
            sData = self.StocksData[shcode]

            if self.Trader.RealizedProfit > self.Cache_EstimatedFund*0.002:
                continue
                
            needToSellCount = trader.GetStockCount(shcode) * self.sellRatioByProfits
            needCount = max(int(needToSellCount), 1)
            curPrice = market.GetStockPrice(shcode)
            if needCount > 0:            
                result, takenMoney, count  = self.Trader.SellStock(shcode, curPrice['close'], needCount)
                self.soldFund = self.soldFund + takenMoney
                if not trader.hasStock(shcode):
                    del self.StocksData[shcode]
                else:
                    sData.SellCount = sData.SellCount + 1
        
    # ======================================[신규 종목 편입 로직]====================================================== 
    def __Logic_NewStock(self):
        
        market = self.Trader.Market
        trader = self.Trader

        
        whiteListWithChange = {}
        whiteList = self.Evaluator.GetWhiteList()
        for whiteStock in whiteList:
            if (whiteStock in self.StocksData):
                continue
                
            if not market.IsStockTradable(whiteStock):
                continue
                
            curPrice = market.GetStockPrice(whiteStock)
            dropRate = (curPrice['close'] / curPrice['open'])  - 1.0
            if dropRate < -0.03:
                whiteListWithChange[whiteStock] = dropRate
        
        sorted_dict = sorted(whiteListWithChange.items(), key = lambda item: item[1])
        #print("white_soredt : ", sorted_dict)
        
        
        
        def Logic_NewStock2(targetCode):

            extraFund = self.BuyFundLimit[0] - self.boughtFund    
            if extraFund < 2000: # 
                return False
            usingMoney = min(extraFund, self.maxBuyFund)
            #usingMoney = min(extraFund, self.FundPerPosition)
            result, usedMoney, count  = self.Trader.BuyStockByMoney(targetCode, market.GetStockPrice(targetCode)['close'], usingMoney)
            self.boughtFund = self.boughtFund + usedMoney
            print("newMoney_sky", targetCode, result, usedMoney)
            if result:
                self.StocksData[targetCode] = StockManager.StockData(targetCode, market.GetStockPrice(targetCode)['close'], market.LastDateTime, count)
                self.StocksData[targetCode].LastBuyDate = market.LastDateTime
            return True
     
        
        # 신규 종목 편입(기본적 분석이 완료된 종목 대상)

        for whiteStockPair in sorted_dict:
            whiteCode = whiteStockPair[0]

            loop = Logic_NewStock2(whiteCode)
            if not loop:
                return
        
        '''
        #신규 종목 편입(새로운 종목 탐색)
        searchCount = 0
        while self.boughtFund < self.BuyFundLimit[0]:
            searchCount = searchCount + 1
            
            if searchCount > 1000:
                break
            randStockCode = market.GetRandomStock()
            if (randStockCode in self.StocksData):
                continue
            #if self.Trader.CurrentFund < estiMoney * 0.2:
            #    continue    
                
            if market.IsStockTradable(randStockCode) and self.Evaluator.Evaluate(randStockCode):
                loop = Logic_NewStock(randStockCode)
                if not loop:
                    return
        '''
    # ======================================[물타기 로직]======================================================  
    def __Logic_RepurchaseForGround(self):
        market = self.Trader.Market
        trader = self.Trader
        possibles = {}
        for possibleStockData in self.StocksData.values():
            shcode = possibleStockData.shcode
            curPrice = market.GetStockPrice(shcode)
            price_close = curPrice['close']
            
            
            
            if possibleStockData.prevLowPrice > price_close:
                possibleStockData.prevLowPrice = price_close
                
            if not market.IsStockTradable(shcode) or possibleStockData.LossCut_Today:
                continue
            if not self.Evaluator.Evaluate(shcode):
                possibleStockData.State = StockState.SEA
                continue
            
            
            if possibleStockData.State != StockState.SKY: 
                possibleStockData.State = StockState.GROUND
            else:
                continue
                
                
            curLoss = -possibleStockData.GetCurrentProfitFromFirst(price_close)
            if curLoss < 0:
                continue
                
            dropRate = (price_close / curPrice['open'])  - 1.0
            if dropRate < -0.03:
                possibles[shcode] = dropRate * 0.6 + (-curLoss * 0.4)

        sorted_dict = sorted(possibles.items(), key = lambda item: item[1])
        #print("repur ", sorted_dict)
        # 보유 종목 중 떨어진 종목에 대해서 추가 매수 실시
        for sPair in sorted_dict:   
            extraFund = self.BuyFundLimit[0] - self.boughtFund    
            if extraFund < 2000: # 
                break
        
            shcode = sPair[0]
            sData = self.StocksData[shcode]
            #if self.Trader.CurrentFund < estiMoney * 0.5:
            #    continue\
            curPrice = market.GetStockPrice(shcode)   
            curLoss = -sData.GetCurrentProfitFromFirst(curPrice['close'])
            curPosition = self.GetStockPositionSize(shcode)    
            properPosition = self.__getProperPositionSize(curLoss)
            
            #if properPosition > curPosition and sData.LastBuyDate + timedelta(days = 1) < market.LastDateTime:
            if properPosition > curPosition :
                needPosition = properPosition - curPosition
                needBuyAmount = min(min(needPosition * self.FundPerPosition, self.maxBuyFund), extraFund)
                needCount = int(needBuyAmount / curPrice['close'])
                if needCount > 0:
                    result, usedMoney, count  = self.Trader.BuyStockByMoney(shcode, curPrice['close'], needBuyAmount)
                    self.boughtFund = self.boughtFund + usedMoney
                    sData.LastBuyDate = market.LastDateTime
                    print("appendMoney_Sea", shcode)
    
    # ======================================[손절 로직]======================================================  
    def __Logic_LossCut(self):   
        market = self.Trader.Market
        trader = self.Trader

        possibles = {}
        
        for possibleStockData in self.StocksData.values():
            possibleStockData.LossCut_Today = False
            shcode = possibleStockData.shcode
            curPrice = market.GetStockPrice(shcode)
            price_close = curPrice['close']
            if trader.AveragePrice[shcode] < price_close:
                continue
            #print("check ", shcode, trader.AveragePrice[shcode], price_close)
            ratioFromLow = (price_close/possibleStockData.prevLowPrice ) - 1.0
                          
            if not market.IsStockTradable(shcode) or ratioFromLow < 0.02:
                continue
            score = (-ratioFromLow)
            if possibleStockData.State == StockState.SEA: 
                possibles[shcode] = score
            elif possibleStockData.State == StockState.GROUND: 
                possibles[shcode] = score+100
            
    
        sorted_dict = sorted(possibles.items(), key = lambda item: item[1])
        #print("losscut:", sorted_dict)
        
        for sPair in sorted_dict:         
            if self.Trader.RealizedProfit < self.Cache_EstimatedFund*0.002:
                break
            shcode = sPair[0]
            sData = self.StocksData[shcode]

            curPrice = market.GetStockPrice(shcode)

      
            result, takenMoney, count  = self.Trader.SellStock(shcode, curPrice['close'], 4)
            self.soldFund = self.soldFund + takenMoney
            if not trader.hasStock(shcode):
                del self.StocksData[shcode]
            if result:
                sData.LossCut_Today = True

                
    def Propagate(self):
        market = self.Trader.Market
        trader = self.Trader
        
        print("---(Propagate")
        
        #=========================================[Sky 종목 처리]==========================================
        #보유 종목 중 수익중인 종목 매도
        tempList = list(self.StocksData.values())
        for sData in tempList:
            #neededFund = self.SellFundLimit[0] - self.soldFund    
            #if neededFund < 2000: # 
            #    break
        
            shcode = sData.shcode
            stockBoughtMoney = self.Trader.GetStockBoughtPriceSum(shcode)
            if not market.IsStockTradable(shcode):
                continue
            
            if sData.State != StockState.SKY:
                continue
            
            curPrice = market.GetStockPrice(shcode)['open']
            curPrice_Close = market.GetStockPrice(shcode)['close']
            oldMaxPrice = sData.prevMaxPrice
            if curPrice_Close > sData.prevMaxPrice:
                sData.prevMaxPrice = curPrice_Close
            ratioByMaxPrice = (curPrice_Close/oldMaxPrice) - 1.0 
                    
            appendMoney = False
            
            if ratioByMaxPrice < -0.8  and trader.AveragePrice[shcode] < curPrice_Close:
                #needBuyAmount = max(min(stockBoughtMoney * 0.3, self.Trader.CurrentFund), curPrice)
                needBuyAmount = max(min(min(self.maxBuyFund, self.Trader.CurrentFund), stockBoughtMoney * 0.2), curPrice_Close)
                result, usedMoney, count  = self.Trader.BuyStockByMoney(shcode, curPrice_Close, needBuyAmount)
                print("appendMoney_sky", shcode, result, usedMoney)
                self.boughtFund = self.boughtFund + usedMoney
                if result:
                    appendMoney = True
                    sData.RepurchaseForProfit_Today = True
                    sData.prevMaxPrice = curPrice_Close
                    #print("appendMoney", shcode)
                
            
            curProfitRatio, curProfitFund  = trader.GetProfit(shcode)
            if curProfitRatio < 0.0050 and not appendMoney:
                _, takenMoney, _  = self.Trader.SellStock(shcode, curPrice_Close, 10000)
                self.soldFund = self.soldFund + takenMoney
                if not trader.hasStock(shcode):
                    del self.StocksData[shcode]  
                continue


        self.__Logic_TakingProfit()


        
        self.__Logic_LossCut()
        
        if self.BuyFundLimit[0] > self.boughtFund:
            self.__Logic_RepurchaseForGround()
        
        if self.BuyFundLimit[0] > self.boughtFund:
            self.__Logic_NewStock()
        
