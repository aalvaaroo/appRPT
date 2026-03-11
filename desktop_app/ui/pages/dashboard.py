from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop_app.db import session_scope
from app.services.query.dashboard import get_dashboard_summary


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._count_labels = {}
        layout = QVBoxLayout(self)

        summary_frame = QFrame()
        summary_layout = QGridLayout(summary_frame)

        self._count_labels["expedientes"] = self._add_kpi(summary_layout, 0, "Expedientes")
        self._count_labels["ayuntamientos"] = self._add_kpi(summary_layout, 1, "Ayuntamientos")
        self._count_labels["descripciones"] = self._add_kpi(summary_layout, 2, "Descripciones de puesto")
        self._count_labels["denominaciones"] = self._add_kpi(summary_layout, 3, "Denominaciones")

        layout.addWidget(summary_frame)

        self._last_import = QLabel("Sin importaciones.")
        self._errors = QLabel("Sin incidencias.")

        import_box = QGroupBox("Última importación")
        import_layout = QVBoxLayout(import_box)
        import_layout.addWidget(self._last_import)

        errors_box = QGroupBox("Incidencias recientes")
        errors_layout = QVBoxLayout(errors_box)
        errors_layout.addWidget(self._errors)

        layout.addWidget(import_box)
        layout.addWidget(errors_box)

        self._refresh_btn = QPushButton("Refrescar")
        self._refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self._refresh_btn)
        layout.addStretch()

        self.refresh()

    def _add_kpi(self, layout: QGridLayout, col: int, title: str) -> QLabel:
        box = QGroupBox(title)
        box_layout = QVBoxLayout(box)
        value = QLabel("0")
        value.setStyleSheet("font-size: 22px; font-weight: 600;")
        box_layout.addWidget(value)
        layout.addWidget(box, 0, col)
        return value

    def refresh(self):
        with session_scope() as session:
            summary = get_dashboard_summary(session)

        self._count_labels["expedientes"].setText(str(summary.get("total_expedientes", 0)))
        self._count_labels["ayuntamientos"].setText(str(summary.get("total_ayuntamientos", 0)))
        self._count_labels["descripciones"].setText(str(summary.get("total_descripciones", 0)))
        self._count_labels["denominaciones"].setText(str(summary.get("total_denominaciones", 0)))

        last = summary.get("last_import")
        if last:
            self._last_import.setText(
                f"Estado: {last.status}\n"
                f"Inicio: {last.started_at}\n"
                f"Fin: {last.finished_at or '—'}\n"
                f"Archivos: {last.file_count or 0}\n"
                f"Filas: {last.row_count or 0}\n"
                f"Errores: {last.error_count or 0}"
            )
        else:
            self._last_import.setText("No hay importaciones registradas.")

        errors = summary.get("error_summary") or []
        if errors:
            lines = [f"{item['type']}: {item['count']}" for item in errors]
            self._errors.setText("\n".join(lines))
        else:
            self._errors.setText("Sin incidencias registradas.")
