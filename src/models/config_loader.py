"""Leitura dos arquivos de configuração (.ini)."""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path


class ConfigLoader:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def load_sqlite_config(self) -> dict:
        parser = ConfigParser()
        parser.read(self.project_root / "config" / "sqlite.ini", encoding="utf-8")
        relative_path = parser.get("sqlite", "db_path")
        full_path = self.project_root / relative_path
        return {
            "db_path": str(full_path),
            "source_file": str(self.project_root / "config" / "sqlite.ini"),
        }

    def load_mongodb_config(self) -> dict:
        parser = ConfigParser()
        parser.read(self.project_root / "config" / "mongodb.ini", encoding="utf-8")
        return {
            "uri": parser.get("mongodb", "uri"),
            "database": parser.get("mongodb", "database"),
            "use_mongomock_on_failure": parser.getboolean("mongodb", "use_mongomock_on_failure"),
            "source_file": str(self.project_root / "config" / "mongodb.ini"),
        }
