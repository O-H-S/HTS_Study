
import struct
import time
from datetime import datetime, timedelta
from XingCommand import XingQueryCommand

from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.CSPAT00600")
logger = logMgr.logger

__imple__ = 'Command_XAQueryCSPAT00600'
# 계좌 잔고 조회

class Command_XAQueryCSPAT00600(XingQueryCommand):
    ResFileName = ".\\Res\\CSPAT00600.res"
    #override
    def Init(self):
        
              
        self.inst.SetFieldData("CSPAT00600InBlock1", "AcntNo", 0, self.input_accno)
        self.inst.SetFieldData("CSPAT00600InBlock1", "InptPwd", 0, self.input_passwd)
        self.inst.SetFieldData("CSPAT00600InBlock1", "IsuNo", 0, self.input_shcode)
        self.inst.SetFieldData("CSPAT00600InBlock1", "OrdQty", 0, self.input_quantity)
        self.inst.SetFieldData("CSPAT00600InBlock1", "OrdPrc", 0, self.input_price)
        self.inst.SetFieldData("CSPAT00600InBlock1", "BnsTpCode", 0, self.input_buyORsell)
        self.inst.SetFieldData("CSPAT00600InBlock1", "OrdprcPtnCode", 0, "00")
        self.inst.SetFieldData("CSPAT00600InBlock1", "MgntrnCode", 0, "000")
        self.inst.SetFieldData("CSPAT00600InBlock1", "LoanDt", 0, "0")
        self.inst.SetFieldData("CSPAT00600InBlock1", "OrdCndiTpCode", 0, "0")
        
        
        
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName, LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
    
   
 
    #override
    def OnFinish(self, result):
        if not result:
            
            return
                      
                      
       
       
        
        tr = self.inst 
        
        self.orderNo = tr.GetFieldData("CSPAT00600OutBlock2", "OrdNo",0)
        self.orderTime = tr.GetFieldData("CSPAT00600OutBlock2", "OrdTime",0)
        self.r = tr.GetFieldData("CSPAT00600OutBlock2", "OrdMktCode",0)
        self.r2 = tr.GetFieldData("CSPAT00600OutBlock2", "OrdPtnCode",0)
        self.r3 = tr.GetFieldData("CSPAT00600OutBlock2", "ShtnIsuNo",0)
        self.r4 = tr.GetFieldData("CSPAT00600OutBlock2", "OrdAmt",0)
        self.r5 = tr.GetFieldData("CSPAT00600OutBlock2", "SpotOrdQty",0)
              
        
    @classmethod
    def Create(cls, parentCommandID, accno, passwd, shcode, quantity, price, buyORsell):
        newCommand = cls(parentCommandID)
        newCommand.input_accno = accno
        newCommand.input_passwd = passwd 
        newCommand.input_shcode = shcode  
        newCommand.input_quantity = quantity
        newCommand.input_price = price
        if buyORsell :
            newCommand.input_buyORsell = '2'
        else:
            newCommand.input_buyORsell = '1'

        return newCommand
 
    