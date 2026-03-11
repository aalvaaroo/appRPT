from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.query.organizacion import get_organizacion
from desktop_app.db import session_scope
from desktop_app.models import ColumnSpec, DictTableModel


class OrganizacionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Ayuntamiento:"))
        self._ay_combo = QComboBox()
        top.addWidget(self._ay_combo)
        btn = QPushButton("Aplicar")
        btn.clicked.connect(self.refresh)
        top.addWidget(btn)
        clear_btn = QPushButton("Limpiar")
        clear_btn.clicked.connect(self._clear)
        top.addWidget(clear_btn)
        top.addStretch()
        layout.addLayout(top)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, 1)

        self._tables: dict[str, DictTableModel] = {}
        self._init_tabs()
        self.refresh()

    def _init_tabs(self):
        columns = [
            ColumnSpec("code", "Código"),
            ColumnSpec("label", "Descripción"),
            ColumnSpec("total", "Total expedientes"),
        ]
        for key, label in [
            ("areas", "Áreas"),
            ("servicios", "Servicios"),
            ("secciones", "Secciones"),
            ("negociados", "Negociados"),
            ("departamentos", "Departamentos"),
            ("unidades", "Unidades"),
            ("centros", "Centros"),
        ]:
            model = DictTableModel(columns)
            view = QTableView()
            view.setModel(model)
            view.horizontalHeader().setStretchLastSection(True)
            self._tabs.addTab(view, label)
            self._tables[key] = model

    def _clear(self):
        self._ay_combo.setCurrentIndex(0)
        self.refresh()

    def refresh(self):
        with session_scope() as session:
            data = get_organizacion(session, ayuntamiento=None)
            if self._ay_combo.count() == 0:
                self._ay_combo.addItem("Todos", None)
                for ay in data.get("ayuntamientos", []):
                    self._ay_combo.addItem(f"{ay[1]}", ay[0])

        ay_value = self._ay_combo.currentData()
        with session_scope() as session:
            data = get_organizacion(session, ayuntamiento=ay_value)

        for key, model in self._tables.items():
            model.set_rows(data.get(key, []))
