from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from desktop_app.env import load_dotenv


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _check_database() -> str | None:
    try:
        from sqlalchemy import create_engine, text
        from app.core.config import settings
    except Exception as exc:
        return str(exc)

    try:
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        return str(exc)
    return None


def main() -> int:
    base_dir = _get_base_dir()
    load_dotenv(base_dir)

    app = QApplication(sys.argv)

    try:
        db_error = _check_database()
        if db_error:
            QMessageBox.critical(
                None,
                "Error de base de datos",
                "No se pudo conectar con la base de datos.\n"
                "Revisa el valor de DATABASE_URL en el archivo .env.\n\n"
                f"Detalle: {db_error}",
            )
            return 1

        from desktop_app.ui.main_window import MainWindow

        window = MainWindow()
        window.show()
    except Exception as exc:  # pragma: no cover - UI error
        QMessageBox.critical(None, "Error", f"No se pudo iniciar la aplicación.\n\n{exc}")
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
