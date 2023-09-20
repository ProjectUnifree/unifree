#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
import dataclasses
import json
from typing import Optional, List

from unifree import LLM, QueryHistoryItem


class TrivialLLM(LLM):
    """
    This is a trivial implementation of an LLM used for unit tests and an example for other implementations
    """

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        return json.dumps({
            "user": user,
            "system": system if system else '',
            "history": [dataclasses.asdict(h) for h in history] if history else [],
        })

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return True

    def count_tokens(self, source_text: str) -> int:
        return len(source_text)
