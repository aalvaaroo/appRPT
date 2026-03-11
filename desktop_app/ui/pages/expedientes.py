from __future__ import annotations

from typing import Callable
from pathlib import Path

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
from app.services.query.expedientes import list_expedientes
from app.services.query.lookups import get_filter_options
from desktop_app.db import session_scope
from desktop_app.exporter import export_csv, export_excel
from desktop_app.models import ColumnSpec, DictTableModel


class ExpedientesPage(QWidget):
    def __init__(self, on_open_expediente: Callable[[int], None], parent=None):
        super().__init__(parent)
        self._on_open_expediente = on_open_expediente
        self._page = 1
        self._page_size = 50
        self._page_info = None

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Listado de expedientes"))
        top.addStretch()
        self._export_csv_btn = QPushButton("Exportar CSV")
        self._export_csv_btn.clicked.connect(lambda: self._export("csv"))
        self._export_xlsx_btn = QPushButton("Exportar Excel")
        self._export_xlsx_btn.clicked.connect(lambda: self._export("xlsx"))
        top.addWidget(self._export_csv_btn)
        top.addWidget(self._export_xlsx_btn)
        layout.addLayout(top)

        self._filters_box = QGroupBox("Filtros")
        filters_layout = QGridLayout()

        self._combos: dict[str, QComboBox] = {}
        self._text_q = QLineEdit()
        self._text_q.setPlaceholderText("Buscar...")

        with session_scope() as session:
            options = get_filter_options(session)

        row = 0
        row = self._add_combo(filters_layout, row, "Ayuntamiento", "ayuntamiento", options["ayuntamientos"])
        row = self._add_combo(filters_layout, row, "Área", "area", options["areas"])
        row = self._add_combo(filters_layout, row, "Servicio", "servicio", options["servicios"])
        row = self._add_combo(filters_layout, row, "Sección", "seccion", options["secciones"])
        row = self._add_combo(filters_layout, row, "Negociado", "negociado", options["negociados"])
        row = self._add_combo(filters_layout, row, "Departamento", "departamento", options["departamentos"])
        row = self._add_combo(filters_layout, row, "Unidad", "unidad", options["unidades"])
        row = self._add_combo(filters_layout, row, "Centro", "centro", options["centros"])
        row = self._add_combo(filters_layout, row, "Grupo", "grupo", options["grupos"])
        row = self._add_combo(filters_layout, row, "Subgrupo", "subgrupo", options["subgrupos"])
        row = self._add_combo(filters_layout, row, "Nivel/CD", "nivel_cd", options["cdestinos"])
        row = self._add_combo(filters_layout, row, "Categoría", "categoria", options["categorias"])
        row = self._add_combo(filters_layout, row, "Tipo de puesto", "tipo_puesto", options["tipos_puesto"])
        row = self._add_combo(filters_layout, row, "Forma de provisión", "forma_provision", options["formas_provision"])
        row = self._add_combo(filters_layout, row, "Régimen laboral", "regimen_laboral", options["regimen_laboral"])
        row = self._add_combo(filters_layout, row, "Denominación", "denominacion", options["denominaciones"])

        filters_layout.addWidget(QLabel("Texto libre"), row // 4, (row % 4) * 2)
        filters_layout.addWidget(self._text_q, row // 4, (row % 4) * 2 + 1)

        actions = QHBoxLayout()
        self._apply_btn = QPushButton("Aplicar filtros")
        self._apply_btn.clicked.connect(self.apply_filters)
        self._clear_btn = QPushButton("Limpiar")
        self._clear_btn.clicked.connect(self.clear_filters)
        actions.addWidget(self._apply_btn)
        actions.addWidget(self._clear_btn)

        box_layout = QVBoxLayout(self._filters_box)
        box_layout.addLayout(filters_layout)
        box_layout.addLayout(actions)
        layout.addWidget(self._filters_box)

        columns = [
            ColumnSpec("cod_exp", "Expediente"),
            ColumnSpec("denominacion", "Denominación"),
            ColumnSpec("descripcion", "Descripción"),
            ColumnSpec("ayuntamiento", "Ayuntamiento"),
            ColumnSpec("grupo", "Grupo"),
            ColumnSpec("cd", "CD"),
            ColumnSpec("tipo_puesto", "Tipo"),
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

    def _add_combo(self, layout: QGridLayout, idx: int, label: str, key: str, items: list[dict]) -> int:
        row = idx // 4
        col_idx = (idx % 4) * 2
        layout.addWidget(QLabel(label), row, col_idx)
        combo = QComboBox()
        combo.addItem("Todos", None)
        for item in items:
            combo.addItem(str(item.get("label") or item.get("value")), item.get("value"))
        self._combos[key] = combo
        layout.addWidget(combo, row, col_idx + 1)
        return idx + 1

    def _collect_filters(self) -> dict:
        filters = {}
        for key, combo in self._combos.items():
            value = combo.currentData()
            if value not in (None, ""):
                filters[key] = value
        q = self._text_q.text().strip()
        if q:
            filters["q"] = q
        return filters

    def apply_filters(self):
        self._page = 1
        self._load()

    def clear_filters(self):
        for combo in self._combos.values():
            combo.setCurrentIndex(0)
        self._text_q.setText("")
        self.apply_filters()

    def _load(self):
        filters = self._collect_filters()
        with session_scope() as session:
            rows, page = list_expedientes(session, filters=filters, page=self._page, page_size=self._page_size)
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
        limit = settings.export_max_rows
        with session_scope() as session:
            rows, page = list_expedientes(session, filters=filters, page=1, page_size=limit)

        if not rows:
            QMessageBox.information(self, "Exportación", "No hay datos para exportar.")
            return

        if fmt == "csv":
            path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", "expedientes.csv", "CSV (*.csv)")
            if not path:
                return
            export_csv(rows, [c.key for c in self._model.columns], Path(path))
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", "expedientes.xlsx", "Excel (*.xlsx)")
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
