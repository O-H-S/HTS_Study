from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QWidget, QMainWindow, QApplication, QCompleter
import os, random
from Training2 import Scenario, Market, Trader
from datetime import datetime, timedelta, date, time

from GUI.View.TraderUI import TraderUI
from GUI.View.ScenarioTab import ScenarioTab
from GUI.View.TestUI import TestUI

path = os.path.dirname(os.path.abspath(__file__))
form_class = uic.loadUiType( os.path.join(path, 'training.ui'))[0]


class TrainingWindow(QMainWindow, form_class):
    def __init__(self, dataMgr):
        super().__init__()

        
        self.setupUi(self)
        
        self.dataMgr = dataMgr
        # ======= 시나리오 관련=========
        self.NewScenarioBtn.clicked.connect(self.onClickNewScenario)
        self.NewScenarioTab.scenario = None
        self.NewScenarioTab.owner = None
        self.Scenarios = []
        self.ScenarioToWidget = {}      
        self.ScenarioTabParent.currentChanged.connect(self.onChangedTab)
        
        # ======= 트레이더 관련 =========
        self.maxCountInRow = 5
        self.activeTraderUIList = []
        self.inActiveTraderUIList = []
        self.traderToUI = {}
        self.AddTraderBtn.mouseReleaseEvent = self.OnClickNewTrader
        self.onClickNewTraderEvent = None
        #===========================
        
 

      
      
    
    def onChangedTab(self, index):
        tabUI = self.ScenarioTabParent.widget(index)
        tabView = tabUI.owner
        if hasattr (tabView, 'scenario') and tabView.scenario:
            self.UpdateSenarioView(tabView)
            self.InitTraderUIs(tabView.scenario.Traders)
        else:
            self.ClearTraderUIs()
     
    
    # =========================================시나리오 관련======================================== 
    def onClickNewScenario(self):
        newScene = Scenario(date(2017, 3, 31), date(2022, 5, 1) , dataMgr = self.dataMgr)
        newScene.Name = self.ScenarioNameInput.text()
        self.AddScenario(newScene)
        
        #def printResult():
        #    newScene.Traders[0].ShowProfits()
        #newScene.OnFinishEvent.append(printResult)
        
    def AddScenario(self, scenario):
        if scenario in self.ScenarioToWidget:
            return self.ScenarioToWidget[scenario]
            
        newUI = self.CreateNewScenarioTab(scenario.Name)
        newUI.scenario = scenario
        self.ScenarioToWidget[scenario] = newUI
        self.UpdateSenarioView(newUI)
        return newUI
    
    def InitSenarios(self, scenarios):
        for scenario in scenarios:
            pass
    
    def SelectScenario(self, scenario):
        if scenario in self.ScenarioToWidget:
            scenarioView = self.ScenarioToWidget[scenario]
            self.ScenarioTabParent.SetCurrentWidget(scenarioView.mainWidget)
            self.UpdateSenarioView(scenarioView.mainWidget)
    
    def GetCurrentScenario(self): # 현재 탭과 매핑된 시나리오 객체를 반환
        tabUI = self.ScenarioTabParent.currentWidget()
        if hasattr (tabUI, 'scenario'):
            return tabUI.scenario
        return None  
    
    def UpdateSenarioView(self, view):
        widget = view.mainWidget
        scenario = view.scenario
        widget.StartDate.setText(scenario.StartDateTime.strftime('%Y.%m.%d'))
        widget.EndDate.setText(scenario.EndDateTime.strftime('%Y.%m.%d'))
        widget.CurDate.setText(scenario.CurDateTime.strftime('%Y.%m.%d'))
        widget.TimeProgress.setValue(int(scenario.GetProgress() * 100))

    
    def CreateNewScenarioTab(self, tabText):
        newUI = ScenarioTab(self.ScenarioTabParent)
        newUI.scenario = None       
        self.ScenarioTabParent.addTab(newUI.mainWidget, tabText)
        
        
        def onClickRun():
            finish = newUI.scenario.Run()
            if not finish:
                newUI.scenario.Traders[0].ShowProfits()
        newUI.mainWidget.RunBtn.clicked.connect(onClickRun)
        
        
        newUI.mainWidget.show()
        return newUI
        #self.ScenarioTabParent.setCurrentIndex(0)
    #=====================================
                
    def OnClickNewTrader(self, eventData):
        if self.onClickNewTraderEvent :
            self.onClickNewTraderEvent()
        
        curScenario = self.GetCurrentScenario()
        if curScenario :     
            newTrader = Trader(1000000 + random.randint(0, 100000))
            curScenario.AddTrader(newTrader)
            self.AddTraderUI(newTrader)
    
    def InitTraderUIs(self, traders): # 시나리오가 바뀔 때, 해당 시나리오의 트레이더 목록으로 UI를 초기화함.
        # 모든 ui 비활성화
        self.ClearTraderUIs()
            
        # 새로운 트레이더 ui 추가
        for trader in traders:
            self.AddTraderUI(trader)
    
    def ClearTraderUIs(self): # 모든 ui 비활성화
        oldList = list(self.activeTraderUIList)
        for activeUI in oldList:
            self.ExcludeTraderUI(activeUI)
    
    def AddTraderUI(self, trader): #현재 시나리오에서 트레이더가 추가되어 UI를 추가할 때 사용.
        ui = self.GetTraderUI()
        ui.trader = trader
        self.BatchTraderUI(ui)
        self.UpdateTraderUI( ui)
        
    def GetTraderUI(self): # 남는 or 새로운 트레이더 UI를 가져온다. 이때 가져오는 객체는 이미 바인드된 트레이너가 있을수도 있고, 없을수도 있다.
        gotUI = None
        if len(self.inActiveTraderUIList) > 0:
            gotUI = self.inActiveTraderUIList[-1]
            return gotUI
        gotUI = self.CreateTraderUI()
        self.inActiveTraderUIList.append(gotUI)
        return gotUI
        
    def UpdateTraderUI(self, ui): #트레이더 ui를 업데이트함
        target = ui.trader
        ui.setContent("{0}".format(target.InitFund), "{0}".format(target.InitFund))
        
    def CalculatePos(self, idx):
        row = int(idx / self.maxCountInRow)
        col = idx % self.maxCountInRow
        return (row, col)
    
    def BatchTraderUI(self, ui): # grid layout에 trader ui를 배치한다. spacer와 add 버튼의 위치에 항상 신경써야함. spacer는 항상 rowcount+1위치에 놓는다. add는 항상 마지막 인덱스 위치에 놓는다.      
        
        if self.TrainerGroupLayout.layout().indexOf(ui) > -1: # 이미 배치된 경우 생략.
            return
       
        
        curCount = len(self.activeTraderUIList) 
        newPos = self.CalculatePos(curCount)
        adderPos = self.CalculatePos(curCount+1)
        
        self.TrainerGroupLayout.layout().addWidget(ui, newPos[0], newPos[1])
        self.TrainerGroupLayout.layout().addWidget(self.AddTraderBtn, adderPos[0], adderPos[1])
        self.activeTraderUIList.append(ui)
        self.inActiveTraderUIList.remove(ui)
        ui.show()
        
    def ExcludeTraderUI(self, ui): # 해당 ui를 사용하지 않는 상태로 바꾼다.
        if self.TrainerGroupLayout.layout().indexOf(ui) < 0: # 이미 배치된 경우 생략.
            return
            
        ui.setParent(None)
        self.activeTraderUIList.remove(ui)
        self.inActiveTraderUIList.append(ui)
        ui.hide()
        
    def CreateTraderUI(self):     
        newUI = TraderUI(self.TrainerGroupLayout)
        return newUI
        
    def timerEvent(self, e):

        self.drawCallback()