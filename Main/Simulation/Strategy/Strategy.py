class Strategy:
    def __init__(self, trader):
        self.Trader = trader
    

        
    def Start(self):
        print("start")
        
    def End(self):
        print("end")

    
    def Propagate(self):
        print("update")
        
    def CreateDataTable(self):
        pass
    
    def SaveData(self, traderID):
        pass
        
    def LoadData(self, traderID):
        pass       
# 각 전략에 필요한 데이터는 전략마다 별도의 테이블 형식으로 구현한다.