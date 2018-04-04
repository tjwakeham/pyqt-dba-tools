from PyQt5.QtCore import QObject

import logging
import inspect
import functools


def trace(logger, fn):
    """ Logging decorator """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not getattr(fn, 'trace', True):
            return fn(*args, **kwargs)

        logger.debug('{0}({1}, {2})'.format(fn.__name__, str(args), str(kwargs)))
        try:
            ret_val = fn(*args, **kwargs)
        except:
            logger.exception('{0}'.format(fn.__name__), exc_info=True)
            raise
        logger.debug('{0}(..) -> {1}'.format(fn.__name__, str(ret_val)))
        return ret_val
    return wrapper



class Log(object):
    """ Class decorator which logs calls to all instance methods """

    def trace(self):
        self._logger = logger = logging.getLogger(self.__class__.__name__)

        for attr_name in dir(self):
            if attr_name in ['self'] or attr_name.startswith('__'):
                continue

            attr = getattr(self, attr_name)

            # already being traced by super class
            if hasattr(attr, 'traced'):
                continue

            if callable(attr) and hasattr(attr, '__func__') and not inspect.isclass(attr):
                setattr(attr.__func__, 'traced', True)
                setattr(self, attr_name, trace(logger, attr))

