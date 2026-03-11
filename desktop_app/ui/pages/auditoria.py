from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.services.query.auditoria import (
    get_import_run,
    list_import_errors,
    list_import_runs,
    list_inferred_links,
)
from desktop_app.db import session_scope
from desktop_app.models import ColumnSpec, DictTableModel


class AuditoriaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Importación:"))
        self._runs_combo = QComboBox()
        self._runs_combo.currentIndexChanged.connect(self.refresh)
        top.addWidget(self._runs_combo)
        top.addStretch()
        layout.addLayout(top)

        self._summary_box = QGroupBox("Resumen")
        self._summary_layout = QFormLayout(self._summary_box)
        self._summary_labels = {
            "estado": QLabel("—"),
            "inicio": QLabel("—"),
            "fin": QLabel("—"),
            "archivos": QLabel("—"),
            "filas": QLabel("—"),
            "errores": QLabel("—"),
        }
        self._summary_layout.addRow("Estado:", self._summary_labels["estado"])
        self._summary_layout.addRow("Inicio:", self._summary_labels["inicio"])
        self._summary_layout.addRow("Fin:", self._summary_labels["fin"])
        self._summary_layout.addRow("Archivos:", self._summary_labels["archivos"])
        self._summary_layout.addRow("Filas:", self._summary_labels["filas"])
        self._summary_layout.addRow("Errores:", self._summary_labels["errores"])

        self._notes_box = QGroupBox("Notas")
        self._notes_layout = QVBoxLayout(self._notes_box)
        self._notes_label = QLabel("—")
        self._notes_label.setWordWrap(True)
        self._notes_layout.addWidget(self._notes_label)

        layout.addWidget(self._summary_box)
        layout.addWidget(self._notes_box)

        self._errors_model = DictTableModel(
            [
                ColumnSpec("error_type", "Tipo"),
                ColumnSpec("source_file", "Archivo"),
                ColumnSpec("source_row", "Fila"),
                ColumnSpec("error_message", "Mensaje"),
            ]
        )
        self._errors_table = QTableView()
        self._errors_table.setModel(self._errors_model)
        self._errors_table.horizontalHeader().setStretchLastSection(True)
        errors_box = QGroupBox("Errores recientes")
        errors_layout = QVBoxLayout(errors_box)
        errors_layout.addWidget(self._errors_table)

        self._links_model = DictTableModel(
            [
                ColumnSpec("from_table", "Origen"),
                ColumnSpec("from_column", "Columna origen"),
                ColumnSpec("to_table", "Destino"),
                ColumnSpec("to_column", "Columna destino"),
                ColumnSpec("coverage", "Cobertura"),
            ]
        )
        self._links_table = QTableView()
        self._links_table.setModel(self._links_model)
        self._links_table.horizontalHeader().setStretchLastSection(True)
        links_box = QGroupBox("Relaciones inferidas")
        links_layout = QVBoxLayout(links_box)
        links_layout.addWidget(self._links_table)

        layout.addWidget(errors_box, 1)
        layout.addWidget(links_box, 1)

        self.refresh_runs()

    def refresh_runs(self):
        with session_scope() as session:
            runs = list_import_runs(session, limit=50)

        self._runs_combo.blockSignals(True)
        self._runs_combo.clear()
        if not runs:
            self._runs_combo.addItem("No hay importaciones", None)
        else:
            for run in runs:
                self._runs_combo.addItem(f"{run.id} - {run.started_at} - {run.status}", run.id)
        self._runs_combo.blockSignals(False)
        self.refresh()

    def refresh(self):
        run_id = self._runs_combo.currentData()
        if run_id is None:
            for label in self._summary_labels.values():
                label.setText("—")
            self._notes_label.setText("—")
            self._errors_model.set_rows([])
            self._links_model.set_rows([])
            return
        with session_scope() as session:
            run = get_import_run(session, run_id)
            errors = list_import_errors(session, run_id)
            links = list_inferred_links(session, run_id)

        if not run:
            return

        self._summary_labels["estado"].setText(str(run.status))
        self._summary_labels["inicio"].setText(str(run.started_at))
        self._summary_labels["fin"].setText(str(run.finished_at or "—"))
        self._summary_labels["archivos"].setText(str(run.file_count or 0))
        self._summary_labels["filas"].setText(str(run.row_count or 0))
        self._summary_labels["errores"].setText(str(run.error_count or 0))

        notes = run.notes or "—"
        author = run.created_by or "sistema"
        self._notes_label.setText(f"{notes}\n\nCreado por {author}.")

        self._errors_model.set_rows(
            [
                {
                    "error_type": e.error_type,
                    "source_file": e.source_file,
                    "source_row": e.source_row,
                    "error_message": e.error_message,
                }
                for e in errors
            ]
        )
        self._links_model.set_rows(
            [
                {
                    "from_table": l.from_table,
                    "from_column": l.from_column,
                    "to_table": l.to_table,
                    "to_column": l.to_column,
                    "coverage": l.coverage,
                }
                for l in links
            ]
        )
