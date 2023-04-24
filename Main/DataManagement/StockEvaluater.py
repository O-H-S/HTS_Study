
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager

import re, time
from pandas import Series, DataFrame
import math

logMgr = LogManager("Main.DM.SE")
logger = logMgr.logger

class StockEvaluater:



    def __init__(self, dataMgr, reportMgr):
        self.dataMgr = dataMgr
        self.ReportManager = reportMgr
        
    
        

    def GetRecentYearQuater(self, currentDatetime, earlyDay = 10):
        curMonth = currentDatetime.month
        curDay = currentDatetime.day
        
        Prev_Start_4Q = datetime(currentDatetime.year, 3, 30) - timedelta(days=earlyDay)
        Start_1Q = datetime(currentDatetime.year, 5, 15) - timedelta(days=earlyDay)
        Start_2Q = datetime(currentDatetime.year, 8, 15) - timedelta(days=earlyDay)
        Start_3Q = datetime(currentDatetime.year, 11, 15) - timedelta(days=earlyDay)
        
        if currentDatetime < Prev_Start_4Q:
            return (currentDatetime.year-1, '3Q')
        elif currentDatetime < Start_1Q:
            return (currentDatetime.year-1, '4Q')
        elif currentDatetime < Start_2Q:
            return (currentDatetime.year, '1Q')
        elif currentDatetime < Start_3Q:
            return (currentDatetime.year, '2Q')
        else:
            return (currentDatetime.year, '3Q')    
    
    
        

    def testReports(self, aStock, targetYear, targetQuater, reportType, loadedDF):
        def CheckReportAvailable(qReport, needAccounts):
            if qReport is None:
                return None, "전체"
            
            
            for ac in needAccounts:
                if not(ac in qReport) or qReport[ac] is None:
                    return None, ac
            return qReport, None
          
          
        def GetYearQuater(targetCode, currentYear, currentQuater, offsetYear, offsetCount):
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
    

        def GetQuaterReportFromDataFrame( shcode, yearAndquater, CFS):
            #print("GQRFDF", yearAndquater)
            #try:
            if CFS:
                CFS = 1
            else:
                CFS = 0
            targetReportDF = loadedDF[(yearAndquater[0], yearAndquater[1])]
            resultData = {}
            #print(targetReportDF)
            #print("key :" ,(shcode, yearAndquater[0], yearAndquater[1], CFS))
            try:
                targetDF = targetReportDF.loc[(shcode, yearAndquater[0], yearAndquater[1], CFS)]
            except:
                return None
            #print("TARGETDF:", targetDF)
            for index, value in targetDF['amount'].items():
                resultData[index] = value
            return resultData
            #except Exception as e:
                #print("ERROR: ",e)
                #return None


        '''
        prevY3Report = CheckReportAvailable(self.GetQuaterReportEX(aStock, GetYearQuater(aStock, curYear, 'Y', -3,0)))
        prevY2Report = CheckReportAvailable(self.GetQuaterReportEX(aStock, GetYearQuater(aStock, curYear, 'Y', -2,0)))
        prevYReport = CheckReportAvailable(self.GetQuaterReportEX(aStock, GetYearQuater(aStock, curYear, 'Y', -1,0)))
    

    
        prevQ3Report = CheckReportAvailable(self.GetQuaterReportEX(aStock, GetYearQuater(aStock, curYear, quater, 0, -3)))
        prevQ2Report = CheckReportAvailable(self.GetQuaterReportEX(aStock, GetYearQuater(aStock, curYear, quater, 0, -2)))
        prevQReport = CheckReportAvailable(self.GetQuaterReportEX(aStock, GetYearQuater(aStock, curYear, quater, 0, -1)))
        '''
        loadFunc = self.ReportManager.GetQuaterReportEX
        if loadedDF is not None:
            loadFunc = GetQuaterReportFromDataFrame
        
        report = loadFunc(aStock, GetYearQuater(aStock, targetYear, targetQuater, -1, 0), reportType)
        prevSameQReport, r1 = CheckReportAvailable(report,
        ['매출액', '영업이익', '당기순이익', '영업활동현금흐름'])
        
        prevQReport, r2 = CheckReportAvailable(loadFunc(aStock, GetYearQuater(aStock, targetYear, targetQuater, 0, -1), reportType),
        ['매출액', '영업이익', '당기순이익', '영업활동현금흐름'])
        
        curReport, r3 = CheckReportAvailable(loadFunc(aStock, (targetYear, targetQuater), reportType),
        ['매출액', '영업이익', '당기순이익', '영업활동현금흐름'])
        
        score = {}
                  
        if curReport is None or prevQReport is None or prevSameQReport is None :
        

            reasonTextList = ["보고서 누락"]
            if curReport is None:
                reasonTextList.append("/최근."+r3)
            if prevQReport is None:
                reasonTextList.append("/전분기."+r2)
            if prevSameQReport is None:
                reasonTextList.append("/전년동기."+r1)
 
            return (False, {'grade' : 'B', 'reason': ''.join(reasonTextList)})
            
        if curReport['매출액'] == 0:
            curReport['매출액'] = 1
        OperatingIncomeRatio = (curReport['영업이익'] / curReport['매출액']) * 100
        if  OperatingIncomeRatio < 5.0 or curReport['영업활동현금흐름'] < 0 or curReport['영업이익'] < 0 or curReport['당기순이익'] < 0 or curReport['투자활동현금흐름'] > 0:
            #print("Hazard(최근 분기): ", OperatingIncomeRatio, curReport['영업활동현금흐름'], curReport['영업이익'], curReport['당기순이익'], curReport['투자활동현금흐름'])

            return (True, {'grade' : 'B', 'reason': '재무 위험 요인(최근 분기)'})
    
        if prevQReport['영업이익'] == 0:
            prevQReport['영업이익'] = 1  
        OperatingIncomeDelta_prevQ = ((curReport['영업이익'] - prevQReport['영업이익']) / prevQReport['영업이익']) * 100
        if OperatingIncomeDelta_prevQ < -20.0 or (curReport['영업활동현금흐름'] + prevQReport['영업활동현금흐름']) < 0 :
            #print("Hazard(전분기 대비):", OperatingIncomeDelta_prevQ, str((curReport['영업활동현금흐름'] + prevQReport['영업활동현금흐름'])))
            return (True, {'grade' : 'B', 'reason': '재무 위험 요인(전분기 대비)'})
            
            
        if prevSameQReport['영업이익'] == 0:
            prevSameQReport['영업이익'] = 1  
        OperatingIncomeDelta_prevSameQ = ((curReport['영업이익'] - prevSameQReport['영업이익']) / prevSameQReport['영업이익']) * 100    
        if OperatingIncomeDelta_prevSameQ < -20.0 :
            #print("Hazard(전년동기 대비)")
            return (True, {'grade' : 'B', 'reason': '재무 위험 요인(전년동기 대비)'})
            
        
        return (True, {'grade' : 'G', 'reason': '잠재적 매수 대상'})
    
    def Evaluate(self, targetCode, targetYear, targetQuater, loadedDF = None): # 재무재표 데이터로 평가한다.
        
        resultTuple = self.testReports(targetCode, targetYear, targetQuater, True, loadedDF) # 연결 재무제표부터 테스트한다.
        existReports = resultTuple[0]
        score = resultTuple[1] 
        
        if existReports is True:
            score['reason'] = score['reason'] + "[연]"
            return score
        
        resultTuple = self.testReports(targetCode, targetYear, targetQuater, False, loadedDF) # 별도 재무제표 평가
        existReports = resultTuple[0]
        score = resultTuple[1]
        score['reason'] = score['reason'] + "[별]"
        return score
        
        
        
                                
            