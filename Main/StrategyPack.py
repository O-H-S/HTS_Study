from Simulation.Strategy.FundManager import FundManager
from Simulation.Strategy.StockManager import StockManager
from Simulation.Strategy.FundamentalEvaluator import FundamentalEvaluator


def DefaultPack(targetTrader, dataMgr):

    _evaluator = FundamentalEvaluator(targetTrader, dataMgr)
    stockMgr = StockManager(targetTrader, evaluator = _evaluator)
    
    
    rootStrategy = FundManager(targetTrader, (0.03, 0.2), (0, 1.0), stockMgr)
      
    return rootStrategy