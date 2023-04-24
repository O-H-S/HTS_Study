from XingCommand import XingRealCommand
import struct

from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.XARealJIF")
logger = logMgr.logger


class Command_XARealJIF(XingRealCommand):
    ResFileName = ".\\Res\\JIF.res"
    #override
    def Init(self):
        self.inst.SetFieldData("InBlock", "jangubun", '0')

    #override
    def OnFinish(self, result):
        
        if not result:
            return
        
    def OnReceiveRealData(self, code):
        
        gubun = self.inst.GetFieldData("OutBlock", "jangubun")
        jstatus = self.inst.GetFieldData("OutBlock", "jstatus")
        logger.debug('Received : {0} {1}'.format(gubun, jstatus))
        return (gubun, jstatus)
    
    @classmethod
    def Create(cls, parentCommandID):
        newCommand = cls(parentCommandID)
        
        return newCommand   