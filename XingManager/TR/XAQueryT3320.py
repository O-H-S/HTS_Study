
import struct
import time
from XingCommand import XingQueryCommand
__imple__ = 'Command_XAQueryT3320'


class Command_XAQueryT3320(XingQueryCommand):
    ResFileName = ".\\Res\\t3320.res"
    #override
    def Init(self):
        self.inst.SetFieldData("t3320InBlock", "gicode", 0, self.Input_gicode)

    #override
    def OnFinish(self, result):
        
        if not result:
            return
        
        tr = self.inst
        self.listdate = tr.GetFieldData("t3320OutBlock", "listdate",0)
        self.gsym = tr.GetFieldData("t3320OutBlock", "gsym",0)
        self.t_gsym = tr.GetFieldData("t3320OutBlock1", "t_gsym",0)
    @classmethod
    def Create(cls, parentCommandID, shcode):
        newCommand = cls(parentCommandID)
        newCommand.Input_gicode = shcode
        return newCommand        

