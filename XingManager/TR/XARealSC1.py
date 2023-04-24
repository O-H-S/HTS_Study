from XingCommand import XingRealCommand

class Command_XARealSC1(XingRealCommand):
    ResFileName = ".\\Res\\SC1.res"
    #override
    def Init(self):
        #self.inst.SetFieldData("InBlock", "nwcode", 'NWS001')
        pass
    
    def OnReceiveRealData(self, code):
        pass
    
    
    #override
    def OnFinish(self, result):
        
        if not result:
            return
        
 
    
    @classmethod
    def Create(cls, parentCommandID):
        newCommand = cls(parentCommandID)
        
        return newCommand   
        

