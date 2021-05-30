# general imports
import logging


class CaptScribe:
    def __init__(self, log_info, log_error):
        self.logfile_info = log_info
        self.logfile_error = log_error
        self.loggers = [logging.getLogger("log_info"), logging.getLogger("log_error")]
        self.formatters = [logging.Formatter("%(asctime)s : %(level), %(message)s"), logging.Formatter("%(asctime)s : %(message)s: %(sinfo)")]
        self.handlers = [logging.TimedRotatingFileHandler(self.logfile_info, when='midnight', interval=1), logging.TimedRotatingFileHandler(self.logfile_error, when='midnight', interval=1)]
        for i, handler in enumerate(self.handlers):
            handler.setFormatter(self.formatters[i])
        
        for i, logger in self.loggers:
            logger.addHandler(self.handlers[i])
        
        self.loggers[0].level = logging.INFO
        self.loggers[1].level = logging.ERROR
        
    def critical(self, msg, func=""):
        for logger in self.loggers:
            logger.critical(func.upper() + ": " + msg)

    def error(self, msg, func=""):
        for logger in self.loggers:
            logger.error(func.upper() + ": " + msg)
    
    def warning(self, msg, func=""):
        for logger in self.loggers:
            logger.warning(func.upper() + ": " + msg)
    
    def info(self, msg, func=""):
        for logger in self.loggers:
            logger.info(func.upper() + ": " + msg)
    
    def debug(self, msg, func=""):
        for logger in self.loggers:
            logger.debug(func.upper() + ": " + msg)
