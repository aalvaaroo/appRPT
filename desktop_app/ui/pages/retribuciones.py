from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from app.core.config import settings
from app.services.query.retribuciones import list_retribuciones
from desktop_app.db import session_scope
from desktop_app.exporter import export_csv, export_excel
from desktop_app.models import ColumnSpec, DictTableModel


class RetribucionesPage(QWidget):
    def __init__(self, on_open_expediente: Callable[[int], None], parent=None):
        super().__init__(parent)
        self._on_open_expediente = on_open_expediente
        self._page = 1
        self._page_size = 50
        self._page_info = None

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Retribuciones"))
        top.addStretch()
        self._export_csv_btn = QPushButton("Exportar CSV")
        self._export_csv_btn.clicked.connect(lambda: self._export("csv"))
        self._export_xlsx_btn = QPushButton("Exportar Excel")
        self._export_xlsx_btn.clicked.connect(lambda: self._export("xlsx"))
        top.addWidget(self._export_csv_btn)
        top.addWidget(self._export_xlsx_btn)
        layout.addLayout(top)

        filters_box = QGroupBox("Filtros")
        filters_layout = QGridLayout(filters_box)

        self._source = QComboBox()
        self._source.addItem("Productividad", "productividad")
        self._source.addItem("Mislata", "mislata")

        self._cod_exp = QLineEdit()
        self._ayuntamiento = QLineEdit()
        self._grupo = QLineEdit()
        self._cd = QLineEdit()
        self._cod_ce = QLineEdit()
        self._q = QLineEdit()

        filters_layout.addWidget(QLabel("Fuente"), 0, 0)
        filters_layout.addWidget(self._source, 0, 1)
        filters_layout.addWidget(QLabel("Expediente"), 0, 2)
        filters_layout.addWidget(self._cod_exp, 0, 3)
        filters_layout.addWidget(QLabel("Ayuntamiento"), 0, 4)
        filters_layout.addWidget(self._ayuntamiento, 0, 5)
        filters_layout.addWidget(QLabel("Grupo"), 1, 0)
        filters_layout.addWidget(self._grupo, 1, 1)
        filters_layout.addWidget(QLabel("Nivel/CD"), 1, 2)
        filters_layout.addWidget(self._cd, 1, 3)
        filters_layout.addWidget(QLabel("Código CE"), 1, 4)
        filters_layout.addWidget(self._cod_ce, 1, 5)
        filters_layout.addWidget(QLabel("Texto libre"), 2, 0)
        filters_layout.addWidget(self._q, 2, 1, 1, 5)

        buttons = QHBoxLayout()
        apply_btn = QPushButton("Aplicar filtros")
        apply_btn.clicked.connect(self.apply_filters)
        clear_btn = QPushButton("Limpiar")
        clear_btn.clicked.connect(self.clear_filters)
        buttons.addWidget(apply_btn)
        buttons.addWidget(clear_btn)
        filters_layout.addLayout(buttons, 3, 0, 1, 6)

        layout.addWidget(filters_box)

        columns = [
            ColumnSpec("cod_exp", "Expediente"),
            ColumnSpec("grupo", "Grupo"),
            ColumnSpec("cd", "CD"),
            ColumnSpec("salario_base", "Salario Base"),
            ColumnSpec("c_destino", "CDestino"),
            ColumnSpec("com_esp_imp", "Com. Esp."),
            ColumnSpec("tot_an_act", "Total Anual"),
            ColumnSpec("productividad", "Productividad"),
        ]
        self._model = DictTableModel(columns)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.SingleSelection)
        self._table.doubleClicked.connect(self._open_selected)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table, 1)

        pager = QHBoxLayout()
        self._prev_btn = QPushButton("Anterior")
        self._prev_btn.clicked.connect(self.prev_page)
        self._next_btn = QPushButton("Siguiente")
        self._next_btn.clicked.connect(self.next_page)
        self._page_label = QLabel("Página 1")
        pager.addWidget(self._prev_btn)
        pager.addWidget(self._next_btn)
        pager.addWidget(self._page_label)
        pager.addStretch()
        layout.addLayout(pager)

        self.apply_filters()

    def _collect_filters(self) -> dict:
        filters = {}
        if self._cod_exp.text().strip():
            filters["cod_exp"] = self._maybe_int(self._cod_exp.text().strip())
        if self._ayuntamiento.text().strip():
            filters["ayuntamiento"] = self._maybe_int(self._ayuntamiento.text().strip())
        if self._grupo.text().strip():
            filters["grupo"] = self._grupo.text().strip()
        if self._cd.text().strip():
            filters["cd"] = self._maybe_int(self._cd.text().strip())
        if self._cod_ce.text().strip():
            filters["cod_ce"] = self._cod_ce.text().strip()
        if self._q.text().strip():
            filters["q"] = self._q.text().strip()
        return filters

    def _maybe_int(self, value: str):
        try:
            return int(value)
        except ValueError:
            return value

    def apply_filters(self):
        self._page = 1
        self._load()

    def clear_filters(self):
        self._source.setCurrentIndex(0)
        self._cod_exp.setText("")
        self._ayuntamiento.setText("")
        self._grupo.setText("")
        self._cd.setText("")
        self._cod_ce.setText("")
        self._q.setText("")
        self.apply_filters()

    def _load(self):
        filters = self._collect_filters()
        source = self._source.currentData()
        with session_scope() as session:
            rows, page = list_retribuciones(
                session,
                source=source,
                filters=filters,
                page=self._page,
                page_size=self._page_size,
            )
        self._page_info = page
        self._model.set_rows(rows)
        self._page_label.setText(f"Página {page.page} de {page.pages}")
        self._prev_btn.setEnabled(page.page > 1)
        self._next_btn.setEnabled(page.page < page.pages)

    def prev_page(self):
        if self._page_info and self._page_info.page > 1:
            self._page -= 1
            self._load()

    def next_page(self):
        if self._page_info and self._page_info.page < self._page_info.pages:
            self._page += 1
            self._load()

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

    def _export(self, fmt: str):
        filters = self._collect_filters()
        source = self._source.currentData()
        limit = settings.export_max_rows
        with session_scope() as session:
            rows, page = list_retribuciones(
                session, source=source, filters=filters, page=1, page_size=limit
            )

        if not rows:
            QMessageBox.information(self, "Exportación", "No hay datos para exportar.")
            return

        if fmt == "csv":
            path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", "retribuciones.csv", "CSV (*.csv)")
            if not path:
                return
            export_csv(rows, [c.key for c in self._model.columns], Path(path))
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", "retribuciones.xlsx", "Excel (*.xlsx)")
            if not path:
                return
            export_excel(rows, [c.key for c in self._model.columns], Path(path))

        if page.total > limit:
            QMessageBox.warning(
                self,
                "Exportación",
                f"Se exportaron solo los primeros {limit} registros de {page.total}.",
            )
        else:
            QMessageBox.information(self, "Exportación", "Exportación completada.")
