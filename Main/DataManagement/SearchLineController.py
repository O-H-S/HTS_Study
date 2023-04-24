from datetime import datetime, timedelta
import time, threading
from Common.GlobalLogging import LogManager
from Common.SearchLine import SearchLine

logMgr = LogManager("Main.DM.SLC")
logger = logMgr.logger

# 기본 파라미터
TableParams = "start real PRIMARY KEY, end real"

def LoadFromDB(sqlMgr, tableName, unit = 1, _whereQuery = 1, _selectQuery = '*'):
    global logger
    sections = []
    sections_raw = sqlMgr.GetAllRowSorted(tableName, "start", whereQuery = _whereQuery, selectQuery = _selectQuery)  
    if sections_raw is not None:
        sections = sections_raw
    transformed = SearchLine(sections, unit)
    return transformed

def SaveToDB(sqlMgr, tableName, targetLine, colCount = 2, _paramQuery = None, _whereQuery = 1):
    global logger
    sqlMgr.DeleteRow(tableName, _whereQuery)
    sqlMgr.InsertRowList(tableName, targetLine.sections, colCount, paramQuery = _paramQuery)
    
