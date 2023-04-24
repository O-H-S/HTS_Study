from Common.Command import Command, SyncCommand
from datetime import datetime, timedelta

from pandas import Series, DataFrame

from .Price_Day import StaticPriceCollector
from .Price_Realtime import RealtimePriceCollector

import struct, time
import DataManagement.SearchLineController as SLC
import mmap

from Common.GlobalLogging import LogManager
logMgr = LogManager("Main.DM.PriceManager")
logger = logMgr.logger




class PriceManager:
    def __init__(self, dataMgr):
        self.dataMgr = dataMgr
            
        self.RealtimeCollector = RealtimePriceCollector(dataMgr)
        self.StaticPriceCollector = StaticPriceCollector(dataMgr)
        
        self.dataMgr.AddMessageHandler("GetSectorPrice_Tick_Result", self.__OnArriveResult_Sector)
        
    
    # 임시 사용 중지
    def GetCurrentPrice(self, codeList):
        Command_GSP = SyncCommand()     
        self.dataMgr.SendMessageToManagerAsync("GetCurPrice", (Command_GSP.ID, codeList, None))
        Command_GSP.prices = None
        Command_GSP.Start()
        return Command_GSP.prices

    def GetRecentPrice(self, targetCode):
        return self.RealtimeCollector.CurPrices[code]

    def GetSectorPrice_Tick(self, sectorCode, tickSize, count):
        Command_GSPT = SyncCommand()     
        self.dataMgr.SendMessageToManagerAsync("GetSectorPrice_Tick", (Command_GSPT.ID, sectorCode, tickSize, count))
        Command_GSPT.prices = None

        Command_GSPT.Start()
        return Command_GSPT.prices

         
    def __OnArriveResult_Sector(self, args):
        logger.debug("[DataManager] 업종 가격(틱) 조회 메세지 결과 수신")
        metadata = args[-1]
        
        df = None
        logger.debug("[DataManager] 업종 가격(틱) 데이터 읽는 중... (길이:{0})(데이터 수:{1})".format(metadata['Length'],metadata['Count']))
        if  metadata["Result"] and metadata['Length'] > 0:
            mm = mmap.mmap(-1, metadata['Length'], metadata['MemName'])
            mm.seek(0)
            bytesOfStocks = mm.read(metadata['Length'])
            #print(bytesOfStocks, len(bytesOfStocks))
            self.dataMgr.ReleaseMem(metadata['MemName'])
            #print(metadata)
            #print(struct.calcsize(metadata['Format']))
            df = self.dataMgr.ReadByteByFormat(metadata, bytesOfStocks)
        if metadata["Result"] :
            logger.debug("[DataManager] 업종 가격(틱) 데이터 읽기 완료")
        else:
            logger.debug("[DataManager] 업종 가격(틱) 데이터 읽기 실패")
        
        
        #print(df)
        
        if args[0] < 0:
            return
        
        command = Command.Get(args[0])

        command.prices = df
        command.result = metadata["Result"]
       
        #print(df)
        command.End(metadata["Result"])

    
    