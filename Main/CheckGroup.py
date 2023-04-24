from GUI.View.TableWindow import TableWindow, TableWidgetApplier, GlobalCProcessor, ColumnProcessor
import GUI.TableWindowComponent as TWC

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout
from PyQt5 import uic 
from PyQt5.QtCore import *
import random

class CheckGroup:
    def __init__(self, name, dataMgr, cgMgr, codeCompleter, fromDB = True, keyList = None):
        self.window = TableWindow()

        
        
            

        self.window.AddItemBtn.setEnabled(True)
        self.window.RemoveItemBtn.setEnabled(True)
        self.window.RowEdit.setEnabled(True)
        
        def onClose(event):
            self.window.Apply()
            cgMgr.stockGroupSet.discard(self)
            self.window.__class__.closeEvent(self.window, event)
        
        def onClickNewGroup():
            newWidgetChild = cgMgr.CreateCheckGroup("새 그룹"+ str(random.random()), False)
            newWidgetChild.window.show()
            
        def onClickSaveGroup():            
            self.window.Apply()
            cgMgr.updateStockGroupBox()
        
        self.window.closeEvent = onClose
        self.window.CreateGroupBtn.clicked.connect(onClickNewGroup) 
        self.window.SaveGroupBtn.clicked.connect(onClickSaveGroup) 
        self.window.setCodeCompleter(codeCompleter)
        
        
        
        if keyList is None:
            rows = dataMgr.GroupManager.GetStockGroup(name)
            keyList = []
            for r in rows:
                keyList.append(r[0])

        newApplier = CheckGroup.GetApplier(dataMgr, cgMgr)
        newProcs = CheckGroup.GetProcessors(dataMgr)
        self.window.Init(name, {'rowCount':len(keyList), 'shcodeList':keyList, 'db':name}, newProcs, CheckGroup.GetGlobalProc(dataMgr, newProcs), newApplier, None, applied = fromDB)

    
    cProcList = None
    gProc = None
    applier = None
    
    @classmethod
    def GetApplier(cls, dataMgr, CGManager):

            
        def applyChanges(target, names, existences, items):
            
            lastNameInDB = names[0] # 마지막으로 db에 저장된 이름
            NewName = names[1]
            
            NameInDB = None
            if lastNameInDB is None:
                if NewName is None:
                    logger.warning("이름 적용 예외")
                else: #처음으로 저장하는 경우
                    #print("최초 저장", NewName)    
                    NameInDB = NewName     
            else:        
                if NewName is None: # 이름이 변경되지 않은 케이스
                    NameInDB = lastNameInDB
                else: # 이름이 변경된 케이스
                
                    # 이전 이름으로 DB안 의 모든 관심종목들을 가져옴.              
                    rows = dataMgr.GroupManager.GetStockGroup(lastNameInDB)
                    # 이전 DB의 내용들을 모두 삭제함.
                    dataMgr.sqlMgr.DeleteRow( 'StockGroup', "name == '{0}'".format(lastNameInDB))
                    
                    # 새로운 이름의 DB로 다시 저장함.
                    newRows = []
                    for row in rows:
                        newRows.append([NewName, row[0], row[1]])
                    dataMgr.GroupManager.SaveStockGroup(NewName, newRows) 
                
                    NameInDB = NewName    
                    
                
            
            shcode_idx = target.procTable['shcode'][0]
            desc_idx = target.procTable['desc'][0]
            
            changes = []          
            for item in items:
                colID = target.tableWidget.column(item)
                rowID = target.tableWidget.row(item)
                proc = target.processors[colID]
                
                shcode = target.tableWidget.item(rowID, shcode_idx).text()

                if proc.name == 'desc':                 
                    changes.append([NameInDB, shcode, item.text()])
                '''
                elif proc.name == 'shcode':  
                    # shcode가 바뀌면 
                    changes.append([lastDoneName, shcode, ""])
                '''
                    
            if len(changes) > 0:
                dataMgr.GroupManager.SaveStockGroup(NameInDB, changes)
            
            removed_code = []
            for existence in existences:
                eItem = existence[0]
                ePos = existence[1]
                eText = existence[2]
                eExist = existence[-1]
                colID = ePos[1]
                if not eExist and colID == shcode_idx:
                    removed_code.append(eText)
                    dataMgr.sqlMgr.DeleteRow( 'StockGroup', "name == '{0}' and shcode =='{1}'".format(NameInDB, eText))
                elif eExist and colID == shcode_idx:
                    ePos = (target.tableWidget.row(eItem), target.tableWidget.column(eItem))
                    descItem = target.tableWidget.item(ePos[0], desc_idx)
                    dataMgr.GroupManager.SaveStockGroup(NameInDB, [[NameInDB, eItem.text(), descItem.text()]])

            # 구조 개편 필요함. (Group 테이블, GroupEntry 테이블 별도로 존재해야함)     
            CGManager.updateStockGroupBox()
                    
                
            
        CheckGroup.applier = TableWidgetApplier(applyChanges)
        return CheckGroup.applier
            
    @classmethod
    def GetGlobalProc(cls, dataMgr, procs):

    
        def doing(targetTable, procs, args):
            names = []
            args['db'] = targetTable.applier.lastDone_Name
            if 'shcodeList' in args:
                keyList = args['shcodeList']
                for shcode in keyList:
                    names.append(dataMgr.GetStockInfo(shcode)['name'])
                
            #return { 'shcode' : keyList, 'name' : names, 'desc': args[0]}
            return {}
            
        globalP = GlobalCProcessor(doing, procs)
        CheckGroup.gProc = globalP
        return CheckGroup.gProc
    
    
    @classmethod
    def GetProcessors(cls, dataMgr):          
        CheckGroup.cProcList = []
            
        processor_code = TWC.CreateCP_shcode()
        CheckGroup.cProcList.append(processor_code)
        
        processor_name = TWC.CreateCP_name(dataMgr)
        CheckGroup.cProcList.append(processor_name)
        
        processor_desc = TWC.CreateCP_desc(dataMgr)
        CheckGroup.cProcList.append(processor_desc)
        return CheckGroup.cProcList
        
class CheckGroupManager:
    def __init__(self, targetComboBox, dataMgr, codeCompleter):
        self.targetComboBox = targetComboBox
        self.dataMgr = dataMgr
        self.stockGroupSet = set()
        self.stockGroupTable = {}
        self.StockGroupBoxUpdating = False
        self.codeCompleter = codeCompleter
        
        def openGroup(event):
            
            if targetComboBox.count() == 0:
                newGroup = self.CreateCheckGroup("새 그룹", False)
                newGroup.window.show()
            else:
                curID = targetComboBox.currentIndex()              
                if curID > -1:          
                    originName = targetComboBox.itemData(curID)    
                    if not self.isGroupShown(originName):
                        newWidget = self.CreateCheckGroup(originName, True)
                        newWidget.window.show()
                        targetComboBox.setCurrentIndex(-1)
                    
            targetComboBox.__class__.mousePressEvent(targetComboBox, event)
            
        def onChanged(changedText):
            curID = targetComboBox.currentIndex()
            #print(curID)
            if not self.StockGroupBoxUpdating and curID > -1 :
                originName = targetComboBox.itemData(curID)
                if not self.isGroupShown(originName):
                    newWidget = self.CreateCheckGroup( originName, True )
                    newWidget.window.show()
                    targetComboBox.setCurrentIndex(-1)    
                #print("signal :", changedText,  self.testWindow.StockGroupComboBox.itemData(curID))
        

        targetComboBox.mousePressEvent = openGroup
        targetComboBox.currentTextChanged.connect(onChanged)
        self.updateStockGroupBox()
        
    def CreateCheckGroup(self, name, fromDB = True, keyList = None):
        
        newGroup = CheckGroup(name, self.dataMgr, self, self.codeCompleter, fromDB, keyList)
     
        self.stockGroupSet.add(newGroup)
        return newGroup
    

    
    def updateStockGroupBox(self):
        groupData = self.dataMgr.sqlMgr.GetCountByGroup("StockGroup", 'name')

        self.targetComboBox.clear()
        self.StockGroupBoxUpdating = True
        for group in groupData:
            self.targetComboBox.addItem("{0}({1})".format(group[0],group[1]), group[0])
        self.StockGroupBoxUpdating = False 
        self.targetComboBox.setCurrentIndex(-1)
        
    def isGroupShown(self, groupName):
        alreadyShown = False
        for tableWidget in self.stockGroupSet:
            if tableWidget.window.isVisible() and tableWidget.window.getName() == groupName:
                alreadyShown = True
        return alreadyShown
        