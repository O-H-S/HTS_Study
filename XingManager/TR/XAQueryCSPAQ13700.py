
import struct
import time
from datetime import datetime, timedelta
from XingCommand import XingQueryCommand

from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.CSPAQ13700")
logger = logMgr.logger

__imple__ = 'Command_XAQueryCSPAQ13700'
# 계좌 잔고 조회

class Command_XAQueryCSPAQ13700(XingQueryCommand):
    ResFileName = ".\\Res\\CSPAQ13700.res"
    #override
    def Init(self):
        self.allCount = 0
        self.byteDataList = []
        self.metadata = {}
        self.metadata['Length'] = 0
        
        def DescToFormat(descs):
                stringElements = []
                resultFormat = ""
                for desc in descs:
                    eType = desc[1]
                    eSize = int(desc[2])
                    if eType == "string":
                        stringElements.append("{0}s".format(eSize))
                    elif eType == "long":                      
                        stringElements.append("i")
                    elif eType == "double":
                        stringElements.append("d")
                return "".join(stringElements)
     
        self.metadata['MemberFormat'] = [
        ("OrdDt", "string", 8*4), 
        ("OrdNo", "string", 10*4), 
        ("OrgOrdNo", "string", 10*4), 
        ("IsuNo", "string", 12*4), 
        ("BnsTpCode", "string", 1*4), 
        ("BnsTpNm", "string", 10*4), 
        ("OrdQty", "long", 4),
        ("OrdPrc", "double", 8),
        ("ExecQty", "long", 4),
        ("ExecPrc", "double", 8),
        ("ExecTrxTime", "string", 9*4), 
        ("LastExecTime", "string", 9*4), 
        ("AllExecQty", "long", 4),
        ("OrdTime", "string", 9*4)]
            
        self.metadata['Format'] = DescToFormat(self.metadata['MemberFormat'])
        self.metadata['Count'] = 0
        #print(self.metadata['Format'])
        
        self.inst.SetFieldData("CSPAQ13700InBlock1", "RecCnt", 0, "1")
        self.inst.SetFieldData("CSPAQ13700InBlock1", "AcntNo", 0, self.input_accno)
        self.inst.SetFieldData("CSPAQ13700InBlock1", "InptPwd", 0, self.input_passwd)
        self.inst.SetFieldData("CSPAQ13700InBlock1", "OrdMktCode", 0, '00')
        self.inst.SetFieldData("CSPAQ13700InBlock1", "BnsTpCode", 0, "0")
        self.inst.SetFieldData("CSPAQ13700InBlock1", "IsuNo", 0, "")
        self.inst.SetFieldData("CSPAQ13700InBlock1", "ExecYn", 0, "0") 
        self.inst.SetFieldData("CSPAQ13700InBlock1", "OrdDt", 0, self.input_date)
        self.inst.SetFieldData("CSPAQ13700InBlock1", "SrtOrdNo2", 0, "000000000")
        self.inst.SetFieldData("CSPAQ13700InBlock1", "BkseqTpCode", 0, "1") # 1: 정순으로 가져온다
        self.inst.SetFieldData("CSPAQ13700InBlock1", "OrdPtnCode", 0, "00")
        
        
        
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName, LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
    
    #override
    def IsContinuous(self):
        result = self.inst.GetFieldData("CSPAQ13700OutBlock1", "SrtOrdNo2",0)
       
        if result != "0":
            #print('len', len(result))
            return True
        return False
        
    #override
    def InitForContinuation(self):
        
        result = self.inst.GetFieldData("CSPAQ13700OutBlock1", "SrtOrdNo2",0)
        self.inst.SetFieldData("CSPAQ13700InBlock1", "SrtOrdNo2", 0, result)
        #print("연속 조회 처리 중..", result)
        logger.debug("연속 조회 처리 중.. {0}".format( result))
    
    #override
    def OnReceiveData(self, code):
   
        #print("start")
        # bytearray를 리스트형태로 append함. ToBytes에서 그 리스트를 반환함.
        try:
            curCount = self.inst.GetBlockCount("CSPAQ13700OutBlock3")
            
            if curCount < 1:
                return
            
            self.allCount = self.allCount + curCount
            tr = self.inst 
            
            metadata = self.metadata
            def getListOfMember(index):
                vaList = []
                for entry in metadata['MemberFormat']:
                    entryName = entry[0]
                    entryType = entry[1]
                    entrySize = entry[2]
                    va = None
                    if entryType == "string":
                        va = tr.GetFieldData("CSPAQ13700OutBlock3", entryName, index).encode('utf-8').ljust(entrySize, b'\0')
                    elif entryType == "long":
                        va = int(tr.GetFieldData("CSPAQ13700OutBlock3", entryName, index))
                    elif entryType == "double":
                        va = float(tr.GetFieldData("CSPAQ13700OutBlock3", entryName, index))
                    vaList.append(va)
                return vaList
                        
            sizePerRow = struct.calcsize(metadata['Format'])
            totalBytes = (sizePerRow) * curCount        
            refinedBytearray = bytearray(totalBytes) 
            metadata['Length'] = metadata['Length'] + totalBytes
            metadata['Count'] = self.allCount
            for i in range(curCount):
                startByte = sizePerRow * i
                
                memList = getListOfMember(i)
                pack_result = struct.pack(metadata['Format'], *memList)
                refinedBytearray[startByte : startByte + sizePerRow] = pack_result
                
            self.byteDataList.append(refinedBytearray)
 
        except Exception as e:          
            logger.error("onReceive Error : {0}".format(e))
    #override
    def OnFinish(self, result):
        if not result:
            self.metadata['Result'] = False
            return
                      
                      
       
        self.metadata['Result'] = True
        
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
    def Create(cls, parentCommandID, accno, passwd, timestamp):
        newCommand = cls(parentCommandID)
        newCommand.input_accno = accno
        newCommand.input_passwd = passwd 
        newCommand.input_expcode = ""   
        
        targetDate =  datetime.fromtimestamp(timestamp)
        
        
        newCommand.input_date = targetDate.strftime('%Y%m%d')
        #newCommand.input_date = '20211232'
        return newCommand
        
    def ToBytes(self):
        tr = self.inst

        
        #print(len(blockDataEncoded), count)
        
        
        
        #print("tobytes", self.metadata)
        return(self.metadata, self.byteDataList)
    