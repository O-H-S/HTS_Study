
from enum import Enum

class LookType(Enum):
    NONE = -1
    DIRTY = 0
    ACTIVE_BUY = 1
    ACTIVE_SELL = 2
    INACTIVE = 3


class COrderMark:
    def __init__(self):
        self.Body = None
        self.ID = -1
        self.Line = None
        self.buyORsell =False 
        self.__lineSeg = None
        self.dirty = False
        self.started = False
        self.active = False
        self.__curLook = LookType.NONE
    def Init(self, targetAxes, buyORsell, xd, yd):
    
        
        self.Body = targetAxes.plot([xd], [yd], marker = '^', markeredgecolor = 'red', markerfacecolor='red', linestyle='None', markersize = 6, animated = True, picker = 8, zorder=3) 
        self.Line = targetAxes.hlines(y=yd, xmin= -10000, xmax=xd, colors='red', linestyles=(0, (3, 5, 1, 5)), lw=1.0, zorder=2)
        self.__lineSeg = self.Line.get_segments()
        
        self.SetBuyOrSell(buyORsell)
        self.SetDirty(True)
      
        self.SetActive(False)
        
        #print(type(self.__lineSeg))
    def MoveTo(self, x, y):
        x = int(x)
        y = int(y)
    
        self.Body[0].set_data((x, y))
        
        nArray = self.__lineSeg[0] # firstLine
        #nArray[0,0] = #firstPoint_x
        nArray[0,1] = y
        nArray[1,0] = x
        nArray[1,1] = y
        #FirstLine_Start = nArray[0,0]
        #FirstLine_End = nArray[0,1]
        #self.__lineSeg 
        self.Line.set_segments(self.__lineSeg )
    
    def SetID(self, ID):
        self.ID = ID
     
        
    def SetBuyOrSell(self, buyORsell):       
        self.buyORsell = buyORsell
        
        self.__updateLook(LookType.ACTIVE_SELL)
        
    def SetDirty(self, dirty, update = True):
        self.dirty = dirty

        self.__updateLook(LookType.DIRTY)
    
    def SetStarted(self, started):
        self.started = started
        
        self.__updateLook()
    
    def SetActive(self, active):
        self.active = active
        
        self.__updateLook()
    
    def GetPrice(self):
        return self.Body[0].get_ydata()
        
    def GetPosition(self):
        return self.Body[0].get_data()
    
    
    def __updateLook(self, lookType = None):
        #if lookType == self.CurLookType:
        #    return
    
        if self.buyORsell:
            self.Body[0].set_marker('^')
            if self.dirty:
                self.Body[0].set_markeredgecolor('black')
                self.Body[0].set_markerfacecolor('darkorange')
                self.Line.set_color('darkorange')
                self.CurLookType = LookType.DIRTY
            elif not self.started :
                self.Body[0].set_markeredgecolor('black')
                self.Body[0].set_markerfacecolor('gray')
                self.Line.set_color('gray')          
                self.CurLookType = LookType.INACTIVE
            else:          
                if self.active:
                    self.Body[0].set_markeredgecolor('yellow')
                    self.Body[0].set_linewidth(2)
                else:
                    self.Body[0].set_markeredgecolor('red')
                    self.Body[0].set_linewidth(1)
                self.Body[0].set_markerfacecolor('red')
                self.Line.set_color('red')
                self.CurLookType = LookType.ACTIVE_BUY
            
            
        else:
            self.Body[0].set_marker('v')
            if self.dirty:
                self.Body[0].set_markeredgecolor('black')
                self.Body[0].set_markerfacecolor('darkorange')
                self.Line.set_color('darkorange')
                self.CurLookType = LookType.DIRTY
            elif not self.started :
                self.Body[0].set_markeredgecolor('black')
                self.Body[0].set_markerfacecolor('gray')
                self.Line.set_color('gray')      
                self.CurLookType = LookType.INACTIVE        
            else:                             
                if self.active:
                    self.Body[0].set_markeredgecolor('yellow')
                    self.Body[0].set_linewidth(2)
                else:
                    self.Body[0].set_markeredgecolor('blue')
                    self.Body[0].set_linewidth(1)
                self.Body[0].set_markerfacecolor('blue')
                self.Line.set_color('blue')
                self.CurLookType = LookType.ACTIVE_SELL

    
    def GetArtists(self):
        return [self.Line, self.Body[0]]
