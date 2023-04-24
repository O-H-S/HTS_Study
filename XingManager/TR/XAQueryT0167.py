
import struct
import time
from XingCommand import XingQueryCommand
__imple__ = 'Command_XAQueryT0167'
# 서버 시간 조회
class Command_XAQueryT0167(XingQueryCommand):
    ResFileName = ".\\Res\\t0167.res"
    #override
    def Init(self):
        self.inst.SetFieldData("t0167InBlock", "id", 0, None)
        self.startHearTime = time.time()
    #override
    def OnFinish(self, result):
        
        if not result:
            return
        
        tr = self.inst
        self.endHearTime = time.time()
        self.date = tr.GetFieldData("t0167OutBlock", "dt",0)
        self.time = tr.GetFieldData("t0167OutBlock", "time",0)
    
    @classmethod
    def Create(cls, parentCommandID):
        newCommand = cls(parentCommandID)
        
        return newCommand  