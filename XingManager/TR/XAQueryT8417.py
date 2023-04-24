
import struct
import time
from datetime import datetime, timedelta
from XingCommand import XingQueryCommand

from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.T8417")
logger = logMgr.logger

__imple__ = 'Command_XAQueryT8417'

class Command_XAQueryT8417(XingQueryCommand):
    ResFileName = ".\\Res\\T8417.res"
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
        ("date", "string", 8*4), 
        ("time", "string", 6*4), 
        ("open", "double", 8), 
        ("high", "double", 8), 
        ("low", "double", 8), 
        ("close", "double", 8), 
        ("jdiff_vol", "long", 4)]
            
        self.metadata['Format'] = DescToFormat(self.metadata['MemberFormat'])
        self.metadata['Count'] = 0
        #print(self.metadata['Format'])
        
        

        self.inst.SetFieldData("t8417InBlock", "shcode", 0, self.input_shcode)
        self.inst.SetFieldData("t8417InBlock", "ncnt", 0, self.input_ncnt )
        self.inst.SetFieldData("t8417InBlock", "qrycnt", 0, self.input_qrycnt)
        self.inst.SetFieldData("t8417InBlock", "nday", 0, self.input_nday )
        self.inst.SetFieldData("t8417InBlock", "sdate", 0, ' ')
        self.inst.SetFieldData("t8417InBlock", "stime", 0, '')
        self.inst.SetFieldData("t8417InBlock", "edate", 0, self.input_edate )
        self.inst.SetFieldData("t8417InBlock", "etime", 0, '')
        
        self.inst.SetFieldData("t8417InBlock", "cts_date", 0, '')
        self.inst.SetFieldData("t8417InBlock", "cts_time", 0, '')
        self.inst.SetFieldData("t8417InBlock", "comp_yn", 0, 'N')
        
        
        
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName, LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
    
    #override
    def IsContinuous(self):
        '''
        result = self.inst.GetFieldData("t8417OutBlock", "cts_date",0)
        result2 = self.inst.GetFieldData("t8417OutBlock", "cts_time",0)
        if len(result) == 8 and len(result2) >= 6  :
            return True
        '''
        return False
        
    #override
    def InitForContinuation(self):
        
        result = self.inst.GetFieldData("t8417OutBlock", "cts_date",0)
        result2 = self.inst.GetFieldData("t8417OutBlock", "cts_time",0)
        self.inst.SetFieldData("t8417InBlock", "cts_date", 0, result)
        self.inst.SetFieldData("t8417InBlock", "cts_time", 0, result2)
        #print("연속 조회 처리 중..", result)
        logger.debug("연속 조회 처리 중.. {0}".format( result))
    
    #override
    def OnReceiveData(self, code):
   
        #print("start")
        # bytearray를 리스트형태로 append함. ToBytes에서 그 리스트를 반환함.
        try:
            curCount = self.inst.GetBlockCount("t8417OutBlock1")
            
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
                        va = tr.GetFieldData("t8417OutBlock1", entryName, index).encode('utf-8').ljust(entrySize, b'\0')
                    elif entryType == "long":
                        va = int(tr.GetFieldData("t8417OutBlock1", entryName, index))
                    elif entryType == "double":
                        va = float(tr.GetFieldData("t8417OutBlock1", entryName, index))
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
    def Create(cls, parentCommandID, shcode, ncnt, qrycnt, nday, edate):
        newCommand = cls(parentCommandID)
        newCommand.input_shcode = shcode
        newCommand.input_ncnt =  ncnt
        newCommand.input_qrycnt =  qrycnt 
        newCommand.input_nday =  nday
        newCommand.input_edate =  edate
        
        return newCommand
        
    def ToBytes(self):
        tr = self.inst

        
        #print(len(blockDataEncoded), count)
        
        
        
        #print("tobytes", self.metadata)
        return(self.metadata, self.byteDataList)
    