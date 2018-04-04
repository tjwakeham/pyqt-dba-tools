import inspect

from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QModelIndex, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QDataWidgetMapper, QVBoxLayout, QMessageBox
from PyQt5.QtSql import QSqlRecord

from ..exceptions import ImproperlyConfigured


class RecordFormView(QMainWindow):
    """ Record form view - main view for editing individual records
        Params -
            ui_file - path to designer file
            data_model - database model
            subviews - subviews to insert into this view
                       there must be a QWidget placeholder named [subview_name]_placeholder to insert the subview into
            window_title - obvious
            window_icon - obvious
        Events -
            pre_save - fired before saving the record to database
            post_save - fired after saving the record to database
        """

    ui_file = ''  # type: str
    data_model = None
    subviews = {}

    window_title = None
    window_icon = None

    pre_save = pyqtSignal(QSqlRecord)
    post_save = pyqtSignal()

    def __init__(self, model=None, ui_file: str=None) -> None:
        super().__init__()
        loadUi(ui_file or self.ui_file, self)

        self.row = None
        self.record = None

        self.new_record = False
        self.parent_view = None
        self.sub_views = []

        if self.window_title:
            self.setWindowTitle(self.window_title)

        if self.window_icon:
            self.setWindowIcon(QIcon(self.window_icon))

        # allow passing a model class or instances
        model = model or self.model
        if inspect.isclass(model):
            self.data_model = model()
        else:
            self.data_model = model

        # update subviews on row change
        self.data_mapper = QDataWidgetMapper()
        self.data_mapper.setModel(self.data_model)
        self.data_mapper.currentIndexChanged.connect(self._update_subviews)

        # auto map fields to db columns
        for field in self.data_model.fields:
            if hasattr(self, field.name):
                self.data_mapper.addMapping(getattr(self, field.name), field.index)

        # setup subviews
        for view_name, view_cls in self.subviews.items():
            placeholder_name = '{0}_placeholder'.format(view_name)
            try:
                placeholder = getattr(self, placeholder_name)
            except AttributeError:
                raise ImproperlyConfigured('Unable to find subview placeholder ' + placeholder_name)

            view = view_cls()
            self.sub_views.append(view)
            view.set_parent_view(self)
            layout = placeholder.layout()
            if not layout:
                layout = QVBoxLayout(placeholder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(view)
            setattr(self, view_name, view)

        if hasattr(self, 'setup_ui'):
            self.setup_ui()

    def set_read_only(self, read_only):
        """ Set form as read only """
        for field in self.data_model.fields:
            if hasattr(self, field.name):
                widget = getattr(self, field.name)
                widget.setDisabled(read_only)

    def set_parent_view(self, view):
        """ Used by subviews to designate their parent - not usually called by user """
        self.parent_view = view

    def set_record_index(self, model_index: QModelIndex) -> None:
        """ Set active record by model index """
        if not model_index:
            self.setDisabled(True)
            return

        self.row = model_index.row()
        self.index = model_index
        self.record = self.data_model.record(self.row)
        self.setEnabled(True)
        self.data_mapper.setCurrentModelIndex(model_index)

    def save_record(self) -> bool:
        """ Save active record """
        index = self.data_mapper.currentIndex()
        record = self.data_mapper.model().record(index)
        self.pre_save.emit(record)

        saved = self.data_model.submitAll()
        if not saved:
            QMessageBox.critical(self, 'Save record', 'Unable to save record\n{0}'.format(self.data_model.lastError().text()))
            return False

        self.post_save.emit()
        return True

    # row change event handler
    def _update_subviews(self, index: int):
        record = self.data_model.record(index)
        id = record.value(self.data_model.id_field_name)

        # refresh subviews
        for view_name, view_cls in self.subviews.items():
            view = getattr(self, view_name)
            model = view.data_model
            model.set_related_id(id)
            model.select()
