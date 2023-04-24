from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView, QWidget, QMainWindow, QApplication, QCompleter
import os






    
def clientFunc(a,b,c):
    print(a,b,c)

def testFunc(x,y, *args):  
    clientFunc(args)


testFunc(-1, 0, 1,2,3)

'''
import signal
import threading
import random

import time ,sys, os

from datetime import datetime, timedelta
   
# __file__ 은 두가지 경우에 따라 값이 달라짐.
# import 됨 : 절대경로?
# 직접 실행됨 : 상대경로
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Common.SearchLine import SearchLine

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import OpenDartReader
#api_key = 'a1c6861548bb7876b0ecdb8bc1801162fdc489cb '
#api_key = 'a1c6861543f8bb7876b0ecdb8bc1801162fdc489cb '

try:
    dart = OpenDartReader(api_key) 
except Exception as e:
    print(e)


result = dart.finstate('005930', 2018, reprt_code='11014')
print(result)




#print(datetime.timestamp(datetime(2018, 4, 11) - datetime(2018, 4, 10)))



def handler(signum, frame):
    print("Async :", threading.currentThread())
    print("Ctrl+C 신호를 수신했습니다.")


signal.signal(signal.SIGINT, handler)
print("Async :", threading.currentThread())
while True:
    print('대기중...')
    time.sleep(100)
    


run = True

def handler_stop_signals(signum, frame):
    global run
    run = False

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

while run:
    pass
'''