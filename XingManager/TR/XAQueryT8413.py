
import struct
from XingCommand import XingQueryCommand
__imple__ = 'Command_XAQueryT8413'
# 일봉 데이터 조회
class Command_XAQueryT8413(XingQueryCommand):
    ResFileName = ".\\Res\\t8413.res"
    #override
    def Init(self):
        
        # self.input_shcode input_sdate input_edate    
        self.inst.SetFieldData("t8413InBlock", "shcode", 0, self.input_shcode)
        self.inst.SetFieldData("t8413InBlock", "gubun", 0, "2") # 2 일봉
        self.inst.SetFieldData("t8413InBlock", "sdate", 0, self.input_sdate)
        self.inst.SetFieldData("t8413InBlock", "edate", 0, self.input_edate)
        self.inst.SetFieldData("t8413InBlock", "comp_yn", 0, "Y") # 압축 여부
        # void SetFieldData (BSTR szBlockName,BSTR szFieldName,LONG nOccursIndex, BSTR szData)
        # nOccursIndex 연속되는 값들일 경우, 어디부터 시작할 것인지를 나타내는것같다.
    
    #override
    def OnFinish(self, result):
        if not result:
            return
            
        resultDecom = self.inst.Decompress("t8413OutBlock1")
        if resultDecom <= 0:
            print("[main] decompress error")  
            
        count = self.inst.GetBlockCount("t8413OutBlock1")
        if count == 2000: #다못가져왔을경우.
            self.complete = False
        else:
            self.complete = True
        
    @classmethod
    def Create(cls, parentCommandID, shcode, sdate, edate):
        newCommand = cls(parentCommandID)
        newCommand.input_shcode = shcode
        newCommand.input_sdate = sdate
        newCommand.input_edate = edate         
        return newCommand
        
    def ToBytes(self):
        tr = self.inst
        #blockData = tr.GetBlockData("t8413OutBlock1") 아주 일부의 데이터만 가져옴 버그인듯
        #blockDataEncoded = blockData.encode('utf-8')
        count = tr.GetBlockCount("t8413OutBlock1")
        metadata = {}
        metadata['Format'] = '8siiiiiid'      
        metadata['MemberFormat'] = [("date", "string", 8), ("open", None, 4), ("high", None, 4), ("low", None, 4), ("close", None, 4), ("jongchk", None, 4), ("pricechk", None, 4), ("rate", None, 8)]
        # None은 unpack후 캐스팅을 하지 않는다는 뜻임.
        
        sizePerRow = struct.calcsize(metadata['Format'])
        #print(sizePerRow)
        totalBytes = (sizePerRow) * count        
        refinedBytearray = bytearray(totalBytes) 
        #print(len(blockDataEncoded), count)
        for i in range(count):
            startByte = sizePerRow * i
            # 데이터의 문자열이 모두 숫자이므로 한글자당 1바이트로 취급가능하다.
            # memoryview로  string 사용 불가능
            # unsafe를 사용하여 string 내부의 바이트배열에 간접적으로 접근가능하긴하나 복잡해보임.
            date = tr.GetFieldData("t8413OutBlock1", "date", i).encode('utf-8')
            #open_intByte = int(tr.GetFieldData("t8413OutBlock1", "open", i)).to_bytes(4, byteorder='big', signed =False)
            open_int = int(tr.GetFieldData("t8413OutBlock1", "open", i))
            high_int = int(tr.GetFieldData("t8413OutBlock1", "high", i))
            low_int = int(tr.GetFieldData("t8413OutBlock1", "low", i))
            close_int = int(tr.GetFieldData("t8413OutBlock1", "close", i))
            jongchk_int = int(tr.GetFieldData("t8413OutBlock1", "jongchk", i))
            pricechk_int = int(tr.GetFieldData("t8413OutBlock1", "pricechk", i))
            if tr.GetFieldData("t8413OutBlock1", "pricechk", i) != '0':
                print("pricechk : ", tr.GetFieldData("t8413OutBlock1", "pricechk", i))
            rate_double = float(tr.GetFieldData("t8413OutBlock1", "rate", i))
            
            #print(tr.GetFieldData("t8413OutBlock1", "close", i), tr.GetFieldData("t8413OutBlock1", "rate", i), tr.GetFieldData("t8413OutBlock1", "pricechk", i), tr.GetFieldData("t8413OutBlock1", "jongchk", i))
            pack_result = struct.pack(metadata['Format'], date, open_int, high_int, low_int, close_int, jongchk_int, pricechk_int, rate_double)
            refinedBytearray[startByte : startByte + sizePerRow] = pack_result
            #unpack_result = struct.unpack(metadata['Format'], pack_result)
            #print(unpack_result)
            #print(open_int, unpack_result[1])
            #print(len(refinedBytearray))
            #print(high)
            #print(type(high))
            #print(len(date.encode()) ,len(open2.encode()),len(high.encode()) ,len(low.encode()), len(close.encode()))
            #print(len(date) ,len(open2),len(high) ,len(low), len(close))
        
        metadata['Length'] = totalBytes
        metadata['Count'] = count
        
        return(metadata, refinedBytearray)