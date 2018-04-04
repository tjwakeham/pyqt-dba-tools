## Qt Database Application Toolset

This project is a set of tools to make the prototyping and development of data-driven Qt5 apps very quick and easy.

The `db` module contains database models and view models which generate local column definitions by querying the
database and allow easy override of various display and interaction properties.

The `views` module contains record list and edit views with an array of commonly used configuration options.

Using a database table with the appropriate columns and a UI form developed in QtDesigner and saved to orders.ui, 
the following code will automatically link all the interface elements and allow list and edit operations on the data.

```python
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
```

![Order](http://fs.tjwakeham.com/order.PNG)