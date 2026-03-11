from __future__ import annotations

from PySide6.QtWidgets import (
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QHBoxLayout,
    QWidget,
)

from desktop_app.ui.pages.dashboard import DashboardPage
from desktop_app.ui.pages.search import SearchPage
from desktop_app.ui.pages.expedientes import ExpedientesPage
from desktop_app.ui.pages.retribuciones import RetribucionesPage
from desktop_app.ui.pages.organizacion import OrganizacionPage
from desktop_app.ui.pages.auditoria import AuditoriaPage
from desktop_app.ui.dialogs.expediente_detail import ExpedienteDetailDialog
from desktop_app.ui.dialogs.puesto_detail import PuestoDetailDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Legacy Explorer - Escritorio")
        self.resize(1280, 800)

        container = QWidget()
        layout = QHBoxLayout(container)

        self._nav = QListWidget()
        self._nav.addItem("Inicio")
        self._nav.addItem("Buscar")
        self._nav.addItem("Expedientes")
        self._nav.addItem("Retribuciones")
        self._nav.addItem("Organización")
        self._nav.addItem("Importaciones")
        self._nav.currentRowChanged.connect(self._change_page)

        self._stack = QStackedWidget()
        self._pages = [
            DashboardPage(),
            SearchPage(self.open_expediente_detail),
            ExpedientesPage(self.open_expediente_detail),
            RetribucionesPage(self.open_expediente_detail),
            OrganizacionPage(),
            AuditoriaPage(),
        ]
        for page in self._pages:
            self._stack.addWidget(page)

        layout.addWidget(self._nav, 1)
        layout.addWidget(self._stack, 5)
        self.setCentralWidget(container)

        self._nav.setCurrentRow(0)

    def _change_page(self, index: int):
        if index < 0:
            return
        self._stack.setCurrentIndex(index)

    def open_expediente_detail(self, cod_exp: int):
        dialog = ExpedienteDetailDialog(cod_exp, self.open_puesto_detail, self)
        dialog.exec()

    def open_puesto_detail(self, cod_descripcion: str):
        dialog = PuestoDetailDialog(cod_descripcion, self)
        dialog.exec()
