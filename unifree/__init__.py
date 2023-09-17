#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
from abc import ABC
from dataclasses import dataclass
from typing import Optional, Dict

# =====================
# Overall Configuration
# =====================

log_level: Optional[str] = 'info'
"""Log level to use. Options are 'debug', 'info', 'warn' and 'error'"""

supress_warnings: bool = False
"""If true 'warn'-level messages would be logged into stderr"""


class MigrationStrategy(ABC):
    _config: Dict

    def __init__(self, config: Dict) -> None:
        self._config = config

    @property
    def config(self):
        return self._config

    def execute(self) -> None:
        raise NotImplementedError


class DummyMigrationStrategy(MigrationStrategy):
    def execute(self) -> None:
        pass


@dataclass
class FileMigrationSpec:
    source_file_path: str
    source_project_path: str
    destination_project_path: str

