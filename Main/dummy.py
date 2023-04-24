from pandas import Series, DataFrame

kakao2 = Series([92600, 92400, 92100, 94300, 92300], index=['2016-02-19',
                                                            '2016-02-18',
                                                            '2016-02-17',
                                                            '2016-02-16',
                                                            '2016-02-15'])
print(kakao2)

for date in kakao2.index:
    print(date)

for ending_price in kakao2.values:
    print(ending_price)


global manager     
SyncManager.register('my_object', ttt)
SyncManager.register('my_object2')
manager = SyncManager(address=('127.0.0.1', 1234), authkey= b'123') # setting the port to 0 allows the OS to choose.



#server = manager.get_server()
#server.serve_forever()
thread = threading.Thread(target = serving)
thread.start()

time.sleep(1)
self.ConnectManager()


def classlookup(cls):
    c = list(cls.__bases__)
    for base in c:
        c.extend(classlookup(base))
    return c
    
'''      
    def setChart(self, chartFigure, priceData):
        def hover(event):
            if event.inaxes == ax:
                #print(event.xdata, event.ydata)
                #cont, ind = sc.contains(event)
                #if cont:
                    # change annotation position
                x_int = int(round(event.xdata)  )
                #print(x_int)                
                x_int = max(0, min(x_int, len(priceData)-1))
                #print(x_int)
                annot.xy = (event.xdata, event.ydata)
                
                # write the name of every point contained in the event
                annotString = "{0}\nHigh {1}\nOpen {2}\nClose{2}\nLow {4}".format(priceData.iloc[x_int]["date"], priceData.iloc[x_int]["high"], priceData.iloc[x_int]["open"], priceData.iloc[x_int]["close"], priceData.iloc[x_int]["low"])
                annot.set_text(annotString)
                
                
                annot.set_visible(True)   
                if self.press_StartID > -1:
                    rect.set_width( x_int- self.press_StartID)
                
                self.canvas.draw()
                #else:
                #    annot.set_visible(False)
        
        self.press_StartID = -1
        def on_press(event):
            #print(event)
            if event.inaxes == ax:
                x_int = int(round(event.xdata)  )
                if x_int < 0 or x_int > len(priceData)-1:
                    return
                self.press_StartID = max(0, min(x_int, len(priceData)-1))
                rect.set_visible(True)
                rect.set_x(self.press_StartID)
                ylims = ax.get_ylim()
                rect.set_y(ylims[0])
                rect.set_height(ylims[1] - ylims[0])
                
        def on_release(event):
            rect.set_visible(False)
            if event.inaxes == ax:
                
                if self.press_StartID < 0:
                    return
                    
                x_int = int(round(event.xdata))
                if x_int < 0 :
                    
                    return
                    
                    
                x_int = max(0, min(x_int, len(priceData)-1))
                
                
                
                if x_int < self.press_StartID:
                    subP = sorted(priceData.loc[0:len(priceData),"close"])
                    minY = subP[0] 
                    maxY = subP[-1]
                    
                    #print(minY, maxY, len(priceData))
                    #print(subP)
                    
                    
                    gap = maxY - minY
                    #print(gap)
                    #print([max(1,minY-gap*0.2),maxY+gap*0.2])
                    ax.set_xlim([0, len(priceData)])
                    ax.set_ylim(max(minY * 0.8,minY-gap*0.2),maxY+gap*0.2)                   
                    self.canvas.draw()
  
                elif x_int > self.press_StartID:
                    subP = sorted(priceData.loc[self.press_StartID:x_int+1,"close"])
                    
                    minY = subP[0] 
                    maxY = subP[-1]
                    gap = maxY - minY
                    #print(gap)
                    #print([max(1,minY*0.2),maxY+gap*0.2])
                    ax.set_xlim([self.press_StartID, x_int])
                    ax.set_ylim([max(0,minY-gap*0.2),maxY+gap*0.2])
                    self.canvas.draw()
                ax.yaxis.set_major_locator(ticker.AutoLocator())
                ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        
                #ax.yaxis.set_minor_locator(ticker.Au())
                ax.yaxis.set_minor_formatter(ticker.ScalarFormatter())
                self.press_StartID = -1
                #print([self.press_StartID, x_int])
                
                
        
        self.canvas.mpl_connect('button_press_event', on_press)
        self.canvas.mpl_connect('button_release_event', on_release)
    '''
    
'''        
        mm = mmap.mmap(-1, 1000, "ARandomTagName")
        mm.seek(0)
        print(mm.readline())

        mm.close()
    '''   