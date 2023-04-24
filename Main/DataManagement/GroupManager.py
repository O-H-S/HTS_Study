from Common.Command import Command, SyncCommand
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager

logMgr = LogManager("Main.DM.GM")
logger = logMgr.logger

class GroupManager:
    def __init__(self, dataMgr):
        self.dataMgr = dataMgr
        
    def GetStockGroup(self, groupName):
        tableName = "StockGroup"
        params ="name text, shcode text, desc text, primary key(name, shcode)"
        self.dataMgr.CheckTable(tableName, params) 
        items = self.dataMgr.sqlMgr.GetAllRow(tableName, selectQuery = "shcode, desc", whereQuery= " name =='{0}'".format(groupName))
        return items

    def SaveStockGroup(self, groupName, groupItems):
        tableName = "StockGroup"
        params ="name text, shcode text, desc text, primary key(name, shcode)"
        self.dataMgr.CheckTable(tableName, params)    

        self.dataMgr.sqlMgr.UpsertRowList( "StockGroup(name, shcode, desc)", "name, shcode" , groupItems) 