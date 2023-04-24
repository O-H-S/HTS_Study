
import struct
import time
from XingCommand import XingQueryCommand

from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.T0424")
logger = logMgr.logger

__imple__ = 'Command_XAQueryT0424'
# 계좌 잔고 조회

class Command_XAQueryT0424(XingQueryCommand):
    ResFileName = ".\\Res\\t0424.res"
    #override
    def Init(self):
        self.allCount = 0
        self.byteDataList = []
        self.metadata = {}
        self.metadata['Length'] = 0
        
        self.inst.SetFieldData("t0424InBlock", "accno", 0, self.input_accno)
        self.inst.SetFieldData("t0424InBlock", "passwd", 0, self.input_passwd)
        self.inst.SetFieldData("t0424InBlock", "prcgb", 0, "1")
        self.inst.SetFieldData("t0424InBlock", "chegb", 0, "0")
        self.inst.SetFieldData("t0424InBlock", "dangb", 0, "0")
        self.inst.SetFieldData("t0424InBlock", "charge", 0, "1")
        self.inst.SetFieldData("t0424InBlock", "cts_expcode", 0, "")
        
        
        
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName, LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
    
    #override
    def IsContinuous(self):
        result = self.inst.GetFieldData("t0424OutBlock", "cts_expcode",0)
        if result != "":
            return True
        return False
        
    #override
    def InitForContinuation(self):
        
        result = self.inst.GetFieldData("t0424OutBlock", "cts_expcode",0)
        self.inst.SetFieldData("t0424InBlock", "cts_expcode", 0, result)
        #print("연속 조회 처리 중..", result)
        logger.debug("연속 조회 처리 중.. {0}".format( result))
    
    #override
    def OnReceiveData(self, code):
        #print("start")
        # bytearray를 리스트형태로 append함. ToBytes에서 그 리스트를 반환함.
        try:      
 
            curCount = self.inst.GetBlockCount("t0424OutBlock1")

            self.allCount = self.allCount + curCount
            tr = self.inst 
            
            metadata = self.metadata
            metadata['Format'] = '48siii80siid'      
            metadata['MemberFormat'] = [
            ("expcode", "string", 12*4), 
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
                # 데이터의 문자열이 모두 숫자이므로 한글자당 1바이트로 취급가능하다.
                # memoryview로  string 사용 불가능
                # unsafe를 사용하여 string 내부의 바이트배열에 간접적으로 접근가능하긴하나 복잡해보임.
                expcode = tr.GetFieldData("t0424OutBlock1", "expcode", i).encode('utf-8').ljust(metadata['MemberFormat'][0][2], b'\0')
                janqty = int(tr.GetFieldData("t0424OutBlock1", "janqty", i))
                pamt = int(tr.GetFieldData("t0424OutBlock1", "pamt", i))
                mamt = int(tr.GetFieldData("t0424OutBlock1", "mamt", i))
                hname = tr.GetFieldData("t0424OutBlock1", "hname", i).encode('utf-8').ljust(metadata['MemberFormat'][4][2], b'\0')
                appamt = int(tr.GetFieldData("t0424OutBlock1", "appamt", i))
                dtsunik = int(tr.GetFieldData("t0424OutBlock1", "dtsunik", i))
                sunikrt = float(tr.GetFieldData("t0424OutBlock1", "sunikrt", i))
                
                #print(tr.GetFieldData("t8413OutBlock1", "close", i), tr.GetFieldData("t8413OutBlock1", "rate", i), tr.GetFieldData("t8413OutBlock1", "pricechk", i), tr.GetFieldData("t8413OutBlock1", "jongchk", i))
                pack_result = struct.pack(metadata['Format'], expcode, janqty, pamt, mamt, hname, appamt, dtsunik, sunikrt)
                refinedBytearray[startByte : startByte + sizePerRow] = pack_result
                #unpack_result = struct.unpack(metadata['Format'], pack_result)
                #print(unpack_result)
                #print(open_int, unpack_result[1])
                #print(len(refinedBytearray))
                #print(high)
                #print(type(high))
                #print(len(date.encode()) ,len(open2.encode()),len(high.encode()) ,len(low.encode()), len(close.encode()))
                #print(len(date) ,len(open2),len(high) ,len(low), len(close))
            #print(len(refinedBytearray), totalBytes)
            #print( self.metadata)
            #print(metadata)
            self.byteDataList.append(refinedBytearray)
        except Exception as e:          
            print(e)
            logger.error("0424 onReceive Error : {0}".format(e))
    #override
    def OnFinish(self, result):
        if not result:
            return
                      
                      
        

        
        tr = self.inst 
        self.sunamt = tr.GetFieldData("t0424OutBlock", "sunamt",0)
        self.dtsunik = tr.GetFieldData("t0424OutBlock", "dtsunik",0)
        self.mamt = tr.GetFieldData("t0424OutBlock", "mamt",0)
        self.tappamt = tr.GetFieldData("t0424OutBlock", "tappamt",0)
        self.tdtsunik = tr.GetFieldData("t0424OutBlock", "tdtsunik",0)
        '''
        print(tr.GetFieldData("t0424OutBlock1", "hname", 0))
        print(tr.GetFieldData("t0424OutBlock1", "jangb", 0))
        print(tr.GetFieldData("t0424OutBlock1", "janqty", 0))
        '''
        #
        
        
    @classmethod
    def Create(cls, parentCommandID, accno, passwd):
        newCommand = cls(parentCommandID)
        newCommand.input_accno = accno
        newCommand.input_passwd = passwd      
        return newCommand
        
    def ToBytes(self):
        tr = self.inst

        
        #print(len(blockDataEncoded), count)
        
        
        
        #print("tobytes", self.metadata)
        return(self.metadata, self.byteDataList)
    