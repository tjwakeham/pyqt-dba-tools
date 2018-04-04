from PyQt5.QtSql import QSqlQuery

from ..utils.logging import Log


class SqlCalculation(Log):
    """ Query which returns a single value
        Params -
            query - SQL to execute
            paramaters - list of parameters expected by query"""

    query = ''
    parameters = []

    def __init__(self):
        Log.trace(self)

    def _check_args(self, **kwargs):
        """ Check all required parameters are passed """

        for parameter in self.parameters:
            if parameter not in kwargs:
                return False
        return True

    def calculate(self, **kwargs):
        """ Return calculated value from query using supplied parameters"""

        if not self._check_args(**kwargs):
            raise KeyError('Missing arguments - requires {0}'.format(','.join(self.parameters)))

        sql_query = QSqlQuery(self.query)

        for idx, parameter in enumerate(self.parameters):
            sql_query.bindValue(idx, kwargs[parameter])

        sql_query.next()
        return sql_query.value(0) or 0