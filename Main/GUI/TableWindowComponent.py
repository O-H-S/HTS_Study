from GUI.View.TableWindow import TableWindow, TableWidgetApplier, GlobalCProcessor, ColumnProcessor
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout
from PyQt5 import uic 
from PyQt5.QtCore import *



def itemEditable(targetTable, item):
    item.setFlags(Qt.ItemIsEditable  | Qt.ItemIsEnabled | Qt.ItemIsSelectable )
    

def itemNotEditable(targetTable, item):
    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable )
    #item.setTextAlignment(Qt.AlignRight)

def itemAlign(targetTable, item, align):
    item.setTextAlignment(align)

def itemColor(targetTable, item, color):
    item.setForeground(QBrush(color))


def CreateCP_shcode():
    def shcodeUpdator(targetTable, args):
        if 'shcodeList' in args:
            keyList = args['shcodeList']
            return keyList
        return []
    return ColumnProcessor('shcode', '종목코드', shcodeUpdator, itemNotEditable)

def CreateCP_getFromAccountStocks(cpName, cpTitle, targetDF, targetColumn):
    def updator(targetTable, args):
        shcode_idx = targetTable.procTable['shcode'][0]
        rowList = args["rows"]
        rowCount = len(rowList)
        results = []                
        for rowID in rowList:
            shcode = targetTable.tableWidget.item(rowID, shcode_idx).text()
            results.append(targetDF.loc[targetDF['expcode'] == shcode].iloc[0][targetColumn])
       
        return results
        
    def itemDoing(targetTable, item):
        itemNotEditable(targetTable, item)
        itemAlign(targetTable, item, Qt.AlignRight)
        #itemColor(tableWidget, item, color):
    return ColumnProcessor(cpName, cpTitle, updator, itemDoing)
def CreateCP_grade(sqlMgr):
    def updator(targetTable, args):
        shcode_idx = targetTable.procTable['shcode'][0]
        rowList = args["rows"]
        rowCount = len(rowList)
               
        shcodesList = []     
        shcodesTable = {}
        results = []                
        for rowID in rowList:
            shcode = targetTable.tableWidget.item(rowID, shcode_idx).text()
            shcodesTable[shcode] = rowID
            shcodesList.append(shcode)
            results.append("-")

        listQuery = sqlMgr.GetListQuery(shcodesList)   
        
        grades = sqlMgr.GetAllRow("StocksGrade", selectQuery = "shcode, grade, reason", whereQuery= " shcode in {0}".format(listQuery), execArgs = shcodesList)
        
        for gr in grades:
            code = gr[0]
            targetGrade = gr[1]
            reason =  gr[2]
            gradeText = "{0} - {1}".format(targetGrade, reason)
            results[shcodesTable[code]] = gradeText
            
    
        
         
        return results
    return ColumnProcessor('grade', '등급', updator, itemNotEditable)

  
def CreateCP_name(dataMgr):
    def codeNameUpdator(targetTable, args):
        shcode_idx = targetTable.procTable['shcode'][0]
        rowList = args["rows"]
        rowCount = len(rowList)
        results = []
        for rowID in rowList:
            shcode = targetTable.tableWidget.item(rowID, shcode_idx).text()
            results.append(dataMgr.GetStockInfo(shcode)['name'])
        return results
        
    return ColumnProcessor('name', '종목명', codeNameUpdator, itemNotEditable)
    
def CreateCP_desc(dataMgr):
    def stockDescUpdator(targetTable, args):          
        shcode_idx = targetTable.procTable['shcode'][0]
        rowList = args["rows"]
        dbName = args["db"]
        
        if dbName is None:
            resultsEmpty = []
            for rowID in rowList:                
                resultsEmpty.append("")
            return resultsEmpty
        
        rows = dataMgr.GroupManager.GetStockGroup(dbName)
        descTable = {}
        for r in rows:
            descTable[r[0]] = r[1]
        
        rowCount = len(rowList)
        results = []
        for rowID in rowList:
            shcode = targetTable.tableWidget.item(rowID, shcode_idx).text()
            if shcode in descTable:
                results.append(descTable[shcode])
            else:
                results.append("")
            
        return results
    return ColumnProcessor('desc', '설명', stockDescUpdator, itemEditable)