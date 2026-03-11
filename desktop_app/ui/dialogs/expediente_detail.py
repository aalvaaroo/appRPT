from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.query.expedientes import get_expediente
from app.services.query.expediente_detail import get_expediente_detail
from desktop_app.db import session_scope


class ExpedienteDetailDialog(QDialog):
    def __init__(self, cod_exp: int, on_open_puesto, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Expediente {cod_exp}")
        self.resize(900, 700)

        with session_scope() as session:
            record = get_expediente(session, cod_exp)
            detail = get_expediente_detail(session, cod_exp)

        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        if not record:
            content_layout.addWidget(QLabel("No se encontró el expediente."))
            return

        content_layout.addWidget(self._group_main(record))

        if record.get("dp_cod_descripcion"):
            btn_row = QHBoxLayout()
            btn = QPushButton("Ver ficha de puesto")
            btn.clicked.connect(lambda: on_open_puesto(record["dp_cod_descripcion"]))
            btn_row.addWidget(btn)
            btn_row.addStretch()
            content_layout.addLayout(btn_row)

        content_layout.addWidget(self._group_descripcion(record, detail))
        content_layout.addWidget(self._group_dimension(detail))
        content_layout.addWidget(self._group_list("Funciones genéricas", detail.get("funciones_genericas", [])))
        content_layout.addWidget(self._group_list("Misiones genéricas", detail.get("misiones_genericas", [])))

        misiones = [m.get("descrip") for m in detail.get("misiones_por_puesto", [])]
        content_layout.addWidget(self._group_list("Misiones por puesto (inferidas)", misiones))

        content_layout.addWidget(self._group_retribuciones(detail))
        content_layout.addStretch()

    def _group_main(self, record: dict) -> QGroupBox:
        box = QGroupBox("Datos principales")
        form = QFormLayout(box)
        form.addRow("Denominación:", QLabel(str(record.get("denominacion") or "—")))
        form.addRow("Descripción:", QLabel(str(record.get("descripcion") or "—")))
        form.addRow("Ayuntamiento:", QLabel(f"{record.get('ayuntamiento') or '—'} ({record.get('ay_cod_ayto') or '—'})"))
        form.addRow("Área:", QLabel(f"{record.get('area') or '—'} ({record.get('ar_cod_area') or '—'})"))
        form.addRow("Servicio:", QLabel(f"{record.get('servicio') or '—'} ({record.get('se_cod_serv') or '—'})"))
        form.addRow("Sección:", QLabel(f"{record.get('seccion') or '—'} ({record.get('se_cod_sec') or '—'})"))
        form.addRow("Negociado:", QLabel(f"{record.get('negociado') or '—'} ({record.get('ng_cod_neg') or '—'})"))
        form.addRow("Departamento:", QLabel(f"{record.get('departamento') or '—'} ({record.get('de_cod_dpto') or '—'})"))
        form.addRow("Unidad:", QLabel(f"{record.get('unidad') or '—'} ({record.get('ud_cod_ud') or '—'})"))
        form.addRow("Centro:", QLabel(f"{record.get('centro') or '—'} ({record.get('ce_cod_ctr') or '—'})"))
        form.addRow("Grupo:", QLabel(str(record.get("grupo") or record.get("gr_cod_grup") or "—")))
        form.addRow("Subgrupo:", QLabel(str(record.get("subgrupo") or record.get("sgr_cod_subgrupo") or "—")))
        form.addRow("Nivel/CD:", QLabel(str(record.get("cd") or "—")))
        form.addRow("Tipo puesto:", QLabel(str(record.get("tipo_puesto") or record.get("ti_cod_tipo") or "—")))
        form.addRow("Forma provisión:", QLabel(str(record.get("forma_provision") or record.get("fp_cod_for_pro") or "—")))
        form.addRow("Régimen:", QLabel(str(record.get("regimen_laboral") or record.get("re_cod_reg_lab") or "—")))
        return box

    def _group_descripcion(self, record: dict, detail: dict) -> QGroupBox:
        box = QGroupBox("Descripción del puesto")
        form = QFormLayout(box)
        exp = detail.get("expediente") or {}
        form.addRow("Descripción:", QLabel(str(record.get("descripcion") or "—")))
        form.addRow("Misión específica:", QLabel(str(exp.get("mision_espec") or "—")))
        form.addRow("Funciones específicas:", QLabel(str(exp.get("func_espec") or "—")))
        return box

    def _group_dimension(self, detail: dict) -> QGroupBox:
        box = QGroupBox("Dimensión del puesto")
        form = QFormLayout(box)
        dim = detail.get("dimension") or {}
        form.addRow("Horas/día:", QLabel(str(dim.get("horas_dia") or "—")))
        form.addRow("Horas/semana:", QLabel(str(dim.get("horas_semana") or "—")))
        form.addRow("Días/semana:", QLabel(str(dim.get("dias_semana") or "—")))
        form.addRow("Tipo jornada:", QLabel(str(dim.get("tipo_jornada") or "—")))
        return box

    def _group_list(self, title: str, items: list) -> QGroupBox:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        if items:
            widget = QListWidget()
            for item in items:
                widget.addItem(str(item))
            layout.addWidget(widget)
        else:
            layout.addWidget(QLabel("Sin datos."))
        return box

    def _group_retribuciones(self, detail: dict) -> QGroupBox:
        box = QGroupBox("Retribuciones")
        form = QFormLayout(box)
        prod = detail.get("retribucion_productividad") or []
        mislata = detail.get("retribucion_mislata") or []
        if prod:
            row = prod[0]
            form.addRow("Productividad:", QLabel(str(row.get("productividad") or "—")))
            form.addRow("Total anual:", QLabel(str(row.get("tot_an_act") or "—")))
        elif mislata:
            row = mislata[0]
            form.addRow("Total anual:", QLabel(str(row.get("tot_an_act") or "—")))
        else:
            form.addRow(QLabel("Sin datos de retribución."))
        return box
