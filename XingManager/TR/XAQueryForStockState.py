
import struct
import time
from XingCommand import XingQueryCommand


from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.T1404")
logger = logMgr.logger

__imple__ = 'Command_XAQueryT1404'

class Command_XAQueryT1404(XingQueryCommand):
    ResFileName = ".\\Res\\t1404.res"
    InBlockName = "t1404InBlock"
    OutBlockName = "t1404OutBlock"
    OutBlockName2 = "t1404OutBlock1"
    HasField_jongchk = True
    #override
    def Init(self):
        self.allCount = 0
        self.byteDataList = []
        self.metadata = {}
        self.metadata['Length'] = 0

        self.inst.SetFieldData(self.__class__.InBlockName, "gubun", 0, '0')
        if self.__class__.HasField_jongchk:
            self.inst.SetFieldData(self.__class__.InBlockName, "jongchk", 0, self.input_jongchk)
        self.inst.SetFieldData(self.__class__.InBlockName, "cts_shcode", 0, "")
        
        
        
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName, LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
    
    #override
    def IsContinuous(self):
        result = self.inst.GetFieldData(self.__class__.OutBlockName, "cts_shcode", 0)
        if result != "":
            return True
        return False
        
    #override
    def InitForContinuation(self):
        
        result = self.inst.GetFieldData(self.__class__.OutBlockName, "cts_shcode",0)
        self.inst.SetFieldData(self.__class__.InBlockName, "cts_shcode", 0, result)

        logger.debug("연속 조회 처리 중.. {0}".format( result))
        
    
    #override
    def OnReceiveData(self, code):
        #print("start")
        # bytearray를 리스트형태로 append함. ToBytes에서 그 리스트를 반환함.
        curCount = self.inst.GetBlockCount(self.__class__.OutBlockName2)
        self.allCount = self.allCount + curCount
        tr = self.inst 
        
        metadata = self.metadata
        metadata['Format'] = '40s24s'      
        metadata['MemberFormat'] = [
        ("hname", "string", 20*4), 
        ("shcode", "string", 6*4)]

        
        sizePerRow = struct.calcsize(metadata['Format'])
        totalBytes = (sizePerRow) * curCount        
        refinedBytearray = bytearray(totalBytes) 
        metadata['Length'] = metadata['Length'] + totalBytes
        metadata['Count'] = self.allCount
        for i in range(curCount):
            startByte = sizePerRow * i
            hname = tr.GetFieldData(self.__class__.OutBlockName2, "hname", i).encode('utf-8').ljust(metadata['MemberFormat'][0][2], b'\0')
            shcode = tr.GetFieldData(self.__class__.OutBlockName2, "shcode", i).encode('utf-8').ljust(metadata['MemberFormat'][1][2], b'\0')          
            pack_result = struct.pack(metadata['Format'], hname, shcode)
            refinedBytearray[startByte : startByte + sizePerRow] = pack_result
            
        self.byteDataList.append(refinedBytearray)
    #override
    def OnFinish(self, result):
        if not result:

            return
                      
                      
            
        tr = self.inst 

        '''
        print(tr.GetFieldData("t0424OutBlock1", "hname", 0))
        print(tr.GetFieldData("t0424OutBlock1", "jangb", 0))
        print(tr.GetFieldData("t0424OutBlock1", "janqty", 0))
        '''
        #
        
        
    @classmethod
    def Create(cls, parentCommandID, jongchk):
        newCommand = cls(parentCommandID)
        newCommand.input_jongchk = jongchk
     
        return newCommand
        
    def ToBytes(self):
        tr = self.inst
        return(self.metadata, self.byteDataList)
        
class Command_XAQueryT1405(Command_XAQueryT1404):
    ResFileName = ".\\Res\\t1405.res"
    InBlockName = "t1405InBlock"
    OutBlockName = "t1405OutBlock"
    OutBlockName2 = "t1405OutBlock1"
    
    
class Command_XAQueryT1410(Command_XAQueryT1404):
    ResFileName = ".\\Res\\t1410.res"
    InBlockName = "t1410InBlock"
    OutBlockName = "t1410OutBlock"
    OutBlockName2 = "t1410OutBlock1"
    HasField_jongchk = False
    
    @classmethod
    def Create(cls, parentCommandID):
        newCommand = cls(parentCommandID)
     
        return newCommand