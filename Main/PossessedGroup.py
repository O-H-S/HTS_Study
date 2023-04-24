from GUI.View.TableWindow import TableWindow, TableWidgetApplier, GlobalCProcessor, ColumnProcessor
import GUI.TableWindowComponent as TWC

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout
from PyQt5 import uic 
from PyQt5.QtCore import *
import random


class PossessedGroup:
    def __init__(self, parentWindow, dataMgr):
        self.ParentWindow = parentWindow
        self.dataMgr = dataMgr
        
        self.window = TableWindow()
        self.window.AddItemBtn.setDisabled(True)
        self.window.RemoveItemBtn.setDisabled(True)
        self.window.RowEdit.setDisabled(True)
        
        #row['mamt'],row['pamt'] , row['janqty'] ,row['dtsunik'], row['sunikrt']
        self.procs = [
            TWC.CreateCP_shcode(),
            TWC.CreateCP_grade(dataMgr.sqlMgr),
            TWC.CreateCP_name(dataMgr),
            TWC.CreateCP_getFromAccountStocks('mamt', "매입금", dataMgr.AccStocks, "mamt"),
            TWC.CreateCP_getFromAccountStocks('pamt', "평균단가", dataMgr.AccStocks, "pamt"),
            TWC.CreateCP_getFromAccountStocks('janqty', "수량", dataMgr.AccStocks, "janqty"),
            TWC.CreateCP_getFromAccountStocks('dtsunik', "평가손익", dataMgr.AccStocks, "dtsunik"),
            TWC.CreateCP_getFromAccountStocks('sunikrt', "수익률", dataMgr.AccStocks, "sunikrt")
        ]
        #newApplier = CheckGroup.GetApplier(dataMgr, cgMgr)
        #newProcs = CheckGroup.GetProcessors(dataMgr)
        
        
        
        
    def Init(self, targetStocks):
        self.window.Init("보유종목", {'rowCount':len(targetStocks), 'shcodeList':targetStocks}, self.procs)
        self.window.show()