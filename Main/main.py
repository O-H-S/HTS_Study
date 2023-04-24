from DataManager import DataManager
from AutoUpdater import AutoUpdater

import STWindow 
import threading,os, signal
from datetime import datetime, timedelta

import matplotlib.patches as patches


import pandas as pd

import random, time

import sys

import StatusPrinter as SP

from Common.GlobalLogging import LogManager
from XingMarket import XingMarket

logMgr = LogManager("Main")
logger = logMgr.logger
logger.debug("__________________________________________________________________________________________________________________________________________________________________")
logger.debug("Starting Process")

ID = None
Password  = None
CERT_Password = None
Dart_Key = None
pushedConnectBtn = False
accPassSaved = False
Market = None
autoUpdater = None
Exited = False
def main():
    global autoUpdater
    
    
    dataManager = None   
    WindowInstance = None
    
    
    def onDataMgrInit():
        if pushedConnectBtn or WindowInstance.testWindow.AutoLoginBtn.isChecked():           
            onPushConnect()
    
    def onDataMgrDisable():
        WindowInstance.testWindow.setOnline(False)
        if Market is not None:
            Market.Release()
        #autoUpdater.startUpdate(None)
    
    def onConnectedToServer(result, code, reason):
        global Market, autoUpdater

        if result :

            dataManager.sqlMgr.SetMetaData("RecentID", ID)
            dataManager.sqlMgr.SetMetaData("RecentPass", Password)
            dataManager.sqlMgr.SetMetaData("RecentCertPass", CERT_Password)
            dataManager.sqlMgr.SetMetaData("RecentDartKey", Dart_Key)

            WindowInstance.testWindow.setOnline(True)
            if Market is None:
                Market = XingMarket(dataManager)

            Market.Init()

            dataManager.OrderManager.SetMarket(Market)

            autoUpdater.startUpdate(None)

            
            #dataManager.OrderManager.OrderStocks('293480', True , 19500, 1)
            
            
            #UpdateTime(0.5)

            
            
        else :
            logger.warning("로그인 실패 : {0} | {1}".format(reason, code))
        
    
    dataManager = DataManager()   
    dataManager.InitFinishCallback.append(onDataMgrInit)
    dataManager.ConnectToDB()
    dataManager.serverConnectedCallback = onConnectedToServer
    dataManager.OnDisableEventHandlers.append(onDataMgrDisable)
    
    autoUpdater = AutoUpdater(dataManager)
    
    
    #dataManager.GetStocks()

    

    def onAppExit() :
        global Exited
        dataManager.sqlMgr.SetMetaData("AutoLogin", WindowInstance.testWindow.AutoLoginBtn.isChecked())
        try:
            dataManager.Close()
            Exited = True
        except Exception as e:
            logger.error("{0}".format( e))
        
    def onDraw():
        global accPassSaved
        #threading.Timer(interval, UpdateTime, args=(interval,)).start()       
        WindowInstance.testWindow.ServerTime.setText(dataManager.TimeManager.GetServerDate(True).strftime('%Y-%m-%d-%H:%M:%S'))
        
        if dataManager.AccInfo:
            if not accPassSaved:
                accPassSaved = True
                dataManager.sqlMgr.SetMetaData("RecentAccPass", WindowInstance.testWindow.Input_AccPass.text())
            WindowInstance.testWindow.CurrentMoney.setText("{0:,} / {1:,}".format(int(dataManager.AccInfo[3]), int(dataManager.AccInfo[0])))
            
            profit = int(dataManager.AccInfo[4])
            if int(dataManager.AccInfo[2]) != 0:
                ratio = (profit / int(dataManager.AccInfo[2])) * 100
            else:
                ratio = 0.0
            
            if int(dataManager.AccInfo[0]) != 0:          
                moneyRatio = (int(dataManager.AccInfo[2]) / int(dataManager.AccInfo[0])) * 100
            else:
                moneyRatio = 0.0
            WindowInstance.testWindow.profit.setText("{0:,} ({1:.2f}%)".format(profit, ratio ))

            
            
            WindowInstance.testWindow.moneyRatioBar.setValue(int(moneyRatio))
            WindowInstance.testWindow.Account_No.setText(dataManager.AccNo)

    

    def onPushConnect():
        global pushedConnectBtn
        if not dataManager.Inited:
            pushedConnectBtn = True
            return
            
        if dataManager.serverConnected :

            logger.debug("already connected to server")

            
            #dataManager.SendMessageToManagerAsync("GetAllStock", (True, True))
            #dataManager.SendMessageToManagerAsync("Get", (True, True))
            return
            
        if dataManager.connectingServer :
            logger.debug("already trying connect to server")
            return
    
        global ID, Password, CERT_Password, Dart_Key
        #ID = WindowInstance.window.connectionUI.lineEdit.text()
        #Password = WindowInstance.window.connectionUI.lineEdit_2.text()
        #CERT_Password = WindowInstance.window.connectionUI.lineEdit_3.text()
        
        ID =  WindowInstance.testWindow.Input_ID.text()
        Password =  WindowInstance.testWindow.Input_Pass.text()
        CERT_Password =  WindowInstance.testWindow.Input_Cert.text()
        Dart_Key =  WindowInstance.testWindow.Input_DartKey.text()
        
        dataManager.ConnectToServer(ID, Password, CERT_Password, Dart_Key)
        
    def onClickTraining():
        '''
        result = dataManager.DartReader.xbrl_taxonomy('IS3')
        for idx,row in result[['label_kor', 'account_id', 'account_nm']].iterrows():
            print(row['label_kor'],'\n', row['account_id'],'\n', row['account_nm'])
            print("--")
        '''
        WindowInstance.openTrainingMgr()
        #dataManager.SendMessageToManagerAsync("GetAllStock", (True, True))
        #dataManager.UpdateStockStates()
        #
        #dataManager.UpdateSettleMonth( "12", 3)
    def onClickAccountStocksBtn():

        #Completer 구하기
        #allList = dataManager.GetAllStockCode()
        #allList.extend(dataManager.GetAllStockName())
        
        dataManager.GetBlackList(2021,'4Q', 1, dataManager.GetAccountStocks()) # TestCode, 최근분기 자동화하기
        #dataManager.PriceManager.GetCurrentPrice( dataManager.GetAccountStocks())
        
        WindowInstance.openPossessedGroup(dataManager.GetAccountStocks())
        #WindowInstance.openAccountStocksList(dataManager.GetBlackList(2020,'4Q'))
        #dataManager.UpdateSettleMonth( "12", 3600 * 24 * 1)
        #WindowInstance.openAccountStocksList(dataManager.GetBlackList(2021,'4Q', 3600))
        
    def onEditedAccPass():
    
        dataManager.Input_AccPass = WindowInstance.testWindow.Input_AccPass.text()
        #print("edited")

    def onClickPotentialStocks():

        
        results_G = dataManager.GetStocksByGrade('G')
        wi = WindowInstance.CheckGroupManager.CreateCheckGroup("잠재매수가능", False, results_G)
        wi.window.show()
        
        

    recentIP = dataManager.sqlMgr.GetMetaData("RecentID")
    recentPass = dataManager.sqlMgr.GetMetaData("RecentPass")
    recentCertPass = dataManager.sqlMgr.GetMetaData("RecentCertPass")
    recentDartKey = dataManager.sqlMgr.GetMetaData("RecentDartKey")
    
    recentAccPass = dataManager.sqlMgr.GetMetaData("RecentAccPass")
    
    

    AutoLoginToggle = dataManager.sqlMgr.GetMetaData("AutoLogin")
    
    allList = dataManager.GetAllStockCode()
    allList.extend(dataManager.GetAllStockName())
    
    WindowInstance = STWindow.STWindowManager(onDraw, onAppExit, allList, dataManager)
   
    if recentIP != None :
        #WindowInstance.window.connectionUI.lineEdit.setText(recentIP)
        #WindowInstance.window.connectionUI.lineEdit_2.setText(recentPass)
        #WindowInstance.window.connectionUI.lineEdit_3.setText(recentCertPass)
        
        WindowInstance.testWindow.Input_ID.setText(recentIP)
        WindowInstance.testWindow.Input_Pass.setText(recentPass)
        WindowInstance.testWindow.Input_Cert.setText(recentCertPass)
    if recentDartKey != None:
        WindowInstance.testWindow.Input_DartKey.setText(recentDartKey)
        
    if recentAccPass != None:
         WindowInstance.testWindow.Input_AccPass.setText(recentAccPass)
         
    
        
    if AutoLoginToggle != None:
        if AutoLoginToggle == "True":
            WindowInstance.testWindow.AutoLoginBtn.toggle()
        
    
    
    #WindowInstance.window.connectionUI.pushButton.clicked.connect(onPushConnect)
    WindowInstance.testWindow.ConnectBtn.clicked.connect(onPushConnect)
    
    WindowInstance.testWindow.Training_Btn.clicked.connect(onClickTraining)
    WindowInstance.testWindow.AccountStocksBtn.clicked.connect(onClickAccountStocksBtn)
    WindowInstance.testWindow.Input_AccPass.editingFinished.connect(onEditedAccPass)
    WindowInstance.testWindow.PotentialStock_Btn.clicked.connect(onClickPotentialStocks)
    
    def ItemChanged(a,b):
        row = WindowInstance.AccountStocksList.tableWidget.currentRow() 
        if row > -1:
            selectedCode = WindowInstance.AccountStocksList.rows[row][0]
            WindowInstance.testWindow.Input_shcode.setText(selectedCode)

            #onPushShowPrice()
    
    #WindowInstance.AccountStocksList.tableWidget.cellClicked.connect(ItemChanged)
    
    
    def StatusChecking(interval, lastCall = False):   
        global Exited
        if lastCall:
            logger.info("StatusChecking Last Call")
        SP.PrintStatus(dataManager)       
      
        if not lastCall:
            if Exited:
                logger.info("(StatusChecking) 종료가 감지 되었습니다.")
                time.sleep(15)
                newTimer = threading.Timer(interval, StatusChecking, args=(interval, True))    
                newTimer.name = "StatusChecking"
                newTimer.start()
            else:
                newTimer = threading.Timer(interval, StatusChecking, args=(interval, ))    
                newTimer.name = "StatusChecking"
                newTimer.start()        
    
    StatusChecking(30)
    WindowInstance.run()


     
if __name__ == '__main__': 
    main()