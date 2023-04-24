from XingCommand import XingRealCommand
import struct

class Command_XARealNWS(XingRealCommand):
    ResFileName = ".\\Res\\NWS.res"
    #override
    def Init(self):
        self.inst.SetFieldData("InBlock", "nwcode", 'NWS001')

    #override
    def OnFinish(self, result):
        
        if not result:
            return
        
    def OnReceiveRealData(self, code):
        
        title = self.inst.GetFieldData("OutBlock", "title")

        print("a]",title)
        return struct.pack('100s', title.encode('utf-8').ljust(100, b'\0'))
    
    @classmethod
    def Create(cls, parentCommandID):
        newCommand = cls(parentCommandID)
        
        return newCommand   