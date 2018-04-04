import typing
import operator

from PyQt5.QtCore import QSortFilterProxyModel, QModelIndex, pyqtSignal
from PyQt5.QtSql import QSqlRecord


class CustomSortFilterProxyModel(QSortFilterProxyModel):
    """ Model proxy for filtering by multiple filter functions """

    # filter changed custom event
    filter_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.filter_string = ''
        self.filter_functions = {}

        self.boolean_filters = {}

    def set_filter_string(self, text: typing.Any):
        """ Basic string filtering """
        self.filter_string = text
        self.filter_changed.emit()
        self.invalidateFilter()

    def add_filter_function(self, name: str, filter_function: typing.Callable[[QSqlRecord, str], bool]) -> None:
        """ Add filter function
            Params -
                name - name of filter
                filter_function - callable that accepts a QSqlRecord and the value of the field and returns a bool
                                  indicating whether the row should be visible"""

        self.filter_functions[name] = filter_function
        self.invalidateFilter()

    def set_boolean_filter(self, name: str, default: bool=True, op=operator.eq) -> None:
        """ Add filter on boolean fields
            Params -
                name - name of filter
                default - default value of filter
                op - operation to check (basically a simplified filter function)"""

        self.boolean_filters[name] = (default, op)
        self.invalidateFilter()

    def clear_filter_functions(self) -> None:
        """ Remove all filter functions """

        self.filter_functions = {}
        self.invalidateFilter()

    def remove_filter_function(self, name: str) -> bool:
        """ Remove filter function
            Params -
                name - name of function to remove
        """

        if name in self.filter_functions:
            del self.filter_functions[name]
            return True
        return False

    def update(self, *args, **kwargs):
        """ Force refresh of filtered data by proxy """
        self.invalidateFilter()

    def _check_string_filters(self, row: int) -> bool:
        """ Check if string filters pass for given row """
        if (type(self.filter_string) is str and not self.filter_string) or self.filter_string is None:
            return True

        model = self.sourceModel()
        tests = [func(model.record(row), self.filter_string) for func in self.filter_functions.values()]
        return False not in tests

    def _check_boolean_filters(self, row: int) -> bool:
        """ Check if boolean filters pass for given row """
        record = self.sourceModel().record(row)
        tests = [op(record.value(field), value) for field, (value, op) in self.boolean_filters.items()]
        return False not in tests

    # QT override
    def filterAcceptsRow(self, row: int, parent: QModelIndex) -> bool:
        return self._check_string_filters(row) and self._check_boolean_filters(row)

    def get_active_indexes(self) -> typing.List[QModelIndex]:
        """ Return all visible model indexes """

        indexes = []
        for row_index in range(self.rowCount()):
            index = self.index(row_index, 0)
            mapped_index = self.mapToSource(index)
            indexes.append(mapped_index)
        return indexes

    def get_visible_records(self) -> typing.List[QSqlRecord]:
        """ Return all visible records """

        records = []
        for row_index in range(self.rowCount()):
            index = self.index(row_index, 0)
            mapped_index = self.mapToSource(index)
            record = self.sourceModel().record(mapped_index)
            records.append(record)
        return records