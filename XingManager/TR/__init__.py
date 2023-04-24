from TR.XAQueryT8413 import Command_XAQueryT8413
from TR.XAQueryT8430 import Command_XAQueryT8430
from TR.XAQueryT8407 import Command_XAQueryT8407
from TR.XAQueryT1102 import Command_XAQueryT1102
from TR.XAQueryT0167 import Command_XAQueryT0167
from TR.XAQueryT3320 import Command_XAQueryT3320
from TR.XAQueryT8417 import Command_XAQueryT8417
from .XAQueryT0424 import Command_XAQueryT0424
from .XAQueryT0425 import Command_XAQueryT0425
from TR.XAQueryCSPAQ13700 import Command_XAQueryCSPAQ13700
from TR.XAQueryCSPAT00600 import Command_XAQueryCSPAT00600
from TR.XARealNWS import Command_XARealNWS
from TR.XARealSC1 import Command_XARealSC1
from TR.XARealJIF import Command_XARealJIF
from TR.XAQueryForStockState import Command_XAQueryT1404, Command_XAQueryT1405, Command_XAQueryT1410
import sys

__all__ = [
'Command_XAQueryT8413','Command_XAQueryT3320', 'Command_XAQueryT1102','Command_XAQueryT1404',
'Command_XAQueryT1405','Command_XAQueryT1410','Command_XAQueryT8430', 'Command_XAQueryT0167', 'Command_XAQueryT8417',
'Command_XAQueryT0424','Command_XAQueryT0425', 'Command_XAQueryCSPAQ13700',
'Command_XARealNWS', 'Command_XARealSC1', 'Command_XARealJIF', 'Command_XAQueryT8407', 'Command_XAQueryCSPAT00600']

# (차후 업데이트)자동화 가능함
'''
import os.path, pkgutil

import sys, inspect
def print_classes(mName):
    for name, obj in inspect.getmembers(sys.modules[mName]):
        if inspect.isclass(obj):
            print(obj)

pkgpath = os.path.dirname('TR/')
#print(__name__)
for _, name, _ in pkgutil.iter_modules([pkgpath]):
    #print_classes(name)
    from '.{0}'.format(name)
#print([name for _, name, _ in pkgutil.iter_modules([pkgpath])])
'''
