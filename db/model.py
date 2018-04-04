import typing


from PyQt5.QtCore import Qt, QModelIndex, QObject
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtSql import QSqlRecord, QSqlQuery, QSqlRelationalTableModel, QSqlRelation

from ..exceptions import ImproperlyConfigured


class DatabaseField(QObject):
    """ Database field interface """

    def __init__(self, name: str, index: int):
        super().__init__()

        self.name = name
        self.header = ' '.join([part.title() for part in name.split('_')])
        self.header_icon = None
        self.index = index
        self.validation = None
        self.icon = None
        self.auto_populate = None

    def display(self, value, record: QSqlRecord) -> str:
        """ Return the text to be displayed for the given record"""
        return value

    def text_colour(self, value, record: QSqlRecord) -> QColor:
        """ Return the text colour to be displayed for the given record"""
        return None

    def background_colour(self, value, record: QSqlRecord) -> QColor:
        """ Return the cell colour to be displayed for the given record"""
        return None

    def decoration(self, value, record: QSqlRecord) -> QIcon:
        """ Return the icon to be displayed for the given record"""
        return self.icon

    def flags(self, value, record: QSqlRecord) -> int:
        """ Return the flags that determine interaction capabilities"""
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable


class BooleanDatabaseField(DatabaseField):
    """ Database field that shows boolean fields as an icon representing true/false"""

    def __init__(self, parent: DatabaseField, true_icon: str=':record/tick', false_icon: str=':record/cross') -> None:
        super().__init__(parent.name, parent.index)

        self.tick = QIcon(true_icon)
        self.cross = QIcon(false_icon)

    def display(self, value, record: QSqlRecord) -> str:
        # display no text
        return None

    def decoration(self, value, record: QSqlRecord) -> QIcon:
        return self.tick if value else self.cross


class DatabaseModel(QSqlRelationalTableModel):
    """ Database model which sets up field/columns automatically for easy override of data methods
            Params -
                table - required - db table name
                auto_populate_id - whether to generate an autonumber from the supplied id_sequence_name
                id_field_name - primary key field of table
                id_sequence_name - db sequence used to generate autonumber ids
                vertical_header - show vertical header
                vertical_header_field - optionally set field to show in vertical header
         """

    table = ''

    auto_populate_id = True  # type: bool
    id_field_name = 'id'  # type: str
    id_sequence_name = ''  # type: str
    vertical_header = False
    vertical_header_field = None

    def __init__(self) -> None:
        super().__init__()

        self.setTable(self.table)

        record = self.record()

        # need sequence name to generate ids
        if self.auto_populate_id:
            if not (self.id_sequence_name and self.id_field_name) :
                raise ImproperlyConfigured('id_sequence_name must be provided if auto_populate_id is set')

        self.fields = [] # type: List[DatabaseField]

        # auto-generate fields for the database table
        for column_idx in range(self.columnCount()):
            field_name = record.fieldName(column_idx)
            field = DatabaseField(field_name, column_idx)
            self.fields.append(field)
            setattr(self, field_name, field)

    # Qt virtual override - returns header data for given cell
    def headerData(self, index: int, orientation: int, role: int=None) -> str:
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.fields[index].header
            elif role == Qt.DecorationRole:
                if self.fields[index].header_icon:
                    return self.fields[index].header_icon

        if self.vertical_header:
            if role == Qt.DisplayRole:
                if self.vertical_header_field:
                    record = self.record(index)
                    value = record.value(self.vertical_header_field)
                else:
                    value = index + 1
                return value

    headerData.trace = False

    # Qt virtual override - returns data for given data role and cell
    def data(self, model_index: QModelIndex, role: int=None):
        if not model_index.isValid():
            return None

        if role not in [Qt.DisplayRole, Qt.ForegroundRole, Qt.BackgroundRole, Qt.DecorationRole]:
            return super().data(model_index, role)

        row = model_index.row()
        record = self.record(row)
        column = model_index.column()
        field = self.fields[column]
        field_value = record.value(field.index)

        if role == Qt.DisplayRole:
            return field.display(field_value, record)

        elif role == Qt.ForegroundRole:
            return field.text_colour(field_value, record)

        elif role == Qt.BackgroundRole:
            return field.background_colour(field_value, record)

        elif role == Qt.DecorationRole:
            return field.decoration(field_value, record)

        else:
            return None

    data.trace = False

    # Qt virtual override
    def flags(self, model_index: QModelIndex) -> int:
        row = model_index.row()
        record = super().record(row)
        column = model_index.column()
        field = self.fields[column]
        field_value = record.value(field.index)

        return field.flags(field_value, record)

    flags.trace = False

    def get_auto_populated_id(self):
        """ Query the db for an id """

        query = QSqlQuery("SELECT nextval('{0}')".format(self.id_sequence_name))
        query.next()
        return query.value(0)

    def add_record(self, **field_values):
        """ Create record, autofilling id if option is enabled """

        row_count = self.rowCount()
        self.insertRow(row_count)
        model_index = self.index(row_count, 0)
        record = self.record(row_count)

        if self.auto_populate_id:
            id_field_index = self.record().indexOf(self.id_field_name)
            id_model_index = self.index(row_count, id_field_index)
            id_value = self.get_auto_populated_id()
            self.setData(id_model_index, id_value, Qt.EditRole)

        for field in self.fields:
            if not field.auto_populate:
                continue
            field_index = self.index(row_count, field.index)
            field_value = field.auto_populate(record)
            self.setData(field_index, field_value)

        for field, value in field_values.items():
            field_index = self.index(row_count, record.indexOf(field))
            self.setData(field_index, value)

        return self.record(row_count), model_index

    def set_relation(self, column: int, related_table: str, related_id_field:str, related_display_field:str):
        """ Set relation so that Qt can show field values instead of ids """

        self.setRelation(column, QSqlRelation(related_table, related_id_field, related_display_field))

    def set_field(self, field):
        """ Override auto-generated field with user supplied field """

        self.fields[field.index] = field
        setattr(self, field.name, field)
        
    def set_data(self, row, **field_values):
        """ Set data at given row """
        for field, value in field_values.items():
            column = getattr(self, field).index
            index = self.index(row, column)
            self.setData(index, value)


class RelatedDatabaseModel(DatabaseModel):
    """ Extension of DatabaseModel which connects models with foreign keys such that child model can be refreshed when
        parent model index is changed"""

    id_field = 'id'

    def __init__(self):
        super().__init__()
        self.related_id = None

    def set_related_id(self, related_id: typing.Union[str, int]) -> None:
        """ Set id of parent model and refresh model """
        self.related_id = related_id
        if type(related_id) is str:
            related_id = '"{0}"'.format(related_id)
        self.setFilter('{0}={1}'.format(self.id_field, related_id))



