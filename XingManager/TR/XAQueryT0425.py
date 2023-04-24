
import struct
import time
from XingCommand import XingQueryCommand

from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.T0425")
logger = logMgr.logger

__imple__ = 'Command_XAQueryT0425'
# 계좌 잔고 조회

class Command_XAQueryT0425(XingQueryCommand):
    ResFileName = ".\\Res\\t0425.res"
    #override
    def Init(self):
        self.allCount = 0
        self.byteDataList = []
        self.metadata = {}
        self.metadata['Length'] = 0
        
        self.inst.SetFieldData("t0425InBlock", "accno", 0, self.input_accno)
        self.inst.SetFieldData("t0425InBlock", "passwd", 0, self.input_passwd)
        self.inst.SetFieldData("t0425InBlock", "expcode", 0, self.input_expcode)
        self.inst.SetFieldData("t0425InBlock", "chegb", 0, "0")
        self.inst.SetFieldData("t0425InBlock", "medosu", 0, "0")
        self.inst.SetFieldData("t0425InBlock", "sortgb", 0, "2") # 주문번호 순 (1은 역순)
        self.inst.SetFieldData("t0425InBlock", "cts_ordno", 0, "")
        
        
        
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName, LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
    
    #override
    def IsContinuous(self):
        result = self.inst.GetFieldData("t0425OutBlock", "cts_ordno",0)
        if result != "":
            return True
        return False
        
    #override
    def InitForContinuation(self):
        
        result = self.inst.GetFieldData("t0425OutBlock", "cts_ordno",0)
        self.inst.SetFieldData("t0425InBlock", "cts_ordno", 0, result)
        #print("연속 조회 처리 중..", result)
        logger.debug("연속 조회 처리 중.. {0}".format( result))
    
    #override
    def OnReceiveData(self, code):
   
        #print("start")
        # bytearray를 리스트형태로 append함. ToBytes에서 그 리스트를 반환함.
        try:
            curCount = self.inst.GetBlockCount("t0425OutBlock1")
            self.allCount = self.allCount + curCount
            tr = self.inst 
            
            metadata = self.metadata
            metadata['Format'] = '48siii80siid'      
            metadata['MemberFormat'] = [
            ("ordno", "string", 12*4), 
            ("janqty", None, 4), 
            ("pamt", None, 4), 
            ("mamt", None, 4), 
            ("hname", "string", 20*4), 
            ("appamt", None, 4), 
            ("dtsunik", None, 4), 
            ("sunikrt", None, 8)]
            

            sizePerRow = struct.calcsize(metadata['Format'])
            totalBytes = (sizePerRow) * curCount        
            refinedBytearray = bytearray(totalBytes) 
            metadata['Length'] = metadata['Length'] + totalBytes
            metadata['Count'] = self.allCount
            for i in range(curCount):
                startByte = sizePerRow * i
                
                ordno = tr.GetFieldData("t0425OutBlock1", "ordno", i)
                expcode = tr.GetFieldData("t0425OutBlock1", "expcode", i).encode('utf-8').ljust(metadata['MemberFormat'][0][2], b'\0')
                print(ordno, expcode
                , tr.GetFieldData("t0425OutBlock1", "medosu", i)
                , tr.GetFieldData("t0425OutBlock1", "qty", i)
                , tr.GetFieldData("t0425OutBlock1", "price", i)
                , tr.GetFieldData("t0425OutBlock1", "cheqty", i)
                , tr.GetFieldData("t0425OutBlock1", "cheprice", i)
                , tr.GetFieldData("t0425OutBlock1", "ordrem", i)
                , tr.GetFieldData("t0425OutBlock1", "cfmqty", i)
                , tr.GetFieldData("t0425OutBlock1", "status", i)
                , tr.GetFieldData("t0425OutBlock1", "orgordno", i)
                , tr.GetFieldData("t0425OutBlock1", "ordgb", i)
                , tr.GetFieldData("t0425OutBlock1", "ordtime", i)
                , tr.GetFieldData("t0425OutBlock1", "ordermtd", i)
                , tr.GetFieldData("t0425OutBlock1", "sysprocseq", i)
                , tr.GetFieldData("t0425OutBlock1", "hogagb", i)
                , tr.GetFieldData("t0425OutBlock1", "price1", i)
                , tr.GetFieldData("t0425OutBlock1", "orggb", i))

                
                
                '''
                
                janqty = int(tr.GetFieldData("t0425OutBlock1", "janqty", i))
                pamt = int(tr.GetFieldData("t0425OutBlock1", "pamt", i))
                mamt = int(tr.GetFieldData("t0425OutBlock1", "mamt", i))
                hname = tr.GetFieldData("t0425OutBlock1", "hname", i).encode('utf-8').ljust(metadata['MemberFormat'][4][2], b'\0')
                appamt = int(tr.GetFieldData("t0425OutBlock1", "appamt", i))
                dtsunik = int(tr.GetFieldData("t0425OutBlock1", "dtsunik", i))
                sunikrt = float(tr.GetFieldData("t0425OutBlock1", "sunikrt", i))
                '''
                
                #pack_result = struct.pack(metadata['Format'], expcode, janqty, pamt, mamt, hname, appamt, dtsunik, sunikrt)
                #refinedBytearray[startByte : startByte + sizePerRow] = pack_result
                
            #self.byteDataList.append(refinedBytearray)
        except Exception as e:          
            logger.error("0425 onReceive Error : {0}".format(e))
    #override
    def OnFinish(self, result):
        if not result:
            return
                      
                      
        

        
        tr = self.inst 
        '''
        self.sunamt = tr.GetFieldData("t0424OutBlock", "sunamt",0)
        self.dtsunik = tr.GetFieldData("t0424OutBlock", "dtsunik",0)
        self.mamt = tr.GetFieldData("t0424OutBlock", "mamt",0)
        self.tappamt = tr.GetFieldData("t0424OutBlock", "tappamt",0)
        self.tdtsunik = tr.GetFieldData("t0424OutBlock", "tdtsunik",0)

        print(tr.GetFieldData("t0424OutBlock1", "hname", 0))
        print(tr.GetFieldData("t0424OutBlock1", "jangb", 0))
        print(tr.GetFieldData("t0424OutBlock1", "janqty", 0))
        '''
        #
        
        
    @classmethod
    def Create(cls, parentCommandID, accno, passwd, shcode):
        newCommand = cls(parentCommandID)
        newCommand.input_accno = accno
        newCommand.input_passwd = passwd 
        newCommand.input_expcode = shcode   
        return newCommand
        
    def ToBytes(self):
        tr = self.inst

        
        #print(len(blockDataEncoded), count)
        
        
        
        #print("tobytes", self.metadata)
        return(self.metadata, self.byteDataList)
    