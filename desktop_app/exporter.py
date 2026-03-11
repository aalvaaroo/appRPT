from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


def export_csv(rows: list[dict], columns: list[str], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(col, "") for col in columns])


def export_excel(rows: list[dict], columns: list[str], output: Path) -> None:
    from openpyxl import Workbook

    output.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Export"
    ws.append(columns)
    for row in rows:
        ws.append([row.get(col, "") for col in columns])
    wb.save(output)
