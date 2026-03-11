from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from desktop_app.db import session_scope
from desktop_app.models import ColumnSpec, DictTableModel
from app.services.query.expedientes import list_expedientes


class SearchPage(QWidget):
    def __init__(self, on_open_expediente: Callable[[int], None], parent=None):
        super().__init__(parent)
        self._on_open_expediente = on_open_expediente

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Buscar:"))
        self._input = QLineEdit()
        self._input.setPlaceholderText("Texto libre")
        self._input.returnPressed.connect(self.search)
        top.addWidget(self._input)
        btn = QPushButton("Buscar")
        btn.clicked.connect(self.search)
        top.addWidget(btn)
        layout.addLayout(top)

        self._result_label = QLabel("")
        layout.addWidget(self._result_label)

        columns = [
            ColumnSpec("cod_exp", "Expediente"),
            ColumnSpec("denominacion", "Denominación"),
            ColumnSpec("descripcion", "Descripción"),
            ColumnSpec("ayuntamiento", "Ayuntamiento"),
            ColumnSpec("grupo", "Grupo"),
        ]
        self._model = DictTableModel(columns)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.SingleSelection)
        self._table.doubleClicked.connect(self._open_selected)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table, 1)

    def search(self):
        query = self._input.text().strip()
        filters = {"q": query} if query else {"q": None}
        with session_scope() as session:
            rows, _ = list_expedientes(session, filters=filters, page=1, page_size=50)
        self._model.set_rows(rows)
        if query:
            self._result_label.setText(f'Resultados para "{query}"')
        else:
            self._result_label.setText("Resultados")

    def _open_selected(self):
        index = self._table.currentIndex()
        if not index.isValid():
            return
        row = self._model.row_data(index.row())
        if not row:
            return
        try:
            cod = int(row.get("cod_exp"))
        except (TypeError, ValueError):
            return
        self._on_open_expediente(cod)
