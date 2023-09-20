#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
from typing import Optional, List, Dict

from unifree import LLM, QueryHistoryItem


class TrivialLLM(LLM):
    """
    This is a trivial implementation of an LLM used for unit tests and an example for other implementations
    """

    def __init__(self, config: Dict) -> None:
        super().__init__()

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        return user

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return True

    def count_tokens(self, source_text: str) -> int:
        return len(source_text)

    def initialize(self) -> None:
        pass
