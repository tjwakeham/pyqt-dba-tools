import sys

from PyQt5.QtSql import QSqlDatabase
from PyQt5.QtWidgets import QApplication

from db.model import DatabaseModel
from views.record_table import RecordTableView
from views.record_form import RecordFormView
from assets import resources

# application and database setup
application = QApplication(sys.argv)
application.setStyle('Fusion')

database = QSqlDatabase.addDatabase('QPSQL')
database.setHostName('localhost')
database.setDatabaseName('*******')
database.setUserName('*******')
database.setPassword('*******')
assert database.open()

from assets import resources
from db.model import DatabaseModel
from views.record_table import RecordTableView
from views.record_form import RecordFormView


# setup database model
class OrderModel(DatabaseModel):
    table = 'orders'
    auto_populate_id = True
    id_field_name = 'id'
    id_sequence_name = 'order_ids'

    def __init__(self):
        super().__init__()
        self.id.header = 'ID'

model = OrderModel()
model.select()


# setup edit view
class FormView(RecordFormView):
    model = model
    ui_file = 'order.ui'


# setup table view
class TableView(RecordTableView):
    model = model
    form_view = FormView

# show main view
table_view = TableView()
table_view.show()

# start Qt event loop
sys.exit(app.exec_())

