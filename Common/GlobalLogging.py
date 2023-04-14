import sys, os
import logging
import traceback


class LogManager: 
    def __init__(self, name):
        # 로그 생성
        rootPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fileName= os.path.join(rootPath,'Logs.log')
        logger = logging.getLogger(name)
        logger.propagate = False
        # 로그의 출력 기준 설정
        logger.setLevel(logging.DEBUG)

        # log 출력 형식
        formatter_forFile = logging.Formatter('[%(asctime)s][%(thread)s]<%(name)s>(%(levelname)s) %(message)s')
        formatter_forConsole = logging.Formatter('[%(name)s](%(levelname)s) %(message)s')
        
        # log 출력
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter_forConsole)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)

        # log를 파일에 출력
        file_handler = logging.FileHandler(fileName)
        file_handler.setFormatter(formatter_forFile)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        self.logger = logger

