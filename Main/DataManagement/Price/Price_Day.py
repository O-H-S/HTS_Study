from Common.GlobalLogging import LogManager
logMgr = LogManager("Main.DM.Price.Static")
logger = logMgr.logger

import DataManagement.SearchLineController as SLC
import mmap, threading, time
from Common.Command import Command, SyncCommand
from datetime import datetime, timedelta
from datetime import time as dtTime
from pandas import Series, DataFrame



class StaticPriceCollector:

    PriceTableName = "StockPrice_Day"
    PriceSearchLineTableName = "StockPriceSearchLine_Day"
    def __init__(self, dataMgr):
        self.dataMgr = dataMgr
        self.TimeManager = dataMgr.TimeManager
        
        
        self.dataMgr.AddMessageHandler("GetPrice_Day_Result", self.__OnArriveResult)
        
    def __CheckPriceTable(self):
        params = "shcode text, date text, open integer, high integer, low integer, close integer, jongchk integer, pricechk integer, rate real, timestamp integer, primary key(shcode, date)"
        self.dataMgr.CheckTable(StaticPriceCollector.PriceTableName, params) 
        
    def __CheckSearchLineTable(self):
    
        params = "shcode text, start integer, end integer, primary key(shcode, start)"
        self.dataMgr.CheckTable(StaticPriceCollector.PriceSearchLineTableName, params) 
        
        #self.searchLine = SLC.LoadFromDB(self.dataMgr.sqlMgr, "OrderData_SL", 1)
        
    def CollectPrice_Day(self, shcode, startDate, endDate):
        pass
    
    
    def AdjustPrice(self, rawPrice, curDateString, coeList):
    
        powCount = len(coeList)         
        for coeTuple in reversed(coeList):
            startdate = coeTuple[0]
            if startdate <= curDateString:
                powCount = powCount-1 
                continue
            
            coe = coeTuple[1]
            rawPrice = coe * rawPrice * pow(100, -powCount)
            return rawPrice
        
        #print(rawPrice, curDateString, coeList)
        
        return rawPrice
    
    def GetRates(self, startDate):
        rates = self.dataMgr.sqlMgr.GetAllRowSorted(StaticPriceCollector.PriceTableName, "date", " date >= {0} and rate != 0".format(startDate.strftime('%Y%m%d')), selectQuery = "shcode, date, rate")
        df_featuredRow = DataFrame(rates, columns=["shcode", "date", "rate"])
        codeGroupCollection = df_featuredRow.groupby('shcode')

        coeTable = {}

        for shcode, df_group in codeGroupCollection:       
           
            prevIDX = 0       
            coes = []
            prevCoe = 1
            for idx in reversed(df_group.index):
                rate = df_group.loc[idx, 'rate']
                coe = ((rate + 100)) * prevCoe
                coes.append((df_group.loc[idx, 'date'], coe))
                prevCoe = coe

            
            coeTable[shcode] = coes
            
        return coeTable
    
    def GetPricesFromDate_Day(self, startDate, endDate, adjust = True):
        pricesRow = self.dataMgr.sqlMgr.GetAllRowSorted(StaticPriceCollector.PriceTableName, "date", "date <= {1} and date >= {0}".format(startDate.strftime('%Y%m%d'), endDate.strftime('%Y%m%d')), selectQuery = "shcode, date, open, high, low, close, rate") 
        df = DataFrame(pricesRow, columns=["shcode", "date", "open", "high", "low", "close", "rate"])
        df.set_index(['shcode', 'date'], inplace=True)
        #print(df)
        #print(df.index[['date']])
        '''
        if adjust:

            rates = self.dataMgr.sqlMgr.GetAllRowSorted(StaticPriceCollector.PriceTableName, "date", " date >= {0} and rate != 0".format(startDate.strftime('%Y%m%d')), selectQuery = "shcode, date, rate")
            df_featuredRow = DataFrame(rates, columns=["shcode", "date", "rate"])
            codeGroupCollection = df_featuredRow.groupby('shcode')

            for shcode, df_group in codeGroupCollection:       
                #print(df_group)
                
                    
                    
                
                prevIDX = 0
                lastStartDate = "00000000"
                codePrices = None
                try:
                    codePrices = df.loc[shcode]
                except:
                    continue
                    
                coes = []
                prevCoe = 1
                for idx in reversed(df_group.index):
                    rate = df_group.loc[idx, 'rate']
                    coe = ((rate + 100)) * prevCoe
                    #print(coe)
                    coes.append((df_group.loc[idx, 'date'], coe))
                    prevCoe = coe
                    #print(idx, df_featuredRow.loc[idx, 'date'], df_featuredRow.loc[idx, 'rate'])
                
                #codePriceIndex = codePrices.index.to_numpy()
                powCount = len(coes)
                
                #subDF = (df.index.get_level_values('shcode') == shcode)
                #print(len(subDF))
                for coeTuple in reversed(coes):
                    startdate = coeTuple[0]
                    #print(startdate)
                    coe = coeTuple[1]
                    targetDatesPosition = (lastStartDate <= codePrices.index) & (codePrices.index < startdate) # ndarray 형식
                    
                    #appliedIndexes = []
                    #for ind in codePriceIndex[targetDatesPosition]:
                    #    appliedIndexes.append((shcode, ind))
                        
                    #print(codePrices.index[targetDatesPosition])
                    #print(codePriceIndex[targetDatesPosition])
                    #df.loc[prevIDX:idx, 'close'] = (df.loc[prevIDX:idx, 'close'] * coe) * pow(100, -powCount)

                    
                    #codePrices.loc[(lastStartDate <= codePrices.index) & (codePrices.index < startdate), ['close','open','high','low']]
                    #codePrices.loc[(lastStartDate <= codePrices.index) & (codePrices.index < startdate), ['close','open','high','low']] = coe * codePrices.loc[(lastStartDate <= codePrices.index) & (codePrices.index < startdate), ['close','open','high','low']] * pow(100, -powCount) 
                    #df.loc[(subDF) & (lastStartDate <= df.index.get_level_values('date')) & (df.index.get_level_values('date') < startdate), ['close','open','high','low']] = coe * df.loc[(subDF) & (lastStartDate <= df.index.get_level_values('date')) & (df.index.get_level_values('date') < startdate), ['close','open','high','low']] * pow(100, -powCount)
                    
                    
                    df.loc[(shcode, codePrices.index[targetDatesPosition]), ['open','high','low','close']] = coe * df.loc[(shcode, codePrices.index[targetDatesPosition]), ['open','high','low','close']] * pow(100, -powCount)
                    
  
                    lastStartDate = startdate

                    powCount = powCount-1  
                
                #print(shcode, len(coes))
                #print(codePrices)    
                #df.loc[shcode, ['close','open','high','low']] = codePrices.loc[:]
            
        '''
        return df

    
    def GetPrice_Day(self, shCode, startDate, endDate, adjust = True, returnPrices = True): # 동기화 함수, 결과를 받아올때까지 block된다. "Command" 객체가 동기화 작업을 위한 식별자 역할을 한다.
        
        collected = False
        
        endDate = datetime(endDate.year, endDate.month,endDate.day)
        
        curDatetime = self.TimeManager.GetServerDate(True)
        startDate = datetime(startDate.year, startDate.month,startDate.day)
        if endDate > curDatetime or (endDate.year == curDatetime.year and endDate.month == curDatetime.month and endDate.day == curDatetime.day):
            if curDatetime.time() > dtTime(15, 30, 0):              
                endDate = (endDate + timedelta(days=1)) - timedelta(seconds=1)
            elif curDatetime.time() < dtTime(9, 00, 0):     
                endDate =  endDate.replace(hour=9, minute=00)   
            else:
                endDate = curDatetime
        else:
            endDate = (endDate + timedelta(days=1)) - timedelta(seconds=1)
            #print(endDate)

        #search table에서 startDate ~ endDate사이에 홀이 있는지, 해당 기간을 포함하는지 조회함.
        self.__CheckSearchLineTable()
        

        searchSection = (int(datetime.timestamp(startDate)), int(datetime.timestamp(endDate)))
        
        daySearchLine = SLC.LoadFromDB(self.dataMgr.sqlMgr, StaticPriceCollector.PriceSearchLineTableName, 1, _selectQuery = "start, end" , _whereQuery = "shcode == '{0}'".format(shCode))
        #daySearchLine.print()
        holes = daySearchLine.getHolesBySection(searchSection)

        while len(holes) > 0:   
            refinedHole = []
            for hole in holes:
                #if hole[0] == hole[1]: # xing tr 자체가 단 하루의 포맷을 허용하지 않음.
                #    refinedHole.append((hole[0] - 86400, hole[1]))
                #else:
                refinedHole.append(hole) #아래에서 조절하기
            newHoles = []
            for hole in refinedHole:
                
                #포함되지 않는 구간을 xing manager에게 요구함.
                Command_DayPrice = SyncCommand()
                Command_DayPrice.shcode = shCode
                Command_DayPrice.timestamp = int(datetime.timestamp(curDatetime))
                Command_DayPrice.startDate = datetime.fromtimestamp(hole[0])
                Command_DayPrice.endDate = datetime.fromtimestamp(hole[1])
                
                if Command_DayPrice.startDate.date() == Command_DayPrice.endDate.date():
                    Command_DayPrice.startDate = Command_DayPrice.startDate - timedelta(days=1)
                collected = True
                self.dataMgr.SendMessageToManagerAsync("GetPrice_Day", (shCode, Command_DayPrice.startDate.strftime('%Y%m%d'), Command_DayPrice.endDate.strftime('%Y%m%d'), Command_DayPrice.ID))
                #print("hole: ",Command_DayPrice.startDate , '-' , Command_DayPrice.endDate) 
                Command_DayPrice.Start()
                
                if Command_DayPrice.complete:
                    daySearchLine.addSection(hole) #hole을 처리할때마다, searchline에 hole을 매꾼다.
                else:
                    firstDate = Command_DayPrice.firstDate
                    fD_timestamp = int(datetime.timestamp(firstDate))
                    daySearchLine.addSection((fD_timestamp , hole[1]))
                    newHole = ( hole[0], fD_timestamp)                                    
                    newHoles.append(newHole)
                #print(Command_DayPrice.prices)
            
            holes = newHoles
          
        expandedSects = []

        for sect in daySearchLine.sections:
            expandedSects.append((sect[0], sect[1], shCode,))
        daySearchLine.sections = expandedSects
        #daySearchLine.print()

        SLC.SaveToDB(self.dataMgr.sqlMgr, StaticPriceCollector.PriceSearchLineTableName, daySearchLine, colCount = 3, _paramQuery = "start, end, shcode", _whereQuery = "shcode == '{0}'".format(shCode))
        
        # start 호출시 block되고 후에 wake 되면, 작업이 완료된거임.
        #모든 hole들이 처리되었으므로, db에서 한꺼번에 가져오고 그값을 리턴함.
        # df = pd.DataFrame(c.fetchall(), columns=['product_name','price'])
        if not returnPrices:
            return None, None, collected
        
        pricesRow = self.dataMgr.sqlMgr.GetAllRowSorted(StaticPriceCollector.PriceTableName, "date", "shcode == '{2}' and date <= {1} and date >= {0}".format(startDate.strftime('%Y%m%d'), endDate.strftime('%Y%m%d'), shCode)) 

        df = DataFrame(pricesRow, columns=self.dataMgr.sqlMgr.GetTableColumnNames(StaticPriceCollector.PriceTableName))
        adjustedDatetime = None
        if adjust:
            rates = self.dataMgr.sqlMgr.GetAllRowSorted(StaticPriceCollector.PriceTableName, "date", "shcode == '{1}' and date >= {0} and rate != 0".format(startDate.strftime('%Y%m%d'), shCode))
            
            if rates is not None and len(rates) > 0:
                adjustedDatetime = datetime.strptime(rates[-1][1], "%Y%m%d")
            
            df_featuredRow = DataFrame(rates, columns=self.dataMgr.sqlMgr.GetTableColumnNames(StaticPriceCollector.PriceTableName))
            coes = []
            #print("df_featuredRow", df_featuredRow)
            
            prevCoe = 1
            for idx in reversed(df_featuredRow.index):
                rate = df_featuredRow.loc[idx, 'rate']
                coe = ((rate + 100)) * prevCoe
                #print(coe)
                coes.append((df_featuredRow.loc[idx, 'date'], coe))
                prevCoe = coe
                #print(idx, df_featuredRow.loc[idx, 'date'], df_featuredRow.loc[idx, 'rate'])
                
                
            powCount = len(coes)
            prevIDX = 0
            lastStartDate = "00000000"
            for coeTuple in reversed(coes):
                startdate = coeTuple[0]
                coe = coeTuple[1]
                
                #df.loc[prevIDX:idx, 'close'] = (df.loc[prevIDX:idx, 'close'] * coe) * pow(100, -powCount)

                '''
                df.loc[df['date'] < startdate, 'close'] = coe * df.loc[df['date'] < startdate, 'close'] * pow(100, -powCount)
                df.loc[df['date'] < startdate, 'open'] = coe * df.loc[df['date'] < startdate, 'open'] * pow(100, -powCount)
                df.loc[df['date'] < startdate, 'high'] = coe * df.loc[df['date'] < startdate, 'high'] * pow(100, -powCount)
                df.loc[df['date'] < startdate, 'low'] = coe * df.loc[df['date'] < startdate, 'low'] * pow(100, -powCount)
                '''

                df.loc[(lastStartDate <= df['date']) & (df['date'] < startdate), 'close'] = coe * df.loc[(lastStartDate <= df['date']) & (df['date'] < startdate), 'close'] * pow(100, -powCount)
                df.loc[(lastStartDate <= df['date']) & (df['date'] < startdate), 'open'] = coe * df.loc[(lastStartDate <= df['date']) & (df['date'] < startdate), 'open'] * pow(100, -powCount)
                df.loc[(lastStartDate <= df['date']) & (df['date'] < startdate), 'high'] = coe * df.loc[(lastStartDate <= df['date']) & (df['date'] < startdate), 'high'] * pow(100, -powCount)
                df.loc[(lastStartDate <= df['date']) & (df['date'] < startdate), 'low'] = coe * df.loc[(lastStartDate <= df['date']) & (df['date'] < startdate), 'low'] * pow(100, -powCount)
                #df.loc[df['date'] < startdate, 'open'] = coe * df.loc[df['date'] < startdate, 'open'] 
                #df.loc[df['date'] < startdate, 'high'] = coe * df.loc[df['date'] < startdate, 'high']
                #df.loc[df['date'] < startdate, 'low'] = coe * df.loc[df['date'] < startdate, 'low'] 
                lastStartDate = startdate
                '''
                df.loc[df['date'] < startdate, 'close'] =  (df.loc[df['date'] < startdate, 'close'] * pow(100, powCount)) / coe
                df.loc[df['date'] < startdate, 'open'] = (df.loc[df['date'] < startdate, 'open'] * pow(100, powCount)) / coe
                df.loc[df['date'] < startdate, 'high'] = ( df.loc[df['date'] < startdate, 'high'] * pow(100, powCount)) / coe
                df.loc[df['date'] < startdate, 'low'] =  (df.loc[df['date'] < startdate, 'low'] * pow(100, powCount)) / coe
                '''
                powCount = powCount-1       
        return df, adjustedDatetime, collected
        
    def __OnArriveResult(self, args):

        metadata = args[0]
        print("[DataManager] 일봉 데이터 읽는 중... (길이:", metadata['Length'],")(거래일수:", metadata['Count'],")")
        df = None
        if metadata['Length'] > 0:
            mm = mmap.mmap(-1, metadata['Length'], metadata['MemName'])
            mm.seek(0)
            bytesOfPrices = mm.read(metadata['Length'])
            self.dataMgr.ReleaseMem(metadata['MemName'])
            df = self.dataMgr.ReadByteByFormat(metadata, bytesOfPrices)
        print("[DataManager] 일봉 데이터 읽기 완료")
        
        
        
        
        command = Command.Get(args[2])
        command.prices = df
        command.complete = args[3]
        
        # dataframe에 shcode, timestamp 붙히기
        if df is not None:
            
            df.insert(df.shape[1],'timestamp', command.timestamp)
            df.insert(0,'shcode', command.shcode)
            
            #print(df)
            command.lastDate = datetime.strptime (df.iloc[-1]['date'], "%Y%m%d")
            command.firstDate = datetime.strptime (df.iloc[0]['date'], "%Y%m%d")
            self.__CheckPriceTable()
            self.dataMgr.sqlMgr.insert_conflict_ignore(df, StaticPriceCollector.PriceTableName)
        
        command.End()
            