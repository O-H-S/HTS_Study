from datetime import datetime, timedelta
from Trading.Market import MarketState, PriceListener


class ConditionOrder:
    def __init__(self):
        self.ratedDate = datetime(2000, 1, 1)
        self.buyORsell = True
        self.shcode = ''
        self.offsetDays = 0
        self.limitWeight = 0.05
        self.basePrice = -1
        self.started = False
        
        self.active = False
        self.adjustedPrice = -1 # 지정된 주문가는 과거 기준의 수정비율이 적용된 가격, 그때와 현재에 수정 비율이 변화할 가능성이 존재함. 이에대해 보정된 가격
        
        self.priceListener = None
        
    def Init(self, ID):
        self.ID = ID
        
    def InitByRowData(self, rowData):
        self.ID = rowData['ID']
        self.shcode = rowData['shcode']
        self.buyORsell = bool(rowData['buyORsell'])
        self.basePrice = rowData['basePrice']
        if rowData['ratedDate'] is None:
            self.ratedDate = None
        else:
            self.ratedDate = datetime.strptime (rowData['ratedDate'], "%Y%m%d")
        self.baseDate = datetime.strptime (rowData['baseDate'], "%Y%m%d")
        self.offsetDays = rowData['offsetDays']
        self.limitWeight = rowData['limitWeight']
        self.started = bool(rowData['started'])
        
        
        #"ID, shcode, buyORsell, basePrice, ratedDate, baseDate, offsetDays, limitWeight"     
    
    def SetPrice(self, basePrice, adjDate):
        self.basePrice = basePrice
        self.ratedDate = adjDate
        
    def SetDate(self, baseDate, offsetDays):
        self.baseDate = baseDate
        self.offsetDays = offsetDays
    
    
    def __OnUpdatePrice(self, prices): #active된 상태에서만 호출되는 콜백
        targetStockPotentialWeight = 0 # 미체결 주문과 현재 잔고를 종합하여 잠재적 비중을 구한다.

        curPrice = prices['price']
        if self.buyORsell : #매수 주문일 때, limitWeight 의 비중보다 작으면 매수한다.
            
            if curPrice <= self.adjustedPrice and self.limitWeight >= targetStockPotentialWeight:
                print("지정된 조건 충족, 매수 주문후 감시 종료")
                self.Deactivate()
                self.started = False
        else: #매도 주문일 때, limitWeight 의 비중보다 크면 매도한다.
            if curPrice >= self.adjustedPrice and self.limitWeight <= targetStockPotentialWeight:
                print("지정된 조건 충족, 매도 주문후 감시 종료")
                self.Deactivate()    
                self.started = False
        
    
    def TestActivable(self, curStockWeight, curDate):
        
        #print("TA", self.started)
        if not self.started:
            return False
            
        #if self.limitWeight < curStockWeight:
        #    return False
            
        offset = int(self.offsetDays * 1.5)
        #print((self.baseDate + timedelta(days=offset)), curDate)
        if self.baseDate + timedelta(days=offset) < curDate:
            return False
    
        self.adjustedPrice = self.basePrice
    
        return True
    
    def Activate(self, market):
        self.active = True
        self.market = market
        if self.priceListener is None:
            self.priceListener = PriceListener(self.shcode, self.__OnUpdatePrice)
            
        market.AddPriceListener(self.priceListener)
        print(self.ID, "] activated")
        # 실시간 가격 감시 등록
        
        
    def Deactivate(self):
    
    
        self.active = False     
        self.market.RemovePriceListener(self.priceListener)
        print(self.ID, "] deactivated")
        # 감시 해제
        