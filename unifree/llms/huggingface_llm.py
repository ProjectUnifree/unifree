#!/usr/bin/env python3
from typing import Optional, List, Dict

import ctransformers
from ctransformers import AutoModelForCausalLM

from unifree import LLM, QueryHistoryItem, log


# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)


class HuggingfaceLLM(LLM):
    """
    This is a model that represents Huggingface 'AutoModelForCausalLM' transformer model.

      llm_config:
        class: HuggingfaceLLM
        config:
          checkpoint: TheBloke/CodeLlama-34B-Instruct-GGUF
          max_tokens: 1024
          model_type: llama
          gpu_layers: 50
    """
    _model: Optional[ctransformers.LLM]

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

        self._model = None

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        prompt = ''
        if system:
            prompt += system + "\n\n"

        if history:
            history_str = [f"> {h.role}: {h.content}" for h in history]
            history_str = "\n\n".join(history_str)

            prompt += history_str + "\n\n"

        prompt += user
        response = self._model(prompt)

        log.debug(f"\n==== LLM REQUEST ====\n{prompt}\n\n==== LLM RESPONSE ====\n{response}\n")

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
        return len(self._model.tokenize(source_text))
