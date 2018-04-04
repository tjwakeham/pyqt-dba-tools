import re
import typing
import functools
import fnmatch
import operator

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtSql import QSqlRecord
from PyQt5.QtWidgets import QToolBar, QLineEdit, QComboBox, QCheckBox

from ...db.proxy import CustomSortFilterProxyModel


class FilterToolbar(QToolBar):
    """ Toolbar which provides filtering functionality to table views
        Params -
            filter_fields - list of fields to enable filtering on, can be string or dict
            model - database filtering proxy model"""

    def __init__(self, filter_fields: typing.List[str], model: CustomSortFilterProxyModel) -> None:
        super().__init__('Filter')

        self.setObjectName('filter-toolbar')

        self.model = model

        # setup ui
        self.filter = QLineEdit()
        self.filter.setMaximumWidth(200)
        self.filter.setPlaceholderText('Filter')
        self.filter.textChanged.connect(lambda text: self.model.set_filter_string(text))
        self.addWidget(self.filter)

        self.filter_field = QComboBox()
        self.filter_field.currentTextChanged.connect(
            lambda text: self.model.add_filter_function('filter', self.filters[text]['callback']))

        self.filters = {}

        # filtering function
        def filter_function(field: str, custom_match: typing.Callable[[QSqlRecord, str], bool]=None) -> typing.Callable[[QSqlRecord, str], bool]:
            def callback(record: QSqlRecord, pattern: typing.Any):
                if custom_match:
                    return custom_match(record, pattern)

                value = record.value(field)
                regex = '.*?{0}.*'.format(pattern)
                match = re.search(pattern, value or '', flags=re.IGNORECASE)
                return match is not None

            return callback

        # setup filters
        for field_definition in filter_fields:
            if type(field_definition) is str:
                caption = field_definition.replace('_', ' ').title()
                self.filters[caption] = {
                    'caption': caption,
                    'field': field_definition,
                    'callback': filter_function(field_definition)
                }
                self.filter_field.addItem(caption)
            else:
                caption = field_definition.get('caption', field_definition['field'].replace('_', ' ').title())
                self.filters[caption] = {
                    'caption': caption,
                    'field': field_definition['field'],
                    'callback': filter_function(field_definition['field'], field_definition.get('callback', None))
                }
                self.filter_field.addItem(caption)

        # load filter for default item
        filter_function = self.filters[self.filter_field.currentText()]['callback']
        self.model.add_filter_function('filter', filter_function)

        self.addWidget(self.filter_field)

        self.clear_filter = self.addAction(QIcon(':filter/clear'), 'Clear filter')
        self.clear_filter.triggered.connect(lambda checked: self.filter.setText(''))


class BooleanFilterToolbar(QToolBar):
    """ Toolbar which provides boolean filtering functionality to table views
        Params -
            fields - list of fields to filter by - str or dict"""

    fields = []

    def __init__(self, model: CustomSortFilterProxyModel) -> None:
        super().__init__()

        self.setObjectName('boolean-filter-toolbar')
        self.model = model

        for field in self.fields:
            if type(field) is str:
                caption = field.replace('_', ' ').title()
                field_name = field
                default = False
                op = operator.eq
            else:
                caption = field.get('caption', field['field'].replace('_', ' ').title())
                field_name = field['field']
                default = field.get('default', False)
                op = field.get('op', operator.eq)

                widget = QCheckBox(caption)
                self.addWidget(widget)
                widget.stateChanged.connect(functools.partial(self._update_filter, field_name, op))
                self.update_filter(field_name, op, default)
                widget.setChecked(default)

    # event listener for checkbox state change
    def _update_filter(self, field: str, op: typing.Callable[[typing.Any, typing.Any], bool], state:bool):
        self.model.set_boolean_filter(field, state, op)


