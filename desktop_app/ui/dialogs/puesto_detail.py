from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QVBoxLayout,
)

from app.services.query.puestos import get_puesto_detail
from desktop_app.db import session_scope


class PuestoDetailDialog(QDialog):
    def __init__(self, cod_descripcion: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Puesto {cod_descripcion}")
        self.resize(800, 650)

        with session_scope() as session:
            detail = get_puesto_detail(session, cod_descripcion)

        layout = QVBoxLayout(self)

        if not detail:
            layout.addWidget(QLabel("No se encontró el puesto."))
            return

        desc = detail.get("descripcion") or {}

        box = QGroupBox("Descripción")
        form = QFormLayout(box)
        form.addRow("Título:", QLabel(str(desc.get("titulo") or "—")))
        form.addRow("Escala:", QLabel(str(desc.get("escala") or "—")))
        form.addRow("Subescala:", QLabel(str(desc.get("subescala") or "—")))
        form.addRow("Grupo:", QLabel(str(desc.get("grupo") or "—")))
        form.addRow("Categoría:", QLabel(str(desc.get("categoria") or "—")))
        form.addRow("Misión:", QLabel(str(desc.get("mision_puesto") or "—")))
        form.addRow("Funciones:", QLabel(str(desc.get("funciones_generales") or "—")))
        layout.addWidget(box)

        layout.addWidget(self._group_list("Funciones asociadas", [f.get("descrip") for f in detail.get("funciones", [])]))
        layout.addWidget(self._group_list("Misiones asociadas", [m.get("descrip") for m in detail.get("misiones", [])]))

        exp_items = [f"Expediente {e.get('cod_exp')}" for e in detail.get("expedientes", [])]
        layout.addWidget(self._group_list("Expedientes relacionados", exp_items))

    def _group_list(self, title: str, items: list[str]) -> QGroupBox:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        if items:
            widget = QListWidget()
            for item in items:
                widget.addItem(item)
            layout.addWidget(widget)
        else:
            layout.addWidget(QLabel("Sin datos."))
        return box
