
import struct
import time
from XingCommand import XingQueryCommand

from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.T8407")
logger = logMgr.logger

__imple__ = 'Command_XAQueryT8407'
# 계좌 잔고 조회

class Command_XAQueryT8407(XingQueryCommand):
    ResFileName = ".\\Res\\t8407.res"
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
        ("shcode", "string", 6*4), 
        ("price", "long", 4),
        ("diff", "double", 8),
        ("offerho", "long", 4),
        ("bidho", "long", 4),
        ("open", "long", 4),
        ("high", "long", 4),
        ("low", "long", 4),
        ("offerrem", "long", 4),
        ("bidrem", "long", 4)]
            
        self.metadata['Format'] = DescToFormat(self.metadata['MemberFormat'])
        self.metadata['Count'] = 0
        
        
        

        if self.input_shcodeList is None:
            count = len(self.input_packedString) / 6
            self.inst.SetFieldData("t8407InBlock", "nrec", 0, count)
            self.inst.SetFieldData("t8407InBlock", "shcode", 0, self.input_packedString)
        else:
            self.inst.SetFieldData("t8407InBlock", "nrec", 0, str(len(self.input_shcodeList)))
            codeListString = ''.join(self.input_shcodeList)          
            self.inst.SetFieldData("t8407InBlock", "shcode", 0, codeListString)
        
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName, LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
    
   
    #override
    def OnReceiveData(self, code):
   
        #override
        try:
            curCount = self.inst.GetBlockCount("t8407OutBlock1")           
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
                        va = tr.GetFieldData("t8407OutBlock1", entryName, index).encode('utf-8').ljust(entrySize, b'\0')
                    elif entryType == "long":
                        va = int(tr.GetFieldData("t8407OutBlock1", entryName, index))
                    elif entryType == "double":
                        va = float(tr.GetFieldData("t8407OutBlock1", entryName, index))
                    vaList.append(va)
                return vaList
                        
            sizePerRow = struct.calcsize(metadata['Format'])
            #print("sizePerRow", sizePerRow)
            totalBytes = (sizePerRow) * curCount        
            refinedBytearray = bytearray(totalBytes) 
            metadata['Length'] = metadata['Length'] + totalBytes
            metadata['Count'] = self.allCount
            for i in range(curCount):
                startByte = sizePerRow * i
                
                memList = getListOfMember(i)
                pack_result = struct.pack(metadata['Format'], *memList)
                
                refinedBytearray[startByte : startByte + sizePerRow] = pack_result
                
            #print(len(refinedBytearray))
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
    @classmethod
    def Create(cls, parentCommandID, shcodeList, packedString):
        newCommand = cls(parentCommandID)
        newCommand.input_shcodeList = shcodeList
        newCommand.input_packedString = packedString
        return newCommand
        
    def ToBytes(self):
        tr = self.inst

        
        #print(len(blockDataEncoded), count)
        
        
        
        #print("tobytes", self.metadata)
        return(self.metadata, self.byteDataList)
    