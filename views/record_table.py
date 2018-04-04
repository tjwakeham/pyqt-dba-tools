import typing
import inspect

from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex, QItemSelection
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QAbstractItemView, QHeaderView
from PyQt5.QtGui import QIcon

from .table import TableView
from .toolbar.record_toolbar import RecordToolbar
from .toolbar.filter_toolbar import FilterToolbar


class RecordTableView(QMainWindow):
    """ Record table view with toolbar for basic actions - main list view
        Params -
            model - Database model
            form_view - view for editing data
            inline_vorm - show table and formview in one window
            focus_form_field - field to focus on creation of new record
            show_record_toolbar - show standard record tools (add/edit/remove/etc)
            show_filter_toolbar - show filtering tools
            fitler_fields - fields to filter by - passed ot filter toolbar
            can_create - enable new button (requires show_record_toolbar=true)
            can_edit - enable edit button (requires show_record_toolbar=true)
            can_delete - enable delete button (requires show_record_toolbar=true)
            read_only_table - denotes whether the table cells can be directly edited (default false)
            read_only_form - set form to read only
            row_select - set table cell select mode to select whole row (default true)
            single_select - select whether more than one row can be active at once
            toolbars - list of additional toolbars
            enable_sorting - allow sorting on columns
            word_wrap - enable word wrapping in cells
            wrap_columns - columns to enable wrapping for
            dbl_click_edit - open form view by double clicking table row (default true)
            window_title - obvious
            window_icon - obvious
        Events -
            after_record_added - fired after a new record is added and committed to the db
            after_record_delted - fired after a record has been removed from the db
    """

    model = None
    form_view = None
    inline_form = False
    focus_form_field = None
    show_record_toolbar = True
    show_filter_toolbar = True
    filter_fields = []
    can_create = True
    can_edit = True
    can_delete = True
    read_only_table = True
    read_only_form = False
    row_select = True
    single_select = True
    toolbars = []
    enable_sorting = False
    word_wrap = False
    wrap_columns = []
    dbl_click_edit = True

    window_title = None
    window_icon = None

    after_record_added = pyqtSignal(QModelIndex)
    after_record_deleted = pyqtSignal()

    def __init__(self, model=None):
        super().__init__()

        self.parent_view = None

        if self.window_title:
            self.setWindowTitle(self.window_title)

        if self.window_icon:
            self.setWindowIcon(QIcon(self.window_icon))

        # allow passing a model class or instances
        if model:
            self.data_model = model
        else:
            if inspect.isclass(self.model):
                self.data_model = self.model()
            else:
                self.data_model = self.model

        # -- SETUP UI
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # -- TABLE VIEW

        self.table_view = TableView(self.data_model)
        self.table_view.selectionModel().selectionChanged.connect(self.select_record)
        layout.addWidget(self.table_view)

        # set table options
        if self.read_only_table:
            self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        if self.row_select:
            self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        if self.single_select:
            self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)

        self.table_view.setSortingEnabled(self.enable_sorting)

        if self.word_wrap:
            self.table_view.setWordWrap(True)
            self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            if not self.wrap_columns:
                self.table_view.resizeColumnsToContents()
            else:
                for column_name in self.wrap_columns:
                    column = getattr(self.table_view, column_name)
                    self.table_view.resizeColumnToContents(column.field.index)

        if self.dbl_click_edit and not self.inline_form:
            self.table_view.doubleClicked.connect(self.edit_record)

        # create inline form
        if self.inline_form:
            self.record_form_view = self.form_view()
            layout.addWidget(self.record_form_view)

        self.setCentralWidget(widget)

        # -- RECORD TOOLBAR
        if self.show_record_toolbar:
            self.record_toolbar = RecordToolbar()
            if self.inline_form:
                self.record_toolbar.edit_record.setDisabled(True)
            self.record_toolbar.add_record.setEnabled(self.can_create)
            self.record_toolbar.edit_record.setEnabled(self.can_edit)
            self.record_toolbar.delete_record.setEnabled(self.can_delete)
            self.addToolBar(Qt.TopToolBarArea, self.record_toolbar)

            self.record_toolbar.add_record.triggered.connect(lambda checked: self.new_record())
            self.record_toolbar.edit_record.triggered.connect(lambda checked: self.edit_record())
            # delete buttom
            self.record_toolbar.refresh.triggered.connect(lambda: self.table_view.data_model.select())

        # -- FILTER TOOLBAR
        if self.show_filter_toolbar and self.filter_fields:
            self.filter_toolbar = FilterToolbar(self.filter_fields, self.table_view.proxy_model)
            self.addToolBar(Qt.TopToolBarArea, self.filter_toolbar)

        self.addToolBarBreak(Qt.TopToolBarArea)

        # -- TOOLBARS
        for area, toolbar in self.toolbars:
            self.addToolBar(area, toolbar(self.table_view.proxy_model))

    def set_parent_view(self, view):
        """ Used by subviews to designate their parent - not usually called by user """
        self.parent_view = view
        if self.inline_form:
            self.record_form_view.set_parent_view(view)

    def new_record(self) -> None:
        """ Create new record and set editing mode"""
        model = self.table_view.data_model
        record, model_index = model.add_record()

        if not self.inline_form:
            self.record_form_view = self.form_view(model=self.data_model)
            self.record_form_view.set_parent_view(self.parent_view)

        self.record_form_view.new_record = True
        self.record_form_view.set_record_index(model_index)
        self.record_form_view.show()

        self.after_record_added.emit(model_index)

        if self.focus_form_field:
            field = getattr(self.record_form_view, self.focus_form_field, None)
            if not field:
                return
            field.setFocus(Qt.TabFocusReason)

    def edit_record(self, *args: typing.List[typing.Any], **kwargs: typing.Mapping) -> None:
        """ Edit currently active record """
        model_index = self.table_view.get_selected_index()
        self.record_form_view = self.form_view(model=self.table_view.data_model)
        self.record_form_view.set_record_index(model_index)
        self.record_form_view.show()

        if self.read_only_form:
            self.record_form_view.set_read_only(True)

    def delete_selected_records(self, *args: typing.List[typing.Any], **kwargs: typing.Mapping) -> None:
        """ Delete all selected records """
        model_indexes = self.table_view.get_selected_indexes()
        for index in model_indexes:
            self.data_model.removeRow(index.row())
        self.data_model.select()

    # row change event handler to update inline form
    def select_record(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        if self.inline_form:
            self.record_form_view.new_record = False
            model_index = self.table_view.get_selected_index()
            self.record_form_view.set_record_index(model_index)