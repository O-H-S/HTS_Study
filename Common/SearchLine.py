import time 
from datetime import datetime, timedelta
import random

class SearchLine: 
    def __init__(self, sections = None, unit = 1, dataToPoint = None, pointToData = None):        
        if sections:
            self.sections = sections
        else:
            self.sections = []
                  
        if dataToPoint and pointToData:
            self.rawData = True
        else:
            self.rawData = False
        self.unit = unit
        
    def Clone(self):
        copied = SearchLine(self.sections[:], self.unit)
        return copied
        
    def print(self):
        SearchLine.printSections(self.sections)
        
    def addSection(self, _section):
        section = _section
        if section[0] > section[1]:
            print("error", section[0], section[1])
        '''
        if not isinstance(section[0], int):
            print("not int start")
        if not isinstance(section[1], int):
            print("not int end")
        '''
        unit = self.unit
        '''
        
        if not self.rawData :
            section = (self.dataToPoint(_section[0]), self.dataToPoint(_section[1]))
        '''    
        sections = self.sections
        # edge case : 빈 섹션 리스트, start == end 구간 존재, section이 start == end
        sectCount = len(sections)
        
        a = section[0]
        b = section[1]
        
        aLeft = -1
        bLeft = -1
        
        #aLeft_Value = datetime.min.timestamp()
        #bLeft_Value = datetime.min.timestamp()
        
        for i in range(sectCount):
            curSect = sections[i]
            curStart = curSect[0]
            curEnd = curSect[1]
            if curStart <= a:
                aLeft = i
            if curStart <= b:
                bLeft = i
                
        newSections = []

        # newSections은 크게 3부분으로 A, B,C 나뉜다.
        # A : section을 포함하지 않는 section 전 부분.
        # B : section
        # C : section을 포함하지 않는 section 후 부분
        
        # A 부분 
        PartB_Start = a
        if aLeft < 0:
            # A구간은 존재하지 않는다.  
            PartB_Start = a # == -1 + 1 == 0
            pass
        else:
            if sections[aLeft][1] + unit < a :
                #0 ~ aLeft까지 그대로 넣는다. B구간의 시작은 a다
                newSections.extend(sections[0:aLeft+1])
                PartB_Start = a
            elif a <= sections[aLeft][1] + unit :
                # 0 ~ aLeft-1 까지 그대로 넣는다. B구간의 시작은 aLeft의 시작점이다
                if aLeft > 0:
                    newSections.extend(sections[0:aLeft]) # list[0:0]일 경우 아무 동작도 하지않는다.
                PartB_Start = sections[aLeft][0]
            else:
                print("error")
            
        # C 부분 (미리 계산해놓고 B를 넣은 뒤에 넣는다)
        newSectionsForC = []
        PartB_End = b
        if bLeft < 0:
            if sectCount > 0 :
               if b == sections[0][0] - unit :
                    PartB_End = sections[0][1]
                    if 1 < sectCount:
                        newSectionsForC.extend(sections[1:])
               else:
                    PartB_End = b
                    newSectionsForC.extend(sections[:])
            else:
                PartB_End = b
        
        elif bLeft+1 < sectCount and  b == sections[bLeft+1][0] - unit:
            PartB_End = sections[bLeft+1][1]
            if bLeft+2 < sectCount:
                newSectionsForC.extend(sections[bLeft+2:])

        elif sections[bLeft][0] <= b and b <= sections[bLeft][1] :
            PartB_End = sections[bLeft][1]
            if bLeft+1 < sectCount :
                newSectionsForC.extend(sections[bLeft+1:])
        elif sections[bLeft][1] < b : 
            if bLeft+1 < sectCount :
                if b < sections[bLeft+1][0] - unit:
                    PartB_End = b
                    newSectionsForC.extend(sections[bLeft+1:])
                else:
                    print("error")
            else:                
                PartB_End = b

        else:
            print("error")        

        # B 부분
        newSections.append((PartB_Start, PartB_End))
        
        # C 부분 (위에서 계산된것을 삽입)
        newSections.extend(newSectionsForC)
        print
        self.sections = newSections
        return newSections
        
    def getHolesBySection(self, section):
        sections = self.sections
        sectCount = len(sections)
        unit = self.unit
        a = section[0]
        b = section[1]
        
        x = -1
        y = -1
        
              
        for i in range(sectCount):
            curSect = sections[i]
            curStart = curSect[0]
            curEnd = curSect[1]
            if curStart <= a:
                x = i
            if curStart <= b:
                y = i
                
        lastEnd = 0
        finalStart = 0
        if x < 0:
            lastEnd = a
            x = 0
        elif a < sections[x][1] :
            lastEnd = sections[x][1] + unit
            x = x+1
        else:
            lastEnd = a
            x = x+1
            
        if y < 0:
            finalStart = b
        elif b <= sections[y][1]:
            finalStart = sections[y][0] - unit
            y = y-1
        else:
            finalStart = b
            
        holes = []
        if lastEnd > finalStart:
            return holes
            
        
        for i in range(x, y+1):
            holes.append((lastEnd, sections[i][0]))
            lastEnd = sections[i][1]
        holes.append((lastEnd, finalStart))
        return holes
        
    def getHolesBetween(self, firstID, lastID):
        # 생략 가능해보임
        if firstID >= lastID:
            return []
        
        holes = []
        for i in range(firstID, lastID):
            holes.append((self.sections[i][1], self.sections[i+1][0]))
        return holes   
        
    def verify(self, printing = True):
        # start <= end 검증
        for section in self.sections:
            if section[0] > section[1]:
                if printing:
                    print("검증 실패(1)")
                return False
                
        # end + unit < (next)start 검증
        sectCount = len(self.sections)
        for i in range(sectCount-1):
            curSection = self.sections[i]
            nextSection = self.sections[i+1]
            
            #print(curSection[1] , nextSection[0])
            if curSection[1] + self.unit < nextSection[0]:
                pass
            else:
                if printing:
                    print("검증 실패(2)")
                return False
        if printing:
            print("검증 성공!!")
        return True
        
    def verifyAddition(self, targetSection):
        if not self.verify(False):
            print("검증 실패(기본 제약)")
            return False
    
        contCount = 0
        for section in self.sections:
            if SearchLine.ContainTargetInSection(targetSection, section):
                contCount = contCount + 1
        
        if contCount != 1:
            print("검증 실패(포함) :", contCount)
            return False
        
        print("검증 성공!!")
        return True
        
    @classmethod
    def ContainTargetInSection(cls, targetSection, section):
        if section[0] <= targetSection[0] and section[1] >= targetSection[1]:
            return True
        return False
    
    @classmethod
    def printSections(cls, sections):
        allString = ""
        for section in sections:
            allString = allString + ''+ datetime.fromtimestamp(section[0]).strftime('%Y.%m.%d') + ' - ' + datetime.fromtimestamp(section[1]).strftime('%Y.%m.%d') + ' | '
        print(allString)
        print("Count :", len(sections))
        
        
    



'''
def getHolesBySection(section, sections):
    sectCount = len(sections)
    
    a = section[0]
    b = section[1]
    
    x = -1
    y = -1
    for i in range(sectCount):
        curSect = sections[i]
        curStart = curSect[0]
        curEnd = curSect[1]
        if curStart < a:
            x = i
        if curStart < b:
            y = i
    
    if x == y:
        
    
    bs = 0
    be = 0
    if x < 0 and sections[0][1] <= y:
        
    
    else:
        if sections[x][1] < a:
            bs = x + 1
        else :
            bs = x + 1
            a = sections[x][1]
        
    if sections[y][1] < b:
        be = y
    else :
        be = y - 1
        b = sections[y][0]
        
    holes = []  
    #구간 A
    holes.append((a, sections[bs][0]))
    
    #구간 B   
    holes.extend(getHolesBetween(bs, be, sections))
    
    #구간 C
    holes.append((sections[be][1], b)) 
    return holes


sections = []
count = 0
idx = 0
start_date = datetime(2000, 1, 30)
while idx < count:
    end_date = start_date + timedelta(days=random.randint(0, 3))
    sections.append((datetime.timestamp(start_date),datetime.timestamp(end_date)))
    start_date = end_date + timedelta(days=random.randint(1, 100))
    
    idx = idx +1
    
testSL = SearchLine(sections)
print("초기 구간들")
testSL.print()

print("--holes--")
holes = testSL.getHolesBySection((datetime.timestamp(datetime(2000, 1, 1)), datetime.timestamp(datetime(2010,1, 1))))
SearchLine.printSections(holes)
print("-----------")

for hole in holes:
    testSL.addSection(hole)
    testSL.print()


for i in range(100):
    randDate_Start = datetime(random.randint(2019, 2023), random.randint(1, 12), random.randint(1, 28))
    randDate_End = randDate_Start + timedelta(days=random.randint(0, 200))
    print("<<<<adding : ",randDate_Start, " - ", randDate_End,">>>>>")  
    testSL.addSection((datetime.timestamp(randDate_Start),datetime.timestamp(randDate_End)))
    testSL.print()
'''