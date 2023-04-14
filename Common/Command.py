import threading

class Command:
    CountFromStartup = 0
    Commands = {}
    
    @classmethod
    def Get(cls, ID):
        return Command.Commands[ID]
    
    def __init__(self, parentID = None, childrenID = None):
        self.ID = Command.CountFromStartup
        Command.CountFromStartup = Command.CountFromStartup + 1;
        
        self.parent = parentID
        self.children = childrenID
        
        Command.Commands[self.ID] = self
        
    def Release(self):
        del Command.Commands[self.ID]
        
        
WaitingCommands = set([])
class SyncCommand(Command):
    def __init__(self, parentID = None, childrenID = None):
        super().__init__( parentID , childrenID)
        self.finishEvent = threading.Event()
        
    def Start(self):
        global WaitingCommands
        self.finishEvent.clear()
        WaitingCommands.add(self)
        self.finishEvent.wait()
        return self.result
        
    def End(self, result = True):
        global WaitingCommands
        WaitingCommands.remove(self)
        self.result = result
        self.finishEvent.set()
        
    @classmethod
    def EndAll(cls):
        global WaitingCommands
        temp = list(WaitingCommands)
        for cm in temp:
            cm.End(False)
