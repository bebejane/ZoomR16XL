from inspect import getframeinfo, stack
import ntpath
import logging
import os

CWD = os.path.dirname(os.path.realpath(__file__))
NAME = os.path.basename(CWD)
FILE = os.path.basename(CWD) + '.log'
LOG_FILE  = CWD + '/' + FILE

def log(msg):
    caller = getframeinfo(stack()[1][0])
    logger.debug(ntpath.basename(caller.filename) + ' (' +  str(caller.lineno) + '): ' + str(msg))

def initLog():
    logger = logging.getLogger(NAME);
    if not logger.handlers:
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        fhan = logging.FileHandler(LOG_FILE)
        fhan.setLevel(logging.DEBUG)
        logger.addHandler(fhan)
        formatter = logging.Formatter('%(message)s')
        fhan.setFormatter(formatter)
    return logger

logger = initLog()
