
import struct
import time
from XingCommand import XingQueryCommand
__imple__ = 'Command_XAQueryT1102'

#현재가 시세조회
class Command_XAQueryT1102(XingQueryCommand):
    ResFileName = ".\\Res\\t1102.res"
    #override
    def Init(self):
        self.inst.SetFieldData("t1102InBlock", "shcode", 0, self.Input_shcode)

    #override
    def OnFinish(self, result):
        
        if not result:
            return
        
        tr = self.inst
        self.listdate = tr.GetFieldData("t1102OutBlock", "listdate",0)
        self.gsmm = tr.GetFieldData("t1102OutBlock", "gsmm",0)
    
    @classmethod
    def Create(cls, parentCommandID, shcode):
        newCommand = cls(parentCommandID)
        newCommand.Input_shcode = shcode
        return newCommand  