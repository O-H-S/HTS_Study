from Common.GlobalLogging import LogManager
logMgr = LogManager("Main.DM.Price.Realtime")
logger = logMgr.logger


import mmap, threading, time
from Common.Command import Command, SyncCommand
from datetime import datetime, timedelta
from pandas import Series, DataFrame

from Common.ThreadPool import ThreadPoolExecutorStackTraced as ThreadPoolExecutor


class CodePackage:
    def __init__(self):
        self.Count = 0
        self.PackedString = ""
        self.lastRequestTime = 0
        
        
        
    def AddCode(self, code):
        startPos = self.Count * 6
        self.PackedString = "".join([self.PackedString, code])
        self.Count = self.Count + 1
        #print(self.PackedString)
        return [(code, self.Count-1)]
        
    def RemoveCode(self, code, index):
        if index == self.Count -1:
            self.PackedString = self.PackedString[:-6]
            self.Count = self.Count -1
            #print("removed ", self.PackedString)
            return [(code, -1)]
    
        lastCode = self.PackedString[-6:]
        startPos = index * 6
        #for i in range(0, 6):        
        #    self.PackedString[i + startPos] = lastCode[i]
        self.PackedString ="".join([self.PackedString[:startPos], lastCode, self.PackedString[startPos + 6:-6]])
        #print("removed ", self.PackedString)
        self.Count = self.Count -1
        
        return [(lastCode, index), (code, -1)]

class RealtimePriceCollector:
    def __init__(self, dataMgr):
        self.dataMgr = dataMgr
        self.dataMgr.AddMessageHandler("GetCurPrice_Result", self.__OnArriveResult)
        
        self.CurPrices = {}
        self.OnUpdatePricesHandlers = []
        
        self.UpdatingCurPrices = threading.Thread(target = self.__updateCurPrices, name="RealtimePriceCollector")
        self.UpdatingCurPrices.start()
        
        self.Packages = []       
        self.CodeToPackage = {}
        
    # =========== 등록된 실시간 리스트 조회 쓰레드 ===========
    def __updateCurPrices(self):
        while True:
            if not self.dataMgr.serverConnected:
                logger.debug("서버 연결 상태 불량.. 5초간 대기")
                time.sleep(5)
                continue
                
            if self.dataMgr.isClosing:
                logger.debug("DataManager가 닫히는 중... 쓰레드를 종료합니다")
                break
            
            curTime = time.time()
            for pack in self.Packages:
                if pack.Count > 0 and pack.lastRequestTime + 1.5 < curTime:
                    
                    self.dataMgr.SendMessageToManagerAsync("GetCurPrice", (-1, None, pack.PackedString[:]))
                    pack.lastRequestTime = time.time()
            time.sleep(0.5)
            
    # ============ 실시간 가격 조회 등록, 해제 관련 ==================
    def Register(self, code):
        if len(code) != 6:
            logger.error("unmatched length")
            return False
    
        if code in self.CodeToPackage:
            return False
        
        targetPackage = None
        for pack in self.Packages:
            if pack.Count < 50:
                targetPackage = pack
                break
        
        if targetPackage is None:
            targetPackage = CodePackage()
            self.Packages.append(targetPackage)
        self.CodeToPackage[code] = (targetPackage, -1)
        changes = targetPackage.AddCode(code)      
        # (code, idx) idx가 -1이면 패키지에서 사라진 것
        self.__applyChangesFromPackage(targetPackage,changes)
        return True
        
    def Unregister(self, code):
        if len(code) != 6:
            logger.error("unmatched length")
            return False
        if not(code in self.CodeToPackage):
            return False
        
        packageIn = self.CodeToPackage[code][0]
        indexAt = self.CodeToPackage[code][1]  
        
        changes = packageIn.RemoveCode(code, indexAt)
        self.__applyChangesFromPackage(packageIn,changes)
    
    def __applyChangesFromPackage(self, package, changes):
        for change in changes:
            code = change[0]
            newIdx = change[1]
            
            if newIdx < 0:
                del self.CodeToPackage[code]
            else:
                self.CodeToPackage[code] = (package, newIdx)
                
    def GetAllPackageSize(self):
        allCount = 0
        for pack in self.Packages:
            allCount = pack.Count + allCount
        return allCount
    # ============ 실시간 가격 업데이트 관련 ==================
    def __updateCurrentPrices(self, prices):
        curTime = time.time()
        for idx, row in prices.iterrows():
            code = row['shcode']
            self.CurPrices[code] = (row, curTime)
            
        for handler in self.OnUpdatePricesHandlers:
            handler(prices)
    
    def __OnArriveResult(self, args):
        logger.debug("[DataManager] 현재가(멀티) 조회 메세지 결과 수신")
        metadata = args[-1]
        
        df = None
        logger.debug("[DataManager] 현재가(멀티) 데이터 읽는 중... (길이:{0})(종목 수:{1})".format(metadata['Length'],metadata['Count']))
        if  metadata["Result"] and metadata['Length'] > 0:
            mm = mmap.mmap(-1, metadata['Length'], metadata['MemName'])
            mm.seek(0)
            bytesOfStocks = mm.read(metadata['Length'])
            #print(bytesOfStocks, len(bytesOfStocks))
            self.dataMgr.ReleaseMem(metadata['MemName'])
            #print(metadata)
            #print(struct.calcsize(metadata['Format']))
            df = self.dataMgr.ReadByteByFormat(metadata, bytesOfStocks)
            self.__updateCurrentPrices(df)
        if metadata["Result"] :
            logger.debug("[DataManager] 현재가(멀티) 데이터 읽기 완료")
        else:
            logger.debug("[DataManager] 현재가(멀티) 데이터 읽기 실패")
        
        
        #print(df)
        
        if args[0] < 0:
            return
        
        command = Command.Get(args[0])
        command.prices = df
        command.result = metadata["Result"]
       
        #print(df)
        command.End(metadata["Result"])