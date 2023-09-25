#!/usr/bin/env python3
import pathlib
# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List

# =====================
# Overall Configuration
# =====================

log_level: Optional[str] = 'info'
"""Log level to use. Options are 'debug', 'info', 'warn' and 'error'"""

supress_warnings: bool = False
"""If true 'warn'-level messages would be logged into stderr"""

project_root: str = str(pathlib.Path(__file__).parent.parent.resolve())
"""This is the _root_ folder of the project. All resource files (config, known translations, etc.) will be relative to this folder"""


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


@dataclass
class QueryHistoryItem:
    role: str
    content: str


class LLM(ABC):
    _config: Dict

    def __init__(self, config: Dict) -> None:
        self._config = config

    @abstractmethod
    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        """
        Query LLM with the provided input.

        :param user:     The actual query.
        :param system:   "System" query. Some LLMs support instructions that should be respected by the LLM and treated with higher regard
                         then the user query
        :param history:  User conversation history. This could be helpful to convey knowledge about language/system.
        :return: Response from the LLM
        """
        raise NotImplementedError

    def initialize(self) -> None:
        """
        Initialize the LLM
        """
        raise NotImplementedError

    def fits_in_one_prompt(self, token_count: int) -> bool:
        """
        Check if the given token count fits into one prompt
        :param token_count: Token count to check
        :return: True if this token count fits into one prompt
        """
        raise NotImplementedError

    def count_tokens(self, source_text: str) -> int:
        """
        Count number of tokens for the given source text
        :param source_text: Text to count tokens in
        :return: Number of tokens
        """
        raise NotImplementedError

    @property
    def config(self) -> Dict:
        return self._config
