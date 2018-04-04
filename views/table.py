import typing

from PyQt5.QtCore import QModelIndex, QObject
from PyQt5.QtWidgets import QTableView

from ..db import proxy, model


class TableColumn(QObject):
    """ Abstraction of database column to make it easier to perform column operations -
        not instantiated by user
    """

    def __init__(self, field: model.DatabaseField, table: QTableView) -> None:
        super().__init__()

        self.field = field
        self.table = table

    def show(self) -> None:
        """ Show column """
        self.table.setColumnHidden(self.field.index, False)

    def hide(self) -> None:
        """ Hide column """
        self.table.setColumnHidden(self.field.index, True)

    def visible(self, visible: bool) -> None:
        """ Set column visibility """
        self.table.setColumnHidden(self.field.index, visible)

    def visual_index(self) -> int:
        """ Get visual index of column """
        return self.table.horizontalHeader().visualIndex(self.field.index)

    def move_to(self, index: int) -> None:
        """ Move column to visual index supplied"""
        visual_index = self.table.horizontalHeader().visualIndex(self.field.index)
        self.table.horizontalHeader().moveSection(visual_index, index)

    def swap(self, other: 'TableColumn') -> None:
        """ Swap index of this column with supplied column """
        self.table.horizontalHeader().swapSections(self.field.index, other.field.index)

    def set_width(self, width: int) -> None:
        """" Set column width"""
        self.table.setColumnWidth(self.field.index, width)


class TableView(QTableView):
    """ Basic bound table view with proxy mapping to and from selection"""

    def __init__(self, model: model.DatabaseModel) -> None:
        super().__init__()

        # setup models
        self.data_model = model
        self.proxy_model = proxy.CustomSortFilterProxyModel()
        self.proxy_model.setSourceModel(model)

        self.setModel(self.proxy_model)

        self.columns = []  # type: typing.List[TableColumn]
        for field in self.data_model.fields:
            column = TableColumn(field, self)
            self.columns.append(column)
            setattr(self, field.name, column)

    def get_selected_rows(self) -> typing.List[QModelIndex]:
        """ Get list of selected row indexes mapped to logical data model """
        return [self.proxy_model.mapToSource(index) for index in self.selectionModel().selectedRows(0)]

    def get_selected_indexes(self) -> typing.List[QModelIndex]:
        """ Get list of selected cell indexes mapped to logical data model """
        indexes = self.selectedIndexes()
        return [self.proxy_model.mapToSource(index) for index in indexes]

    def get_selected_index(self) -> QModelIndex:
        """ Get primary selected cell index mapped to logical data model """
        indexes = self.selectedIndexes()
        return self.proxy_model.mapToSource(indexes[0]) if indexes else None

    def get_selected_records(self) -> None:
        """ Get list of selected records """
        indexes = self.get_selected_indexes()
        records = []
        for index in indexes:
            record = self.data_model.record(index.row())
            if record not in records:
                records.append(record)
        return records

    def stretch_last_column(self, stretch: bool) -> None:
        """ Stretch last column to fill available space """
        self.horizontalHeader().setStretchLastSection(stretch)

    def set_column_order(self, columns: typing.List[str]):
        """ Order columns as per index list supplied """
        for index, column in enumerate(self.columns):
            try:
                column_index = columns.index(column.field.name)
            except ValueError:
                continue
            self.columns[column_index].move_to(index)

