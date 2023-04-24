
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager
import OpenDartReader
import re, time, math
from pandas import Series, DataFrame
logMgr = LogManager("Main.DM.ReportManager")
logger = logMgr.logger

class ReportManager:
    QuaterReportVersion = 4

    def __init__(self, dataMgr):
        self.dataMgr = dataMgr
        self.ConvertRawNames()
        self.lastDartCallTime = 0
        self.DartReader = None
      
    def ConnectToDart(self, APIKEY):
        try:
            self.DartReader = OpenDartReader(APIKEY) 
        except Exception as e:
            logger.error("dart error : {0}".format(e))
    
    def ConvertRawNames(self):
        hangul = re.compile('[^\(\)ㄱ-ㅣ가-힣]+') # 한글과 괄호를 제외한 모든 글자       
        regex = "\(.*\)|\s-\s.*" # 괄호와 괄호안의 내용
        
        def convert_name(rawName):
            replaced = hangul.sub('', rawName)          
            return re.sub(regex, '', replaced)
        
        def convertRaws(rawNameList):
            cNameSet = set()
            for rName in rawNameList:
                cNameSet.add(convert_name(rName))
                
            #print(list(cNameSet))
            return list(cNameSet)
    
        NameList_유동자산 = ['유동자산']
        NameList_부채총계 = ['부채총계']
        NameList_자본총계 = ['자본총계', "자본총계"]
        NameList_매출액 = ['매출액', '영업수익', '수익', '영업수익(매출액)', '수익(매출액)', 'I. 영업수익','I.영업수익']
        NameList_매출총이익 = ['매출총이익']
        NameList_영업이익 = ['영업이익','영업이익(손실)','III.영업이익(손실)']
        NameList_당기순이익 = ['당기순이익','당기순이익(손실)','당순이익(손실)','분기순이익','분기순이익(손실)','반기순이익','반기순이익(손실)','당기연결순이익','연결분기순이익','연결반기순이익','연결당기순이익','연결분기(당기)순이익','연결반기(당기)순이익','연결분기순이익(손실)']
        NameList_영업현금흐름 = ["영업활동으로 인한 현금흐름","영업활동으로부터의 순현금유입","영업활동으로 인한 순현금흐름",'영업활동으로 인한 순현금흐름 합계','영업활동순현금흐름 합계','영업활동현금흐름','영업활동으로인한순현금흐름', '영업활동순현금흐름','영업활동으로인한현금흐름', '영업활동 순현금흐름유입(유출)', '영업활동 순현금흐름']
        NameList_투자현금흐름 = ["투자활동으로 인한 순현금흐름","투자활동으로 인한 현금흐름",'투자활동으로 인한 순현금흐름 합계','투자활동으로부터의 순현금유출','투자활동순현금흐름 합계','투자활동현금흐름', '투자활동으로부터의 순현금유입(유출)', '투자활동으로인한순현금흐름', '투자활동순현금흐름','투자활동 순현금흐름유입(유출)','투자홛동으로 인한 순현금흐름','투자활동으로인한현금흐름', '투자활동으로 인한 순현금흐름액','투자활동 순현금흐름']
        NameList_재무현금흐름 = ['재무활동으로부터의 순현금유입(유출)',"재무활동으로 인한 순현금흐름","재무활동으로 인한 현금흐름",'재무활동으로 인한 순현금흐름 합계','재무활동으로부터의 순현금유출','재무활동순현금흐름 합계','재무활동현금흐름','재무활동으로인한순현금흐름','재무활동순현금흐름','재무활동 순현금흐름유입(유출)','재무홛동으로 인한 순현금흐름','재무활동으로인한현금흐름','재무활동으로 인한 순현금흐름액','재무활동 순현금흐름']
        NameList_당기순이익_세전 = ['당기순이익(세전)', '법인세비용차감전순이익(손실)']
        NameList_당기순이익_세금 = ['당기순이익(세금)', '법인세비용']
        
        self.NameList_유동자산 = convertRaws(NameList_유동자산)
        self.NameList_부채총계 = convertRaws(NameList_부채총계)
        self.NameList_자본총계 = convertRaws(NameList_자본총계)
        self.NameList_매출액 = convertRaws(NameList_매출액)
        self.NameList_매출총이익 = convertRaws(NameList_매출총이익)
        self.NameList_영업이익 = convertRaws(NameList_영업이익)
        self.NameList_당기순이익 = convertRaws(NameList_당기순이익)
        self.NameList_영업현금흐름 = convertRaws(NameList_영업현금흐름)
        self.NameList_투자현금흐름 = convertRaws(NameList_투자현금흐름)
        self.NameList_재무현금흐름 = convertRaws(NameList_재무현금흐름)
        self.NameList_당기순이익_세금 = convertRaws(NameList_당기순이익_세금)
        self.NameList_당기순이익_세전 = convertRaws(NameList_당기순이익_세전)
    def GetBusinessReport(self, code, year, CFS = True):
        return self.GetQuaterReport(code, year, 'Y', -1,CFS)
    
    def GetQuaterReportEX(self, code, yearAndQuater, CFS = True):
        return self.GetQuaterReport( code, yearAndQuater[0], yearAndQuater[1], -1, CFS)
    
    def _getAccountDataFromDF(self, df):
        pass
      

    def GetYearQuater(self, targetCode, currentYear, currentQuater, offsetYear, offsetCount):
        resultYear = currentYear + offsetYear
        
        if currentQuater == 'Y':
            return (resultYear, 'Y')
            
        quaterIndexTable = {'1Q' : 0, '2Q' : 1, '3Q' : 2, '4Q' : 3} 
        indexQuaterTable = ['1Q','2Q','3Q','4Q']
        qIndex = quaterIndexTable[currentQuater]
        targetIndex = (qIndex + offsetCount) % 4
        #print(((qIndex + offsetCount) / 4), int(((qIndex + offsetCount) / 4)))

        targetYear = (currentYear + offsetYear) + math.floor(((offsetCount+qIndex) / 4))
        return (targetYear, indexQuaterTable[targetIndex])


    def GetReportsFromYearQuater(self, YQ_Start, YQ_End):
        sqlMgr = self.dataMgr.sqlMgr
        
        startYear = YQ_Start[0]
        startQuater = YQ_Start[1]
        
        endYear = YQ_End[0]
        endQuater = YQ_End[1]
    
        boundQuery_start = "({0} < year) or (({0} == year) and '{1}' <= quater)".format(startYear, startQuater)
        boundQuery_end = "({0} > year) or (({0} == year) and '{1}' >= quater)".format(endYear, endQuater)
        boundQuery_all = "({0}) and ({1})".format(boundQuery_start, boundQuery_end)
    
        tableName = "QuaterReport"
        result = sqlMgr.GetAllRow(tableName, whereQuery= "{0}".format(boundQuery_all))
        df = DataFrame(result, columns=sqlMgr.GetTableColumnNames(tableName))
        
        #df = df[df["account"] == 'Date' & df["amount"]]
        
        df.set_index(['shcode', 'year', 'quater', 'CFS', 'account'], inplace=True)
        df.sort_index(inplace=True)
        
        
        
        return df
        '''
        if len(result) > 0:
            emptyTup = (0, 0, 0, 0, 0, 0, 0, 0,0, 0,0)
            taken_data = Series(emptyTup, index = ['유동자산', '부채총계', '자본총계', '매출액', '매출총이익', '영업이익', '당기순이익', '영업활동현금흐름', '투자활동현금흐름','재무활동현금흐름', '잉여현금흐름'])
            for ac in result:
                taken_data[ac[4]] = ac[5]
            
            if 'Date'  in taken_data.keys() and 'Version'  in taken_data.keys():
                lastTimeStamp = taken_data['Timestamp']
                if lastTimeStamp + interval > curTime:
                    #print("interval", lastTimeStamp, curTime)
                    return None
                    
                if taken_data['Date'] is None and int(taken_data['Version']) == ReportManager.QuaterReportVersion:
                    
                    today = datetime.fromtimestamp(curTime)
                    lastUpdateDate = datetime.fromtimestamp(lastTimeStamp)                   
                    qBaseDate = self.GetBaseDateFromYearQuater(year, quaterText)
                    if  today < qBaseDate - timedelta(days=30) or (qBaseDate + timedelta(days=1) < lastUpdateDate):               
                        #print("failed: ",year, quaterText, ( qBaseDate + timedelta(days=1)), lastUpdateDate)
                        return None
                    #print("passed: ",year, quaterText, ( qBaseDate + timedelta(days=1)), lastUpdateDate)
                elif int(taken_data['Version']) < possibleVersion:
                    logger.debug("report data version is low {0} < {1}". format(int(taken_data['Version']), ReportManager.QuaterReportVersion) )
                else:
                    return taken_data
        '''

    def UpdateQuaterReport(self, code, startYear, endYear, CFS = True):
        quaterIndexTable = {'1Q':0, '2Q': 1,'3Q': 2,'4Q': 3}
        quaterTextOrder = ['1Q', '2Q','3Q','4Q']
        

        for curYear in range(startYear, endYear+1):
            self.GetQuaterReport(code, curYear, '1Q',-1,CFS)
            self.GetQuaterReport(code, curYear, '2Q',-1,CFS)
            self.GetQuaterReport(code, curYear, '3Q',-1,CFS)    
            self.GetQuaterReport(code, curYear, '4Q',-1,CFS)
            self.GetQuaterReport(code, curYear, 'Y',-1,CFS)
                
    def GetBaseDateFromYearQuater(self, year, quater):
        if quater == '1Q':
            return datetime(year, 5, 15)
        elif quater == '2Q':
            return datetime(year, 8, 15)
        elif quater == '3Q':
            return datetime(year, 11, 15)
        else:
            return datetime(year+1, 3, 30)
    
    
    
    def GetQuaterReport(self, code, year, quaterText, possibleVersion = -1, CFS = True, interval = 0):
        if possibleVersion < 0:
            possibleVersion = ReportManager.QuaterReportVersion
        sqlMgr = self.dataMgr.sqlMgr
        quaterCodeFromText = {'1Q':'11013', '2Q': '11012','3Q': '11014','4Q': '11011', 'Y':'11011'}
        quaterIndexTable = {'1Q':0, '2Q': 1,'3Q': 2,'4Q': 3}
        quaterTextOrder = ['1Q', '2Q','3Q','4Q']
        # Table 체크후, 로컬에서 가져올수있으면 가져온다.
        curTime = time.time()

        quaterCode = quaterCodeFromText[quaterText]
        #quaterIndeox = quaterIndexTable[quaterText]
        
        params = "shcode text, year integer, quater text, CFS integer default 1, account text, amount real, primary key(shcode, year, quater, CFS, account)"
        
        
        tableName = "QuaterReport"
        creationQuery = sqlMgr.CreateTable(tableName, params, True)
        if not sqlMgr.IsTableExists(tableName):
            sqlMgr.CreateTable(tableName, params)
  
        else:
            if sqlMgr.GetTableStructure(tableName) != creationQuery:
                pass
                #print("수정 예정")
                #sqlMgr.SetTableStructure(tableName, creationQuery)
                #sqlMgr.RemoveTable(tableName)
                #sqlMgr.CreateTable(tableName, params)
        targetString = "{0}(shcode, year, quater, CFS, account, amount)".format(tableName)
        CFS_InDB = 1
        if not CFS:
            CFS_InDB = 0

        result = sqlMgr.GetAllRow(tableName, whereQuery= " shcode=='{0}' and year == {1} and quater == '{2}' and CFS == {3}".format(code, year, quaterText, CFS_InDB))
        if len(result) > 0:
            emptyTup = (0, 0, 0, 0, 0, 0, 0, 0,0, 0,0)
            taken_data = Series(emptyTup, index = ['유동자산', '부채총계', '자본총계', '매출액', '매출총이익', '영업이익', '당기순이익', '영업활동현금흐름', '투자활동현금흐름','재무활동현금흐름', '잉여현금흐름'])
            for ac in result:
                taken_data[ac[4]] = ac[5]
            
            if 'Date'  in taken_data.keys() and 'Version'  in taken_data.keys():
                lastTimeStamp = taken_data['Timestamp']
                if lastTimeStamp + interval > curTime:
                    #print("interval", lastTimeStamp, curTime)
                    return None
                    
                if taken_data['Date'] is None and int(taken_data['Version']) == ReportManager.QuaterReportVersion:
                    
                    today = datetime.fromtimestamp(curTime)
                    lastUpdateDate = datetime.fromtimestamp(lastTimeStamp)                   
                    qBaseDate = self.GetBaseDateFromYearQuater(year, quaterText)
                    if  today < qBaseDate - timedelta(days=30) or (qBaseDate + timedelta(days=1) < lastUpdateDate):               
                        #print("failed: ",year, quaterText, ( qBaseDate + timedelta(days=1)), lastUpdateDate)
                        return None
                    #print("passed: ",year, quaterText, ( qBaseDate + timedelta(days=1)), lastUpdateDate)
                elif int(taken_data['Version']) < possibleVersion:
                    logger.debug("report data version is low {0} < {1}". format(int(taken_data['Version']), ReportManager.QuaterReportVersion) )
                else:
                    return taken_data

        
        

        
        if self.lastDartCallTime + 0.1 > curTime:
            time.sleep((self.lastDartCallTime + 0.1) - curTime)
        

        try:
            self.lastDartCallTime = curTime
            df1 = None
            if CFS:
                df1 = (self.DartReader.finstate_all(code, year, reprt_code=quaterCode, fs_div='CFS')) 
            else:
                df1 = (self.DartReader.finstate_all(code, year, reprt_code=quaterCode, fs_div='OFS')) 
            #df1 = (self.DartReader.finstate(code, year, reprt_code=quaterCode)) 
            #print(df1)
            #for idx,row in df1[['fs_div','sj_div', 'account_nm','thstrm_amount']].iterrows():
            #    print(row['fs_div'],'\n',row['sj_div'],'\n', row['account_nm'],'\n',row['thstrm_amount'])
            #    print("--")
            #print(df1)
            #df1 = (self.DartReader.finstate_all(code, year, reprt_code=quaterCode)) 
            #print(df1)
            if df1 is None:       
                failData = [(code, str(year), quaterText, CFS_InDB,'Version', ReportManager.QuaterReportVersion),
                (code, str(year), quaterText, CFS_InDB, 'Timestamp', int(curTime)),
                (code, str(year), quaterText, CFS_InDB, 'Date', None)]
                
                sqlMgr.UpsertRowList(targetString, "shcode, year, quater, CFS, account" , failData)   
                noneMessage = "quater report) {0} {1} {2} cfs({3}) 보고서 수신 불가 ".format( code, year, quaterText, CFS)
                logger.debug(noneMessage)
                return None
        except Exception as e:
            logger.error("quaterReport) {0}".format( e))
            return None
        
        #self.UpsertRowList(targetString, "shcode, year, quater, account" ,[(code, str(year), quaterText, 'Result', '1')])
        #for idx,row in df1[['sj_div', 'account_id', 'account_nm']].iterrows():
        #    print(row['sj_div'],'\n', row['account_id'],'\n', row['account_nm'])
        #    print("--")
            
        #hangul = re.compile('[^ \(\)ㄱ-ㅣ가-힣]+') # 한글과 띄어쓰기, 괄호를 제외한 모든 글자
        hangul = re.compile('[^\(\)ㄱ-ㅣ가-힣]+') # 한글과 괄호를 제외한 모든 글자
        regex = "\(.*\)|\s-\s.*" # 괄호와 괄호안의 내용
        
        def convert_name(rawName):
            replaced = hangul.sub('', rawName)
            
            #return replaced.strip()
            return re.sub(regex, '', replaced)

        df1.account_nm = df1.account_nm.apply(convert_name)
                
        def GetCell(df, divs, ids, names):
            
            for div in divs:
                result_div = (df.sj_div == div)
                if len(df.loc[result_div]) == 0:
                    #print("case1", div)
                    continue
                for aid in ids:
                    result_aid = result_div & (df.account_id == aid)
                    if len(df.loc[result_aid]) > 0:
                        return result_aid
                    #print("case2", aid)
                        
                for name in names:
                    #replaced = hangul.sub('', df.account_nm)
                    #replaced.strip()
                    result_name = result_div & (df1.account_nm == name)
                    #print(
                    if len(df.loc[result_name]) > 0:
                        return result_name
                    #print("case3", name)
                        
            return None        

       
        # 다른 컨디션에 포함되는것도 제외가능함 
        # 컨디션차원의 우선순위
        #condition = (df1.sj_div == 'BS') & ((df1.account_id == 'ifrs-full_CurrentAssets')|(df1.account_nm == '유동자산')) # 유동자산
        condition = GetCell(df1, ('BS',), ('ifrs-full_CurrentAssets',), self.NameList_유동자산)
        #condition_2 = (df1.sj_div == 'BS') & (df1.account_id == 'ifrs-full_Liabilities') # 부채총계
        condition_2 = GetCell(df1, ('BS',), ('ifrs-full_Liabilities',), self.NameList_부채총계)
        #condition_3 = (df1.sj_div == 'BS') &  ((df1.account_id == 'ifrs-full_Equity')|(df1.account_nm == '자본총계'))  #자본총계
        condition_3 = GetCell(df1, ('BS',), ('ifrs-full_Equity', 'ifrs_Equity',), self.NameList_자본총계)
        # 손익계산서 부분
        #condition_4 = ((df1.sj_div == 'IS')|(df1.sj_div == 'CIS')) & ((df1.account_id == 'ifrs-full_Revenue')|(df1.account_nm == '영업수익')|(df1.account_nm == '매출액')) # 매출액
        condition_4 = GetCell(df1, ('CIS', 'IS',), ('ifrs-full_Revenue','ifrs_Revenue',), self.NameList_매출액)
        #condition_5 = ((df1.sj_div == 'IS')|(df1.sj_div == 'CIS')) & ((df1.account_id == 'ifrs-full_GrossProfit')|(df1.account_nm == '매출총이익'))
        condition_5 = GetCell(df1, ('CIS', 'IS',), ('ifrs-full_GrossProfit','ifrs_GrossProfit',), self.NameList_매출총이익)
              
        #condition_6 = ((df1.sj_div == 'IS')|(df1.sj_div == 'CIS')) & ((df1.account_id == 'dart_OperatingIncomeLoss') | (df1.account_nm == '영업이익'))
        condition_6 = GetCell(df1, ('CIS', 'IS',), ('dart_OperatingIncomeLoss',),self.NameList_영업이익)
        
        #condition_7 = ((df1.sj_nm == '손익계산서') | (df1.sj_nm == '포괄손익계산서')) & ((df1.account_nm == '당기순이익(손실)') | (df1.account_nm == '당기순이익') | (df1.account_nm == '분기순이익') | (df1.account_nm == '분기순이익(손실)') | (df1.account_nm == '반기순이익') | (df1.account_nm == '반기순이익(손실)') |(df1.account_nm == '연결분기순이익') | (df1.account_nm == '연결반기순이익')| (df1.account_nm == '연결당기순이익')|(df1.account_nm == '연결분기(당기)순이익')|(df1.account_nm == '연결반기(당기)순이익')|(df1.account_nm == '연결분기순이익(손실)'))
        #condition_7 = ((df1.sj_div == 'IS')|(df1.sj_div == 'CIS')) & ((df1.account_id == 'ifrs-full_ProfitLoss') |(df1.account_nm == '당기순이익(손실)') | (df1.account_nm == '당기순이익') | (df1.account_nm == '분기순이익') | (df1.account_nm == '분기순이익(손실)') | (df1.account_nm == '반기순이익') | (df1.account_nm == '반기순이익(손실)') |(df1.account_nm == '연결분기순이익') | (df1.account_nm == '연결반기순이익')| (df1.account_nm == '연결당기순이익')|(df1.account_nm == '연결분기(당기)순이익')|(df1.account_nm == '연결반기(당기)순이익')|(df1.account_nm == '연결분기순이익(손실)'))
        condition_7 = GetCell(df1, ('CIS', 'IS',), ('ifrs-full_ProfitLoss',), self.NameList_당기순이익)

        #condition_8 = (df1.sj_div == 'CF') & ((df1.account_id == 'ifrs_CashFlowsFromUsedInOperatingActivities') |(df1.account_id == 'ifrs-full_CashFlowsFromUsedInOperatingActivities')| (df1.account_nm =="영업활동으로 인한 현금흐름") | (df1.account_nm =="영업활동으로부터의 순현금유입") |(df1.account_nm =="영업활동으로 인한 순현금흐름") | ( df1.account_nm =='영업활동으로 인한 순현금흐름 합계')| ( df1.account_nm =='영업활동순현금흐름 합계')| ( df1.account_nm =='영업활동현금흐름'))
        condition_8 = GetCell(df1, ('CF',), ('ifrs-full_CashFlowsFromUsedInOperatingActivities', 'ifrs_CashFlowsFromUsedInOperatingActivities',), self.NameList_영업현금흐름) 
        
        #condition_9 = (df1.sj_div == 'CF') & ((df1.account_id == 'ifrs-full_CashFlowsFromUsedInInvestingActivities')|(df1.account_nm =="투자활동으로 인한 순현금흐름")| (df1.account_nm =="투자활동으로 인한 현금흐름") | ( df1.account_nm =='투자활동으로 인한 순현금흐름 합계') |(df1.account_nm =='투자활동으로부터의 순현금유출')| ( df1.account_nm =='투자활동순현금흐름 합계')| ( df1.account_nm =='투자활동현금흐름'))
        condition_9 = GetCell(df1, ('CF',), ('ifrs-full_CashFlowsFromUsedInInvestingActivities', 'ifrs_CashFlowsFromUsedInInvestingActivities',), self.NameList_투자현금흐름)
        
        #condition_10 = (df1.sj_div == 'CF') & ((df1.account_id == 'ifrs-full_CashFlowsFromUsedInFinancingActivities')| (df1.account_nm =='재무활동으로부터의 순현금유입(유출)')| (df1.account_nm =="재무활동으로 인한 현금흐름") |(df1.account_nm =="재무활동으로 인한 순현금흐름")| ( df1.account_nm =='재무활동으로 인한 순현금흐름 합계') | ( df1.account_nm =='재무활동순현금흐름 합계')| ( df1.account_nm =='재무활동현금흐름'))
        condition_10 = GetCell(df1, ('CF',), ('ifrs-full_CashFlowsFromUsedInFinancingActivities', 'ifrs_CashFlowsFromUsedInFinancingActivities',),self.NameList_재무현금흐름)

        def amountTextToNumber(text):
            if text == "":
                return 0
            return int(text)
            
        def verify(df, condition, desc, replaced = None):
            if condition is None:
                rea = "quater report) {0} {1} {2} cfs.{4} {3}  None".format( code, year, quaterText, desc, CFS)
                logger.warning(rea)
                return replaced
        
            locResult = df.loc[condition]
            if len(locResult) != 1:
                rea = "quater report) {0} {1} {2} cfs.{3} {4} {5}".format( code, year, quaterText, CFS,desc, len(locResult))
                logger.warning(rea)
                return replaced


            return amountTextToNumber(locResult.iloc[0]['thstrm_amount'])
            
        def A_minus_sumBCD(A, B, C=0, D=0):
            try:
                return A - (B+C+D)
            except TypeError:
                return None
        try:
            current_assets = verify(df1, condition, "유동자산") # 유동자산
            liabilities = verify(df1, condition_2, "부채총계") #뷰채총계
            equity = verify(df1, condition_3, "자본") #자본
            revenue = verify(df1, condition_4, "매출액") #매출액
                    
            
            income = verify(df1, condition_6, "영업이익")   
            grossProfit = verify(df1, condition_5, "매출총이익", income)   
            
            net_income = 0
            if not(condition_7 is None):
                net_income = verify(df1, condition_7, "당기순이익")   
            else:
                #condition_7 = ((df1.sj_div == 'IS')|(df1.sj_div == 'CIS')) & (df1.account_id == 'ifrs-full_ProfitLossBeforeTax')
                condition_7 = GetCell(df1, ('CIS', 'IS',), ('ifrs-full_ProfitLossBeforeTax',), self.NameList_당기순이익_세전)
                
                
                #condition_7_2 = ((df1.sj_div == 'IS')|(df1.sj_div == 'CIS')) & (df1.account_id == 'ifrs-full_IncomeTaxExpenseContinuingOperations')
                condition_7_2 = GetCell(df1, ('CIS', 'IS',), ('ifrs-full_IncomeTaxExpenseContinuingOperations',), self.NameList_당기순이익_세금)             
                net_income = A_minus_sumBCD(verify(df1, condition_7, "당기순이익(세전)"), verify(df1, condition_7_2, "당기순이익 세금)", 0)) #당기순이익
            cfo = verify(df1, condition_8, "영업활동 현금흐름") # 영업활동 현금흐름
            cfi = verify(df1, condition_9, "투자활동 현금흐름") #투자활동 현금흐름
            cff = verify(df1, condition_10, "재무활동 현금흐름") #재무활동 현금흐름
            if cfo is None or cfi is None or cff is None:
                fcf = None
            else:
                fcf = (cfo + cfi + cff) #잉여현금 흐름
        
            #if len(df1.loc[condition]) > 1:
            #    print(code, quaterText, "condition multipl"
        
        except  Exception as e:

            #for idx,row in df1[['sj_div', 'account_id', 'account_nm']].iterrows():
            #    print(row['sj_div'],'\n', row['account_id'],'\n', row['account_nm'])
            #    print("--")

            
            print(e)
            print(code, quaterText)
            print(len(df1.loc[condition]), len(df1.loc[condition_2]), len(df1.loc[condition_3]), len(df1.loc[condition_4]), len(df1.loc[condition_5]), len(df1.loc[condition_6]), len(df1.loc[condition_7]), len(df1.loc[condition_8]), len(df1.loc[condition_9]), len(df1.loc[condition_10]))
            '''
            print(df1.loc[condition].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_2].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_3].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_4].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_5].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_6].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_7].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_7_2].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_8].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_9].iloc[0]['thstrm_amount'])
            print(df1.loc[condition_10].iloc[0]['thstrm_amount'])
            '''
        
        
        tup_data= (current_assets, liabilities, equity, revenue, grossProfit, income, net_income, cfo, cfi, cff,fcf)
        series_data = Series(tup_data, index = ['유동자산', '부채총계', '자본총계', '매출액', '매출총이익', '영업이익', '당기순이익', '영업활동현금흐름', '투자활동현금흐름','재무활동현금흐름','잉여현금흐름'])
        emptyTup = (0, 0, 0, 0, 0, 0, 0, 0,0, 0,0)
        empty_data = Series(emptyTup, index = ['유동자산', '부채총계', '자본총계', '매출액', '매출총이익', '영업이익', '당기순이익', '영업활동현금흐름', '투자활동현금흐름','재무활동현금흐름', '잉여현금흐름'])
      
        
      
        if quaterText == '4Q':
            
        
            Data_1Q = self.GetQuaterReport( code, year, '1Q', possibleVersion,CFS)
            Data_2Q = self.GetQuaterReport( code, year, '2Q', possibleVersion, CFS)
            Data_3Q = self.GetQuaterReport( code, year, '3Q', possibleVersion,CFS)
            
                
            Data_Prev = Data_3Q
            if Data_Prev is None:
                Data_Prev = Data_2Q
            if Data_Prev is None:
                Data_Prev = Data_1Q
            if Data_Prev is None:
                Data_Prev = empty_data

                
            if Data_1Q is None:
                Data_1Q = empty_data
            if Data_2Q is None:
                Data_2Q = empty_data                               
            if Data_3Q is None:
                Data_3Q = empty_data

            series_data['매출액'] = A_minus_sumBCD(series_data['매출액'],Data_1Q['매출액'] , Data_2Q['매출액'] , Data_3Q['매출액'])
            series_data['매출총이익'] = A_minus_sumBCD(series_data['매출총이익'],Data_1Q['매출총이익'] , Data_2Q['매출총이익'] , Data_3Q['매출총이익'])
            series_data['영업이익'] = A_minus_sumBCD(series_data['영업이익'],Data_1Q['영업이익'] , Data_2Q['영업이익'] , Data_3Q['영업이익'])
            series_data['당기순이익'] = A_minus_sumBCD(series_data['당기순이익'],Data_1Q['당기순이익'] , Data_2Q['당기순이익'] , Data_3Q['당기순이익'])
            series_data['잉여현금흐름'] = A_minus_sumBCD(series_data['잉여현금흐름'] ,Data_1Q['잉여현금흐름'] , Data_2Q['잉여현금흐름'] , Data_3Q['잉여현금흐름'])
            series_data['영업활동현금흐름'] = A_minus_sumBCD(series_data['영업활동현금흐름'],Data_1Q['영업활동현금흐름'] , Data_2Q['영업활동현금흐름'] , Data_3Q['영업활동현금흐름'])
            series_data['투자활동현금흐름'] = A_minus_sumBCD(series_data['투자활동현금흐름'] ,Data_1Q['투자활동현금흐름'] , Data_2Q['투자활동현금흐름'] , Data_3Q['투자활동현금흐름'])
            series_data['재무활동현금흐름'] = A_minus_sumBCD(series_data['재무활동현금흐름'] ,Data_1Q['재무활동현금흐름'] , Data_2Q['재무활동현금흐름'] , Data_3Q['재무활동현금흐름'])
        elif quaterText == '2Q':

            Data_1Q = self.GetQuaterReport( code, year, '1Q',possibleVersion, CFS)
            if Data_1Q is None:
                Data_1Q = empty_data             
            series_data['영업활동현금흐름'] =  A_minus_sumBCD(series_data['영업활동현금흐름'] , Data_1Q['영업활동현금흐름'])
            series_data['투자활동현금흐름'] =  A_minus_sumBCD(series_data['투자활동현금흐름'] , Data_1Q['투자활동현금흐름'])
            series_data['재무활동현금흐름'] =  A_minus_sumBCD(series_data['재무활동현금흐름'] ,Data_1Q['재무활동현금흐름'])
        elif quaterText == '3Q':
            Data_1Q = self.GetQuaterReport( code, year, '1Q', possibleVersion,CFS)
            if Data_1Q is None:
                Data_1Q = empty_data    
            Data_2Q = self.GetQuaterReport( code, year, '2Q',possibleVersion, CFS)
            if Data_2Q is None:
                Data_2Q = empty_data
            series_data['영업활동현금흐름'] =  A_minus_sumBCD(series_data['영업활동현금흐름'] ,Data_1Q['영업활동현금흐름'], Data_2Q['영업활동현금흐름'])
            series_data['투자활동현금흐름'] =  A_minus_sumBCD(series_data['투자활동현금흐름'],Data_1Q['투자활동현금흐름'], Data_2Q['투자활동현금흐름'])
            series_data['재무활동현금흐름'] =  A_minus_sumBCD(series_data['재무활동현금흐름'] ,Data_1Q['재무활동현금흐름'] , Data_2Q['재무활동현금흐름'] )
        
        

        targetString = "{0}(shcode, year, quater, CFS, account, amount)".format(tableName)
        rowList = []
        rawNo_string = df1["rcept_no"][0][0:4+2+2] # ex) 20200401
        dateObj = datetime.strptime (rawNo_string, "%Y%m%d")

        succData = [(code, str(year), quaterText, CFS_InDB,'Version', ReportManager.QuaterReportVersion),
                (code, str(year), quaterText, CFS_InDB,'Timestamp', int(curTime)),
                (code, str(year), quaterText, CFS_InDB,'Date', datetime.timestamp(dateObj))]
        for index, value  in series_data.items():         
            rowList.append((code, str(year), quaterText, CFS_InDB, index, value))   
       
        rowList.extend(succData)
        sqlMgr.UpsertRowList(targetString, "shcode, year, quater, CFS, account" ,rowList)
            
        
                
                
            
            
        return series_data