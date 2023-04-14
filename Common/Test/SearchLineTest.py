
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


def Testing():

    testLine = SearchLine([], 86400)
    for i in range(0, 100):
       
        curRandPoint = datetime(2000, 1, 1) + timedelta(days=random.randint(2, 1000))
        nextRandPoint = curRandPoint + timedelta(days=random.randint(0, 100))
        curRandPoint_timestamp = datetime.timestamp(curRandPoint)
        nextRandPoint_timestamp = datetime.timestamp(nextRandPoint)
        
        testLine.addSection((curRandPoint_timestamp, nextRandPoint_timestamp))
        testLine.print()
        if not testLine.verify() :
            break
        
'''
    lines = GetLinesInEdgecase(datetime(2000, 1, 1),  datetime(2010, 1, 1))
    
    print("생성한 모든 라인 검증 중...")
    for line in lines:
        print(" ")
        line.print()
        if not line.verify():
            return
    print("[검증 완료]")
    
    
    print("삽입 테스트 진행 중...")
    for line in lines:
        
        for testCount in range(10):
            print(testCount," iteration")
            cases = GetInsertionEdgecase(line)
            for case in cases:
                targetLine = line.Clone()
                targetLine.addSection(case)
                vResult = targetLine.verifyAddition(case)
                if not vResult:
                    targetLine.print()
            # 점, 구간 선택 = A, B
            # (1개, 2개)일치, (1개, 2개)unit 반경, 일반 
            # 점(반경, 일치, 일반) 랜덤
            # 구간(반경, 일치, 일반) 랜덤
            
'''          
               
def GetInsertionEdgecase(line):

    possibleCase = []
    
    sections = line.sections
    unit = line.unit
    sectCount = len(sections)
    
    # [점] (시작 or 사이 or 끝), (일치, 반경)
    # [구간] (시작 or 사이 or 끝 ), (일치, 반경)
    
    
    #----- 점, (시작 or 사이 or 끝), (일치, 반경)------
    
    
    randSection = None
    if sectCount > 0:
        randSection = sections[random.randint(0, sectCount-1)]

    # 점 - 시작 -(일치,반경)
    if randSection:
        possibleCase.append((randSection[0], randSection[0]))
        possibleCase.append((randSection[0] + unit, randSection[0] + unit))
        possibleCase.append((randSection[0] - unit, randSection[0] - unit))
        
    # 점 - 끝 -(일치,반경)
    if randSection:
        possibleCase.append((randSection[1], randSection[1]))
        possibleCase.append((randSection[1] + unit, randSection[1] + unit))
        possibleCase.append((randSection[1] - unit, randSection[1] - unit))
        
    # 점 - 사이 -(일치,반경)
    if randSection:     
        if randSection[0] != randSection[1]:
            randPoint = random.randrange(int(randSection[0]), int(randSection[1]), unit)     
            possibleCase.append((randPoint, randPoint))
    else:
        randDay = datetime.timestamp(GetRandomPoint(datetime(2000, 1, 1),  datetime(2010, 1, 1)))
        possibleCase.append((randDay, randDay))


    
    
    
    return possibleCase

def GetLinesInEdgecase(startDate, endDate):
    lines = []
    unit = 86400
    #Period = endDate - startDate
    
    
    # 빈 공간
    sections = []
    lines.append(SearchLine(sections, unit))
    
    # 점 하나
    sections = []    
    randDay = datetime.timestamp(GetRandomPoint(startDate, endDate))
    sections.append((randDay, randDay))
    lines.append(SearchLine(sections, unit))
       
    # 점 여러개
    sections = []    
    curRandPoint = startDate
    for i in range(20):
        curRandPoint = curRandPoint + timedelta(days=random.randint(2, 100))
        if curRandPoint > endDate:
            break
        curRandPoint_timestamp = datetime.timestamp(curRandPoint)
        sections.append((curRandPoint_timestamp, curRandPoint_timestamp))
    lines.append(SearchLine(sections, unit))
    
    
    # 점과 구간 여러개
    sections = []    
    curRandPoint = startDate
    for i in range(20):
        curRandPoint = curRandPoint + timedelta(days=random.randint(2, 100))
        if curRandPoint > endDate:
            break
        if random.randint(0, 10) < 5: #점 생성
            curRandPoint_timestamp = datetime.timestamp(curRandPoint)
            sections.append((curRandPoint_timestamp, curRandPoint_timestamp))
        else: #구간 생성
            nextRandPoint = curRandPoint + timedelta(days=random.randint(1, 100))
            curRandPoint_timestamp = datetime.timestamp(curRandPoint)
            nextRandPoint_timestamp = datetime.timestamp(nextRandPoint)
            sections.append((curRandPoint_timestamp, nextRandPoint_timestamp))
            curRandPoint = nextRandPoint
        
        
    lines.append(SearchLine(sections, unit))
      
    return lines
 
def GetRandomPoint(startDate, endDate):
    time_between_dates = endDate - startDate
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = startDate + timedelta(days=random_number_of_days)
    return random_date


#Testing()