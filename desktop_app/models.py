from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


Formatter = Callable[[Any], str]


@dataclass(frozen=True)
class ColumnSpec:
    key: str
    title: str
    formatter: Formatter | None = None


def format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


class DictTableModel(QAbstractTableModel):
    def __init__(self, columns: list[ColumnSpec], rows: list[dict] | None = None, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._rows = rows or []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role not in (Qt.DisplayRole, Qt.ToolTipRole):
            return None
        row = self._rows[index.row()]
        col = self._columns[index.column()]
        value = row.get(col.key)
        if col.formatter:
            return col.formatter(value)
        return format_value(value)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._columns[section].title
        return section + 1

    def set_rows(self, rows: list[dict]):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_data(self, row: int) -> dict | None:
        if row < 0 or row >= len(self._rows):
            return None
        return self._rows[row]

    @property
    def columns(self) -> list[ColumnSpec]:
        return self._columns
