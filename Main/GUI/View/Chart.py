from PyQt5.QtCore import QDate, Qt
from datetime import datetime, timedelta
from Common.GlobalLogging import LogManager
from Common.BlitManager import BlitManager
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import re, time
from pandas import Series, DataFrame
import math,sys
from six.moves import xrange, zip
from matplotlib import colors as mcolors
from matplotlib.collections import LineCollection, PolyCollection
import pandas as pd
import matplotlib.ticker as ticker
import matplotlib.patches as patches
from .ConditionOrderMark import COrderMark
logMgr = LogManager("Main.GUI.ChartView")
logger = logMgr.logger



class Chart:
    def __init__(self, baseWidget = None):
        if baseWidget is None: #기반이 되는 위젯이 존재하지 않을 때, 직접 생성해야함 (차후 구현)
            pass
            
        self.BaseWidget = baseWidget    
        self.OnMovedEventHandlers = []
        self.PickerTable = {} # key : artist, value : mappedObject
        self.PickerTable_Inv = {}
        
        self.OnCreateCOMarkHandlers = []
        self.OnSaveCOMarkHandlers = []
        self.OnStartCOMarkHandlers = []
        
        self.Figure = plt.figure(figsize=(12, 6))    


        pressStates = {}
        def getPress(key):
            if key in pressStates:
                return pressStates[key]
            return False
        
        def on_release(event):
            if event.key is not None:
                pressStates[event.key] = False
        
        def on_press(event):
            
            if event.key is not None:
                pressStates[event.key] = True

            

            if self.CurPicked is not None:
                if event.key == ' ':
                    
                    self.CurPicked.SetBuyOrSell(not self.CurPicked.buyORsell)
                    self.CurPicked.SetDirty(True, update = False)
                    self.blitMgr.update()
                    return 
                elif event.key == 's':

                    self.saveConditionOrderMark(self.CurPicked)
                    self.blitMgr.update()
                    return 
                elif event.key == 'enter':
                    
                    self.setCOrderStarted(self.CurPicked, not self.CurPicked.started)
                    #self.CurPicked.SetStarted(not self.CurPicked.started)
                    self.saveConditionOrderMark(self.CurPicked)
                    self.blitMgr.update()
                    return
            moveCeo = 0
            if event.key == 'left':
                moveCeo = -1
            elif event.key == 'right':
                moveCeo = 1
            elif event.key == ' ':
                self.RelimY()
                self.Canvas.draw()

            if moveCeo != 0:
                xlims = self.Axes.get_xlim()
                xlimSize = xlims[1] - xlims[0]
                moveSize = moveCeo * int(xlimSize / 5)
                movedLim = [xlims[0] + moveSize , xlims[1] + moveSize]
                self.Axes.set_xlim(movedLim)
                self.Canvas.draw()
                
                for handler in self.OnMovedEventHandlers :
                    handler(xlims, movedLim, moveSize)
            else:
                moveCeo = 0
                if event.key == 'up':
                    moveCeo = 1.3
                elif event.key == 'down':
                    moveCeo = 0.7
                 
                if moveCeo != 0:
                    ylims = self.Axes.get_ylim()
                    ylimSize = ylims[1] - ylims[0]
                    moveSize = moveCeo * int(ylimSize / 5)
                    movedLim = [ylims[0] * moveCeo , ylims[1] * moveCeo]
                    self.Axes.set_ylim(movedLim)
                    self.Canvas.draw()
            

        def on_press_mouse(event):
            if getPress('a') and event.button == 3 and self.CurPicked is None:
                
                self.createConditionOrderMark(event.xdata, event.ydata, self)
                self.blitMgr.update()

                #print(con, att)
        def on_release_mouse(event):

            if self.CurPicked is not None:
                self.CurPicked = None
        
        def wheel(event):
            mulCoe = 0
            if event.button == 'up':
                mulCoe = 0.8
            elif event.button == 'down':
                mulCoe = 1.2
            
            if mulCoe != 0:
                xlims = self.Axes.get_xlim()
                ylims = self.Axes.get_ylim()
                
                
                xlimsCenter = (xlims[1] + xlims[0]) / 2
                ylimsCenter = (ylims[1] + ylims[0]) / 2
                #print(xlims, xlimsCenter)
                #print([xlimsCenter+ (xlims[0]-xlimsCenter)*mulCoe, xlimsCenter+ (xlims[1]-xlimsCenter)*mulCoe])
                self.Axes.set_xlim([xlimsCenter+ (xlims[0]-xlimsCenter)*mulCoe, xlimsCenter+ (xlims[1]-xlimsCenter)*mulCoe])
                #self.Axes.set_ylim([ylimsCenter+ (ylims[0]-ylimsCenter)*mulCoe, ylimsCenter+ (ylims[1]-ylimsCenter)*mulCoe])
                self.Canvas.draw()
                
        def hover(event):
            if self.Annot is None:
                return
            if self.CurPicked and not self.PickedSettingMode:
                #print("aa")
                #self.CurPicked.set_data((event.xdata, event.ydata))
                
                self.setCOrderStarted(self.CurPicked, False)
                #self.CurPicked.SetStarted(False)
                self.CurPicked.MoveTo(event.xdata, event.ydata)
                self.CurPicked.SetDirty(True, update = False)
                
            if event.inaxes == self.Axes:
                #print(event.xdata, event.ydata)
                #cont, ind = sc.contains(event)
                #if cont:
                    # change annotation position
                x_int = int(round(event.xdata))
                #print(x_int)                
                #x_int = max(0, min(x_int, len(priceData)-1))
                #print(x_int)
                self.Annot.xy = (event.xdata, event.ydata)
                
                # write the name of every point contained in the event
                
                if x_int in self.XToPrices:
                    ohlc = self.XToPrices[x_int]
                    xd = self.XToDate[x_int]
                    annotString = "{0}\nHigh {1}\nOpen {2}\nClose{3}\nLow {4}".format(xd, ohlc[1], ohlc[0], ohlc[3], ohlc[2])
                else:  
                    annotString = "{0}".format(x_int)
                self.Annot.set_text(annotString)
                
                if self.Annot.get_visible() is False:
                    self.Annot.set_visible(True)   
                
                self.blitMgr.update()
        
        #self.Canvas.mpl_connect('key_press_event', on_press)
        
        
        self.Axes = self.Figure.add_subplot(111)
        
        self.Canvas = FigureCanvas(self.Figure)
        baseWidget.ChartPlace.layout().addWidget(self.Canvas, 100)
        
        self.Canvas.setFocusPolicy( Qt.ClickFocus )
        
        self.CurPicked = None
        self.PickedSettingMode = False
        def picked(event):
            #print(event.mouseevent)
            if event.mouseevent.button == 1:
                self.CurPicked = self.PickerTable[event.artist]
                self.PickedSettingMode = False
            elif event.mouseevent.button == 3: 
                self.CurPicked = self.PickerTable[event.artist]
                self.PickedSettingMode = True
                

            #if isinstance(event.artist, COrderMark):
            #    print(event)
        self.Canvas.mpl_connect('key_press_event', on_press)
        self.Canvas.mpl_connect('key_release_event', on_release)
        self.Canvas.mpl_connect('button_press_event', on_press_mouse)
        self.Canvas.mpl_connect('button_release_event', on_release_mouse)
        self.Canvas.mpl_connect("motion_notify_event", hover)
        self.Canvas.mpl_connect("scroll_event", wheel)
        self.Canvas.mpl_connect("pick_event", picked)
        self.Annot = None
        self.LeftID = 0
        self.RightID = -1
        self.CandleCollections = []
        self.UnbathcedOrders = None
        self.DateToX = {}
        self.XToDate = {}
        self.XToPrices = {}
        self.COrderToggle = False
        
    def saveConditionOrderMark(self, mark):

        for hand in self.OnSaveCOMarkHandlers:

            hand(mark)
      
        mark.SetDirty(False)
    
    def setCOrderStarted(self, mark, started):
        for hand in self.OnStartCOMarkHandlers:
            hand(mark, started)
    
    def createConditionOrderMark(self, x,y, eventCaller = None ):
    
        
    
        newMark = COrderMark()
        newMark.Init(self.Axes, True, x,y)
        artists = newMark.GetArtists()
        for art in artists:
            self.blitMgr.add_artist(art)
            
        self.registerToPickerTable(artists, newMark)  
        
        if eventCaller is None:
            eventCaller = self
        for hand in self.OnCreateCOMarkHandlers:
            hand(newMark, eventCaller)
        return newMark

    def registerToPickerTable(self, artists, targetObject):
        for art in artists:
            self.PickerTable[art] = targetObject
        self.PickerTable_Inv[targetObject] = artists
    
    def unregisterFromPickerTable(self, targetObject):
        if targetObject in self.PickerTable_Inv:
            for art in self.PickerTable_Inv[targetObject]:
                del self.PickerTable[art]
            del self.PickerTable_Inv[targetObject]
    def Init(self):
        self.Annot = self.Axes.annotate("", xy=(0,0), xytext=(5,5),textcoords="offset points", animated = True)
        self.Annot.set_visible(False)
        
        ylims = self.Axes.get_ylim()
        rect = patches.Rectangle(
                (0, ylims[0]),                   # (x, y)
                200, ylims[1] - ylims[0],
                linewidth=1.0,
                fill = True, animated = True)
        rect.set_visible(False)
        
        self.ZoomRect = rect
        self.Axes.add_patch(rect)
        
        self.blitMgr = BlitManager(self.Canvas, [self.Annot, self.ZoomRect])
        #self.blitMgr = BlitManager(self.Figure.canvas, [self.Annot, self.ZoomRect])
        
        #self.Canvas.draw()
        
    def __addPrices(self, prices, startIndex):
        priceCount = len(prices)

        for idx, date in prices['date'].iteritems():           
            self.DateToX[date] = idx+ startIndex
            self.XToDate[idx+ startIndex] = date
            
        pLists = prices[['open','high','low','close']].values.tolist()
        for index, value in enumerate(pLists):
            self.XToPrices[index+ startIndex] = value

        if self.UnbathcedOrders is not None and len(self.UnbathcedOrders) > 0:
            self.__resolveUnbatchedOrders(prices[['date']].copy())
        
        
        
        candleCollection = CreateCandles(prices['open'], prices['high'], prices['low'], prices['close'], width=0.4, colorup='red', colordown='blue', alpha=0.75, startID = startIndex)
        candleCollection.Insert(self.Axes)
        
        
        self.CandleCollections.append(candleCollection)
        self.Axes.set_yscale('log')
        self.Axes.yaxis.set_major_locator(ticker.AutoLocator())
        self.Axes.yaxis.set_major_formatter(ticker.ScalarFormatter())

        self.Axes.yaxis.set_minor_formatter(ticker.ScalarFormatter())
        def format_date(x, y):
            int_x = int(x)
            if int_x in self.XToDate:
                return "{0}".format(self.XToDate[int_x])
            return ""
        self.Axes.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        self.Axes.xaxis.set_minor_formatter(ticker.FuncFormatter(format_date))
        self.Axes.grid(True)
        

        self.Canvas.draw()
    
    def RelimY(self):
        maxY =float('-inf')
        minY =float('inf')
        
        xlims = self.Axes.get_xlim()
        #print(self.XToPrices)
        for idx in range(int(xlims[0]), int(xlims[1])):
            if not(idx in self.XToPrices):
                continue
        
            p = self.XToPrices[idx]
            high = p[1]
            low = p[2]
            
            if high > maxY:
                maxY = high
            if low < minY:
                minY = low
            
        self.Axes.set_ylim([minY, maxY])
    
        
    def AddPricesLeft(self, prices):    
        priceCount = len(prices)
        self.__addPrices(prices, self.LeftID - priceCount)
        self.LeftID = self.LeftID - priceCount
        
    def AddPricesRight(self, prices):
        priceCount = len(prices)
        self.__addPrices(prices, self.RightID+1)
        self.RightID = self.RightID + priceCount
        

    def AddOrders(self, orders):
        self.UnbathcedOrders = orders

        self.__resolveUnbatchedOrders(pd.DataFrame(list(self.DateToX.keys()), columns = ['date']))


    def __resolveUnbatchedOrders(self, dates):
        
        
        self.UnbathcedOrders['temp_index']= self.UnbathcedOrders.index
        #print(self.UnbathcedOrders)
        dates['temp_index2'] = dates.index
        #print(self.UnbathcedOrders)
        #print(dates)
        resultOrders = pd.merge(dates[['temp_index2','date']], self.UnbathcedOrders, how='inner', on='date')
        orderGroup = resultOrders.groupby(['date','buyORsell'])
        self.UnbathcedOrders = self.UnbathcedOrders.drop(resultOrders['temp_index'])
        #print(self.UnbathcedOrders)
        buyIndex = []
        buyPrice = []
        buyQuantity = []
        sellIndex = []
        sellPrice = []
        sellQuantity = []
        for name, group in orderGroup:
            orderDateIndex = self.DateToX[name[0]]
            orderType = name[1]
            #print(group)
            #print(type(group))
            allCount = group['execQuantity'].sum()
            execAmount = (group['execPrice'] *group['execQuantity']).sum()
            
            if allCount > 0:
                if orderType :
                    buyIndex.append(orderDateIndex)
                    buyPrice.append(execAmount/allCount)
                    buyQuantity.append(allCount)
                else:
                    sellIndex.append(orderDateIndex)
                    sellPrice.append(execAmount/allCount)
                    sellQuantity.append(allCount)
        if len(buyIndex)>0:            
            self.Axes.plot(buyIndex, buyPrice, marker = 'o', markeredgecolor = 'red',markerfacecolor='red', linestyle='None', markersize = 7)    
            self.Axes.plot(buyIndex, buyPrice, marker = '_', color='black', linestyle='None', markersize = 12)   
            
            curOID = 0
            for oID in buyIndex:
                self.Axes.text(oID,buyPrice[curOID],buyQuantity[curOID],
                fontsize=5,
                color="white",
                verticalalignment ='center', 
                horizontalalignment ='center',
                weight="bold")
                #bbox ={'facecolor':'none', 'edgecolor':'black', 'alpha':1,  'boxstyle':'circle', 'pad':0.1})     
                curOID = curOID + 1
        if len(sellIndex)>0:            
            self.Axes.plot(sellIndex, sellPrice, marker = 'o',markeredgecolor = 'blue',markerfacecolor='blue', linestyle = 'None', markersize = 7)                    
            self.Axes.plot(sellIndex, sellPrice, marker = '_', color='black', linestyle='None', markersize = 12)  
            curOID = 0
            for oID in sellIndex:
                self.Axes.text(oID,sellPrice[curOID],sellQuantity[curOID],
                fontsize=5,
                color="white",
                verticalalignment ='center', 
                horizontalalignment ='center',
                weight="bold")
                #bbox ={'facecolor':'none', 'edgecolor':'black', 'alpha':1,  'boxstyle':'circle', 'pad':0.1})     
                curOID = curOID + 1

    def RemoveCanvas(self):
        if self.Canvas:
            self.BaseWidget.ChartPlace.layout().removeWidget(self.Canvas)
            self.Canvas.deleteLater()
            self.Canvas = None
   

   
    def Clear(self):

        self.PickerTable_Inv = {}
        self.PickerTable = {} 
        self.COrderToggle = False
        self.blitMgr = None
        self.DateToX = {}
        self.XToDate = {}
        self.XToPrices = {}
        self.UnbathcedOrders = None
        self.Axes.clear()
        self.LeftID = 0
        self.RightID = -1
        self.CandleCollections = []
    
    def SetName(self, name):
        self.BaseWidget.ChartInfo_Name.setText(name)
        
    def SetPeriod(self, startDate, endDate):
        periodString = "{0} ~ {1}".format(startDate.strftime('%Y-%m-%d'), endDate.strftime('%Y-%m-%d'))
        self.BaseWidget.ChartInfo_Period.setText(periodString)
        

        
   
    
    
class CandleCollection:
   def __init__(self, lines, bars):
        self.lines = lines
        self.bars = bars
        
   def Insert(self, axes):
        axes.add_collection(self.lines)
        axes.add_collection(self.bars)

def CreateCandles(opens, highs, lows, closes, width=4, colorup='k', colordown='r', alpha=0.75, startID = 0):

    delta = width / 2.
    barVerts = [((startID+i - delta, open),
                (startID+i - delta, close),
                (startID+i + delta, close),
                (startID+i + delta, open)) for i, open, close in zip(xrange(len(opens)), opens, closes) if open != -1 and close != -1]

    rangeSegments = [((startID+i, low), (startID+i, high)) for i, low, high in zip(xrange(len(lows)), lows, highs) if low != -1]

    colorup = mcolors.to_rgba(colorup, alpha)
    colordown = mcolors.to_rgba(colordown, alpha)
    colord = {True: colorup, False: colordown}
    colors = [colord[open < close] for open, close in zip(opens, closes) if open != -1 and close != -1]

    useAA = 0,  # use tuple here
    lw = 0.5,   # and here

    rangeCollection = LineCollection(rangeSegments, colors=colors, linewidths=lw, antialiaseds=useAA,)

    barCollection = PolyCollection(barVerts, facecolors=colors, edgecolors=colors, antialiaseds=useAA, linewidths=lw,)



    minx, maxx = 0, len(rangeSegments)
    miny = min([low for low in lows if low != -1])
    maxy = max([high for high in highs if high != -1])
    corners = (minx, miny), (maxx, maxy)
    
    return CandleCollection(rangeCollection, barCollection)
