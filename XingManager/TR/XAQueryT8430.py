
import struct
from XingCommand import XingQueryCommand
__imple__ = 'Command_XAQueryT8430'
# 종목 조회
class Command_XAQueryT8430(XingQueryCommand):

    ResFileName = ".\\Res\\t8436.res"

    #override
    def Init(self):
        self.inst.SetFieldData("t8436InBlock", "gubun", 0, self.gubun)
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName,LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
        
    @classmethod
    def Create(cls, kospi, kosdaq):
        newCommand = cls()
        newCommand.kospi = kospi
        newCommand.kosdaq = kosdaq
        
        gubunV = '0'
        if kospi and not kosdaq:
            gubunV = '1'
        elif not kospi and kosdaq:
            gubunV = '2'
        
        newCommand.gubun = gubunV
              
        return newCommand
               

    def ToBytes(self):

        tr = self.inst
        count = tr.GetBlockCount("t8436OutBlock")
        #blockData = tr.GetBlockData("t8436OutBlock") # 이름 바이트의 크기가 뒤죽박죽임 20~24 사이임. 나머지는 고정적인듯.
        #print(chardet.detect(blockData))
        #encoded = blockData.encode('utf-8')
        #print(blockData)
        #print("count", count)
        #print("encoded length" , len(encoded))
        #print(encoded)
        #print(struct.unpack('82s', encoded))
        
        #BytesExceptName = 57
        BytesExceptName = 19+3
        
        #while i < totalBytes:
            
        
        #print(type(blockData), " " , count, " ", sys.getsizeof(blockData), " ", len(blockData))
        #subList_name = []
        #subList_shcode = []
        #subList_expcode = []
        
        #for i in range(300):
        #    print(i,"]",encoded[0:i+1])
        
        searchSize = count
        nameByteSize = 80
        #한글자당 최대 4바이트를 사용한다. 
        #만약 20글자가 최대라면 20*4 까지 필요할수 있다.
        #실험결과 30바이트로 충분했음.
        totalBytes = (BytesExceptName + nameByteSize) * searchSize
        
        refinedBytearray = bytearray(totalBytes) # bytearray는 mutable 타입이므로 객체 할당시 객체 생성이 일어나지 않는다. 적합한 타입이다.
        for i in range(searchSize):
            #print("변경 전 길이 :", len(refinedBytearray))
            startByte = (BytesExceptName + nameByteSize) * i
            hname = tr.GetFieldData("t8436OutBlock", "hname", i) #22~ 24 #이름 잘림 현상 발생, 바로 프린트해도 발생함.

            hname_encoded = hname.encode('utf-8')
            #print(hname , hname_encoded)
            # ljust(20) 을 이용하여 오른쪽 공백을 채울수 있음
            shcode = tr.GetFieldData("t8436OutBlock", "shcode", i)          
            expcode = tr.GetFieldData("t8436OutBlock", "expcode", i)
            etfgubun = tr.GetFieldData("t8436OutBlock", "etfgubun", i)
            
            group = tr.GetFieldData("t8436OutBlock", "bu12gubun", i)
            spac = tr.GetFieldData("t8436OutBlock", "spac_gubun", i)
            
            #print("각 요소별 길이 ", len(hname.encode('utf-8')), len(shcode.encode('utf-8')), len(expcode.encode('utf-8')),len(etfgubun.encode('utf-8')) )
            nextField = startByte + nameByteSize 
            refinedBytearray[startByte : startByte + len(hname_encoded)] = hname_encoded
            #refinedBytearray[startByte + len(hname_encoded) : nextField ] = b' ' array의 크기가 작아짐. 새로 할당되는듯.
            #print(startByte,  startByte + len(hname))
            refinedBytearray[nextField : nextField + 6] = shcode.encode('utf-8')
            #print(nextField , nextField + 6)
            nextField = nextField + 6
            
            refinedBytearray[nextField : nextField + 12] = expcode.encode('utf-8')
            #print(nextField , nextField + 12)
            nextField = nextField + 12
            refinedBytearray[nextField : nextField + 1] = etfgubun.encode('utf-8')          
            nextField = nextField + 1
            
            refinedBytearray[nextField : nextField + 2] = group.encode('utf-8')
            nextField = nextField + 2
            
            refinedBytearray[nextField : nextField + 1] = spac.encode('utf-8')
            nextField = nextField + 1
            #print(nextField , nextField + 1)
            
            #resultList.append([hname, shcode, expcode, etfgubun])
        #print(len(refinedBytearray))
        #unpacked = struct.unpack('20s6s12s1s' * searchSize, refinedBytearray) # 1차원 튜플로 반환함
        #print(len(unpacked))
        #buf = struct.pack('20s' * len(subList_name), *subList_name)
        #print(refinedBytearray)
        metadata = {}
        metadata['Format'] = '80s6s12s1s2s1s'
        metadata['Length'] = totalBytes
        metadata['Count'] = count
        metadata['MemberFormat'] = [("name", "string", nameByteSize), ("shcode", "string", 6), ("expcode", "string", 12), ("etf", "string", 1), ("groupType", "string", 2), ("spac", "string", 1)]
        # metadata 첨부 : struct 의 format과 원소의 명세를 같이 보낸다.
        return (metadata, refinedBytearray)