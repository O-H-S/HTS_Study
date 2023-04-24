# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ItemListView.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QWidget, QMainWindow, QApplication, QCompleter
import os

path = os.path.dirname(os.path.abspath(__file__))
form_class = uic.loadUiType( os.path.join(path, 'ItemListView.ui'))[0]

class TableWidgetApplier():
    def __init__(self, doing):
        self.doing = doing
    
        self.Clear()
    
        self.lastDone_Name = None
    def Record_Name(self, changedName):
        self.Change_Name = changedName
    
    def Record_Exist(self, item, lastPos ,InOut): #In : True, Out: False
        
        # lastPos, item.text() 같이 저장하는 이유는, 아이템이 삭제됐을 때, 마지막 데이터를 보존하기 하기위함.
        self.Change_Exist.append((item, lastPos, item.text(), InOut))

    
    def Record_Item(self, item):

            
        self.Change_Item.append(item)
     
    def Do(self, target):
        self.doing(target,(self.lastDone_Name,self.Change_Name,), self.Change_Exist, self.Change_Item)
        if self.Change_Name is not None:
            self.lastDone_Name = self.Change_Name
        
    def Clear(self):    
        self.Change_Name = None
        self.Change_Exist = []

        self.Change_Item = [] #key : col, value : [keys..]

class GlobalCProcessor():
    def __init__(self, doing, cProcessors):
        self.doing = doing        
        self.cProcessorTable = {}
        self.childProcessors = cProcessors
        for proc in cProcessors:
            self.cProcessorTable[proc.name] = proc
        
    def Do(self, targetTable, processors, args):
        resultTable = self.doing(targetTable, processors, args)
        for k, v in resultTable.items():
            if k in self.cProcessorTable:
                self.cProcessorTable[k].ProcessedData = v

class ColumnProcessor():
    def __init__(self, name, label, doing = None, doingForItem = None, userDriven = False):
        self.name = name
        self.doing = doing
        self.doingForItem = doingForItem
        self.label = label
        self.ProcessedData = None

        self.userDriven = userDriven
        
        
        
        
        
        
    def Do(self, targetTable, args):
        if self.ProcessedData is not None:
            return self.ProcessedData
        
        if self.doing is None:
            return None
            
        return self.doing(targetTable, args)
    
  
    
    def Clear(self):
        self.ProcessedData = None

class TableWindow(QMainWindow, form_class):
    def __init__(self):
        
        QMainWindow.__init__(self)
        def notDoing(a,b,c):
            pass               
        self.applier = TableWidgetApplier(notDoing)      
        self.processors = []
        self.procTable = {}
        self.setupUi(self)    
       
        def addItemEvent():                 
            codeText = self.RowEdit.text()          
            if codeText == "":
                return
            self.ItemChangingBySystem = True             
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)
            colID = 0
            for proc in self.processors:
                newItem = QTableWidgetItem("")
                self.tableWidget.setItem(rowPosition, colID, newItem)
                self.applier.Record_Exist(newItem, (rowPosition, colID), True) 
                colID = colID +1
                  
            self.tableWidget.item(rowPosition, 0).setText(codeText)
            self.ItemChangingBySystem = False
            self.Update({'rows':[rowPosition]})          
            self.RowEdit.setText("")
       
        self.RowEdit.editingFinished.connect(addItemEvent)
        
        
        def removeItemEvent():
            curRow = self.tableWidget.currentRow()
            if curRow > -1:
                for colID in range(len(self.processors)):
                    self.applier.Record_Exist(self.tableWidget.item(curRow, colID), (curRow, colID), False)       
                self.tableWidget.removeRow(curRow)     
        self.RemoveItemBtn.clicked.connect(removeItemEvent)

        self.ItemChangingBySystem = False
        def recordingItem(item):
            if not self.ItemChangingBySystem:
                self.applier.Record_Item(item)

        self.tableWidget.itemChanged.connect(recordingItem)
        self.ConstructStructure(0, [''])
        self.readOnly = False
    
    def Init(self, name, args, processors, globalProc = None, applier = None, adder=None, applied = True):
        self.processors = processors
        self.procTable = {}
        self.applier = applier
        self.setName(name, True, not applied)
        #print(applied)
        if applier and applied:
            applier.lastDone_Name = name
        rowCount = args['rowCount']
        labelList = []
        colNumb = 0
        for proc in processors:
            labelList.append(proc.label)
            self.procTable[proc.name] = (colNumb, proc)
            colNumb = colNumb+1
   
        self.ConstructStructure(rowCount, labelList)
               
        self.globalProc = globalProc
        if globalProc :
            globalProc.Do(self, processors, args)
            
        args['rows'] = list(range(0, rowCount))
        self.ItemChangingBySystem = True
        colCount = len(self.processors)   
        curProc = 0
        for proc in self.processors:
            resultVerticalItems = proc.Do(self, args)

            for rowID in range(len(resultVerticalItems)):
                item = self.tableWidget.item(rowID, curProc)
                if applier and not applied:
                    applier.Record_Exist(item, (rowID, curProc), True)
                item.setText(str(resultVerticalItems[rowID]))
                if proc.doingForItem is not None:
                    proc.doingForItem(self, item)
                
            proc.Clear()
            curProc = curProc + 1

        

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        self.ItemChangingBySystem = False
    
    def Apply(self):

        if self.applier is None:
            return False

        if not self.readOnly:
            if self.applier.lastDone_Name != self.getName():
                self.setName( self.getName())
        else:
            return False
        
 
        self.applier.Do(self)  
        self.applier.Clear()
        return True
    
    def setName(self, name, editable = True, record = True):

        self.GroupName_Input.setText(name)
        self.setWindowTitle("그룹 - {0}".format(name))
        self.GroupName_Input.setReadOnly(not editable)
        
        if self.applier and record :
            self.applier.Record_Name(name)
    
    def getName(self):
        return self.GroupName_Input.text()
    

    
    def setCodeCompleter(self, codeList):

        self.completer = QCompleter(codeList)
        self.RowEdit.setCompleter(self.completer)
   
   
        
    def Update(self, args):

        if self.globalProc:
            self.globalProc.Do(self, self.processors, args)
            
        self.ItemChangingBySystem = True
        colCount = len(self.processors)   
        curProc = 0
        
        rows = args['rows']

        for proc in self.processors:
            resultVerticalItems = proc.Do(self, args)
            curRowIdx = 0
            for _ in range(len(resultVerticalItems)):
                item = self.tableWidget.item(rows[curRowIdx], curProc)
                item.setText(str(resultVerticalItems[curRowIdx]))

                if proc.doingForItem is not None:                  
                    proc.doingForItem(self,item)
                curRowIdx = curRowIdx+1
            proc.Clear()
            curProc = curProc + 1

        
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        self.ItemChangingBySystem = False
    
    def ConstructStructure(self, rowCount, colLabels):
        self.tableWidget.setColumnCount(len(colLabels))
        self.tableWidget.setHorizontalHeaderLabels(colLabels)
        self.tableWidget.setRowCount(rowCount)
        self.ItemChangingBySystem = True
        
        colCount = len(colLabels)
              
        for row in range(0, rowCount):      
            for col in range(colCount):
                item = QTableWidgetItem("")
                self.tableWidget.setItem(row, col, item)
                
          
        self.ItemChangingBySystem = False
    
    




