#!/usr/bin/env python3
from typing import Optional, List, Dict

from ctransformers import AutoModelForCausalLM, AutoTokenizer

from unifree import LLM, QueryHistoryItem, log


# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)


class HuggingfaceLLM(LLM):
    _model: Optional[AutoTokenizer]
    _tokenizer: Optional[AutoModelForCausalLM]

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

        self._model = None
        self._tokenizer = None

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        # TODO FORMULATE PROPER PROMPT WITH ALL OF THE INPUTS ABOVE
        prompt = user
        response = self._model(prompt)

        log.debug(f"\n==== GPT REQUEST ====\n{user}\n\n==== GPT RESPONSE ====\n{response}\n")

        return response

    def initialize(self) -> None:
        checkpoint = self.config["config"]["checkpoint"]

        self._model = AutoModelForCausalLM.from_pretrained(
            checkpoint,
            model_type=self.config["config"]["model_type"],
            gpu_layers=self.config["config"]["gpu_layers"],
        )

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return token_count < self.config["config"]["max_tokens"]

    def count_tokens(self, source_text: str) -> int:
        raise NotImplementedError("TODO IMPLEMENT")
