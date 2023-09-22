#!/usr/bin/env python3
from typing import Optional, List, Dict

from unifree import LLM, QueryHistoryItem, log


# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)


class HuggingfaceLLM(LLM):
    """
    This is a model that represents Huggingface 'AutoModelForCausalLM' transformer model.

      llm:
        class: HuggingfaceLLM
        config:
          checkpoint: TheBloke/CodeLlama-34B-Instruct-GGUF
          context_length: 4096
          model_type: llama
          gpu_layers: 50

    """
    _model: Optional[any]

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

        self._model = None

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        prompt = ''
        if system:
            prompt += "> user: Remember these rules: \n" + system + "\n\n"
            prompt += "> assistant: Certainly, I will remember and follow these rules. \n\n"

        if history:
            history_str = [f"> {h.role}: {h.content}" for h in history]
            history_str = "\n\n".join(history_str)

            prompt += history_str + "\n\n"

        prompt += "> user: " + user + "\n\n"
        prompt += "> assistant: "

        log.debug(f"\n==== LLM REQUEST ====\n{prompt}\n")

        response = self._model(prompt)

        log.debug(f"\n==== LLM RESPONSE ====\n{response}\n")

        return response

    def initialize(self) -> None:
        from ctransformers import AutoModelForCausalLM

        llm_config = self.config["config"]
        checkpoint = llm_config["checkpoint"]

        self._model = AutoModelForCausalLM.from_pretrained(
            checkpoint,
            model_type=llm_config["model_type"],
            gpu_layers=llm_config["gpu_layers"],
            context_length=llm_config["context_length"],
        )

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return token_count < self.config["config"]["context_length"]

    def count_tokens(self, source_text: str) -> int:
        return len(self._model.tokenize(source_text))
