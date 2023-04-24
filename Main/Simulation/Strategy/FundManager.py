
from .Strategy import Strategy


class FundManager(Strategy):
    def __init__(self, trader, buyLimit , sellLimit, stockMgr):
        super().__init__(trader)
        
        self.buyLimitPerDay = buyLimit
        self.sellLimitPerDay = sellLimit
        
        self.StockManager = stockMgr
    def OnEnable(self):
        pass
        
    def OnDisable(self):
        self.StockManager.OnDisable()
    
    def Start(self):

        
        estimatedFund = self.Trader.GetEstimatedFund()
        

        self.BuyMoneyLimit = (min(estimatedFund * self.buyLimitPerDay[0], self.Trader.CurrentFund), min(estimatedFund * self.buyLimitPerDay[1], self.Trader.CurrentFund))
        self.SellMoneyLimit = (min(estimatedFund * self.sellLimitPerDay[0], self.Trader.CurrentFund), min(estimatedFund * self.sellLimitPerDay[1], self.Trader.CurrentFund))
        

        self.StockManager.Start(self.BuyMoneyLimit, self.SellMoneyLimit)
        
    def End(self):
        self.StockManager.End()
    
    def Propagate(self):
        self.StockManager.Propagate()