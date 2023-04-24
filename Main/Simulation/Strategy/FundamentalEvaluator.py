
from .Strategy import Strategy
from pandas import Series, DataFrame
import random
class FundamentalEvaluator(Strategy):
    EvaluationTableName = "Strategy_FE_Evaluations"
    
    Version = 1
    def __init__(self, trader, dataMgr):
        super().__init__(trader)

        self.CurYearQuater = None
        self.__CurEvaluatedStocks = {} # dataframe: shcode, grade(boolean)
        self.CurRawDataframe = None
        self.__DirtyEvaluations = None
        self.RawDataframeTable = {}
        
        self.CurWhiteList = []

        self.dataMgr = dataMgr

    def OnDisable(self):
        if not(self.__DirtyEvaluations is None):    
            self.SaveEvaluations(self.__DirtyEvaluations)

    def Evaluate(self, shcode):
        if shcode in self.__CurEvaluatedStocks:
            return self.__CurEvaluatedStocks[shcode]
        

        if shcode in self.__LoadedEvaluations:
            eval_version = self.__LoadedEvaluations.at[shcode, 'version']
            if eval_version == FundamentalEvaluator.Version:
                eval_grade = self.__LoadedEvaluations.at[shcode, 'grade']
                if eval_grade == 'G':
                    self.__CurEvaluatedStocks[shcode] = True
                    return True
                else:
                    self.__CurEvaluatedStocks[shcode] = False
                    return False
                 
  
        self.__evaluate(shcode)
        return self.Evaluate(shcode)
        #return 

    def __evaluate(self, shcode):
        results = self.dataMgr.StockEvaluater.Evaluate(shcode, self.CurYearQuater[0], self.CurYearQuater[1], self.RawDataframeTable)
        
        grade = results['grade']
        # year", "quater", "shcode", "grade", "reason", "version
        self.__DirtyEvaluations.loc[len(self.__DirtyEvaluations.index)] = [self.CurYearQuater[0], self.CurYearQuater[1], shcode, grade, results['reason'], FundamentalEvaluator.Version]
        self.__UnevaluatedSet.discard(shcode)
        #print(results['reason'])
        if grade == 'G':
            self.__CurEvaluatedStocks[shcode] = True
            self.CurWhiteList.append(shcode)
        else:
            self.__CurEvaluatedStocks[shcode] = False

    def GetWhiteList(self):
        return self.CurWhiteList


    def __checkEvaluationTable(self):
        params = "year int, quater text, shcode text, grade text, reason text, version int, primary key(year, quater, shcode)"
        result = self.dataMgr.CheckTable(FundamentalEvaluator.EvaluationTableName, params) 
        #if result == 0:
        #    self.dataMgr.sqlMgr.CreateIndex("Stocks_Index", "{0}(year, quater)")
        #  인덱스 생성 함수 작성해야함. (year, quater)
        

    def LoadEvaluations(self, year, quater):
        self.__checkEvaluationTable()
        
        
        evaluations = self.dataMgr.sqlMgr.GetAllRowSorted(FundamentalEvaluator.EvaluationTableName, "shcode", " year == {0} and quater == '{1}'".format(year, quater), selectQuery = "shcode, grade, reason, version")
        df = DataFrame(evaluations, columns=["shcode", "grade", "reason", "version"])
        df.set_index('shcode', inplace=True)
        
        return df      

    def SaveEvaluations(self, evaluationsDF):
        self.__checkEvaluationTable()

        targetString = "{0}(year , quater , shcode , grade , reason , version )".format(FundamentalEvaluator.EvaluationTableName)
        transformed = evaluationsDF.values.tolist()

        if len(transformed) > 0:
            self.dataMgr.sqlMgr.UpsertRowList(targetString, "year, quater, shcode" , transformed)   

    def __CheckNewYearQuater(self):
        curDate = self.Trader.Market.LastDateTime
        recentYQ = self.dataMgr.StockEvaluater.GetRecentYearQuater(curDate, earlyDay = 0)
        
        if self.CurYearQuater and recentYQ[0] == self.CurYearQuater[0] and recentYQ[1] == self.CurYearQuater[1]:
            # 이미 최근분기 업데이트가 되어있는 경우
            # 점진적인 갱신?
            try:
                randSet = random.sample(self.__UnevaluatedSet,  min(20, len(self.__UnevaluatedSet))) 
                print("updating evaluation...", len(randSet))
                for randStock in randSet:
                    self.Evaluate(randStock)
            except:
                print("evaluation finished")
            
      
            return
            
            
        if not(self.__DirtyEvaluations is None):    
            self.SaveEvaluations(self.__DirtyEvaluations)
            
            
        self.__CurEvaluatedStocks = {} # 캐시역할
        self.__DirtyEvaluations = DataFrame(columns = ["year", "quater", "shcode", "grade", "reason", "version"])  
        self.__LoadedEvaluations = self.LoadEvaluations(recentYQ[0], recentYQ[1])
        self.__UnevaluatedSet = self.Trader.Market.AllStockSet - set(self.__LoadedEvaluations.index.unique())
        print(len(self.__UnevaluatedSet), "개의 종목을 평가해야합니다.")
        
        
        prevYQ = self.dataMgr.ReportManager.GetYearQuater(None, recentYQ[0], recentYQ[1], -1, 0)
        while True:
            if not (prevYQ in self.RawDataframeTable):
                self.RawDataframeTable[prevYQ] = self.dataMgr.ReportManager.GetReportsFromYearQuater(prevYQ , prevYQ)
                print("loading ", prevYQ)
            if prevYQ == recentYQ:
                break                  
            prevYQ = self.dataMgr.ReportManager.GetYearQuater(None, prevYQ[0], prevYQ[1], 0, 1)
            
        
        
        self.CurRawDataframe = self.RawDataframeTable[recentYQ]
        self.CurWhiteList = self.__LoadedEvaluations.loc[self.__LoadedEvaluations["grade"] == 'G', "grade"].index.values.tolist()
        #print(self.CurWhiteList)
        #print(type())
        #self.RawDataframeTable)



        self.CurYearQuater = recentYQ

    def Start(self):
        self.__CheckNewYearQuater()
        
        
        
        
    def End(self):
        pass
    
    def Propagate(self):
        pass