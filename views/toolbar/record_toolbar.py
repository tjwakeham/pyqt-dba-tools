from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolBar


class RecordToolbar(QToolBar):
    """ Toolbar for standard record functionality """

    def __init__(self) -> None:
        super().__init__('Record')

        self.add_record = self.addAction(QIcon(':record/add'), 'Add record')
        self.edit_record = self.addAction(QIcon(':record/edit'), 'Edit record')
        self.delete_record = self.addAction(QIcon(':record/delete'), 'Delete record')

        self.addSeparator()

        self.refresh = self.addAction(QIcon(':record/refresh'), 'Refresh')
