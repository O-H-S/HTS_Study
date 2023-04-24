from multiprocessing.managers import BaseManager, SyncManager
import threading
import mmap,random
import time, sys,os
from queue import Queue

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Common.GlobalLogging import LogManager
logMgr = LogManager("XingManager.IPC")
logger = logMgr.logger

class RealtimeChannel:
    def __init__(self, name, blockSize, maxCount, memFormat):
        self.name = name
        self.blockSize = blockSize
        self.maxCount = maxCount
        self.memName = name + str(random.random())
        memLength = self.maxCount * self.blockSize
        
        self.mem = mmap.mmap(-1, memLength, self.memName)
        self.memLength = memLength
        self.mem.seek(0)

        self.memFormat = memFormat
        self.curIndex = 0
        self.WriteLock = threading.Lock()
        
        self.ipcMgr = None
        self.WriteQueue = Queue()
        
        self.SendingThread = threading.Thread(target = self.SendToClient, name="RealtimeChannel")
        self.SendingThread.start()
        
    def SendToClient(self):  
        while True:
            
            try:
                targetData = self.WriteQueue.get()
                if targetData is False:
                    break
               
                oldIndex = self.curIndex
                writtenSize = self.mem.write(targetData)
                if writtenSize != self.blockSize:
                    print("ch eror", writtenSize, self.blockSize)
                               
                self.mem.flush()
                self.curIndex = self.curIndex + 1
                if self.curIndex == self.maxCount:
                    self.curIndex = 0
                    self.mem.seek(0)
                logger.debug("send bytes")
                self.ipcMgr.SendToChannel(self.name, oldIndex)
            except:
                raise
                break
        logger.info("Channel Thread Down")
    
    def Write(self, data):

        self.WriteQueue.put(data)
    
        #self.WriteLock.acquire()
        
        #self.WriteLock.release()
        return 0

class IPCManager:
    def __init__(self, msgCallback):        
        self.currentCommandKey = -1
        self.Commands = {}
        self.MessageHandler = msgCallback
        self.Mems = {}
        self.RealtimeChannels = {}
    def Close(self):
    
        for name, ch in self.RealtimeChannels.items():
            ch.Write(False)
        
        self.manager_serverObject.stop_event.set()
        # self.Mems 해제 루프 필요함.
        #stop_timer = threading.Timer(1, lambda:self.manager_serverObject.stop_event.set())
        #stop_timer.start()
        
    def OpenManager(self):
        SyncManager.register('OnMessageFromMain', self.MessageCallback)
        self.manager_server = SyncManager(address=('127.0.0.1', 0), authkey= b'XingManager') # setting the port to 0 allows the OS to choose.
        self.manager_serverObject = self.manager_server.get_server()
        def serving():
            try:
                logger.debug("opening manager...")
                self.manager_serverObject.serve_forever()
            except Exception as e:
                logger.error("[ipcMgr Error] :", e)
            logger.error("[ipcMgr server exiting")

            
        
        self.thread = threading.Thread(target = serving, name="IPC_Server")
        self.thread.start()

        #self.server = self.manager_server.get_server()
        #self.manager_server.start()

        #while True:
        #    time.sleep(1)
    def MessageCallback(self,name, args):
        if name == "System":
            if args[0] == "ReleaseMem":
                self.ReleaseMem(args[1])
                
            return   
        self.MessageHandler(name, args)
    def ConnectToManager(self, ip, port):
        SyncManager.register('OnMessageFromXing')
        SyncManager.register('RealtimeChannel')
        self.manager = SyncManager(address=(ip, port), authkey=b'123')
        self.manager.connect()
             
        self.OpenManager()
        self.SendMessageToMain("IPC_CON", (self.manager_serverObject.address[0], self.manager_serverObject.address[1]))
    
    
            
    
    def RegisterChannel(self, channel):
        
        self.RealtimeChannels[channel.name] = channel
        channel.ipcMgr = self
        self.manager.OnMessageFromXing("RealtimeChannel", (channel.name, channel.memName, channel.blockSize, channel.maxCount, channel.memLength, channel.memFormat) )
    
    def SendToChannel(self, name, index):
        self.manager.RealtimeChannel(name, index)   
    
    def SendMessageToMain(self, name, args):      
        result = self.manager.OnMessageFromXing(name, args)      
        #print(type(result))
        return result  
        
    def WriteToMem(self, name, byteArray, length):

        if length < 1:
            return False
        self.Mems[name] = mmap.mmap(-1, length, name)
        mm = self.Mems[name]
        mm.seek(0)
        if type(byteArray) is list:
            for bA in byteArray:
                mm.write(bA)
        else:
            mm.write(byteArray)
        mm.flush()
        return True
        
    def ReleaseMem(self, name):
        if name in self.Mems:
            if not self.Mems[name].closed:
                self.Mems[name].close()
            del self.Mems[name]


        
        

    
     

