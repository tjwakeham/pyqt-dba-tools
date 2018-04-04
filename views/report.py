from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtPrintSupport import *


class ReportViewer(QMainWindow):
    """ Simple HTML Report viewer with print and PDF capabilities - requires a report server to generate report
        DEPRECATED - PyQt5 has deprecated QtWebView"""

    def __init__(self, title):
        super().__init__()

        self.setWindowTitle('Report Viewer - ' + title)
        self.setWindowIcon(QIcon(':icon/report.png'))

        self.report = QWebView()
        self.setCentralWidget(self.report)

        self.setWindowIcon(QIcon(':report/report'))

        self.actionToolbar = QToolBar('Actions')
        self.actionToolbar.addAction(QIcon(':report/print'), 'Print Report', self.print)
        self.actionToolbar.addAction(QIcon(':report/pdf'), 'PDF Report', self.pdf)
        self.actionToolbar.addSeparator()
        self.actionToolbar.addAction(QIcon(':record/refresh'), 'Refresh', self.report.reload)
        self.addToolBar(Qt.TopToolBarArea, self.actionToolbar)

        raise DeprecationWarning('Qt5 has deprecated QWebView')

    def set_report_url(self, url):
        """ Set the url of the report to view """
        self.report.setUrl(QUrl(url))

    def print(self):
        """ Print report to selected printer """
        printer = QPrinter()
        dialog = QPrintDialog(printer)
        dialog.setWindowTitle("Print Document")
        if dialog.exec_() != QDialog.Accepted:
            return
        self.report.print_(printer)

    def pdf(self):
        """ Save report to PDF"""
        filename = QFileDialog.getSaveFileName(self, 'Save file', '', 'PDF (*.pdf)')
        if not filename:
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFileName(filename[0])
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOrientation(QPrinter.Portrait)
        printer.setPaperSize(QPrinter.A4)
        printer.setFullPage(True)

        self.report.print_(printer)

        QMessageBox.information(self, 'PDF Export', 'PDF saved to {0}'.format(filename[0]))