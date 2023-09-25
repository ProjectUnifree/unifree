#!/usr/bin/env python3
from typing import Optional, List, Dict

from unifree import LLM, QueryHistoryItem, log
from unifree.utils import get_or_create_global_instance


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
            prompt += self._to_user_prompt(f"Remember these rules:\n{system}\n")
            prompt += "\nCertainly, I will remember and follow these rules.\n"

        if history:
            for item in history:
                if item.role == "user":
                    prompt += self._to_user_prompt(f"\n{item.content}\n")
                else:
                    prompt += f"\n{item.content}\n"

        prompt += self._to_user_prompt(f"\n{user}\n")

        log.debug(f"\n==== LLM REQUEST ====\n{prompt}\n")

        response = self._model(prompt)

        log.debug(f"\n==== LLM RESPONSE ====\n{response}\n")

        return response

    def initialize(self) -> None:
        from ctransformers import AutoModelForCausalLM

        llm_config = self.config["config"]
        checkpoint = llm_config["checkpoint"]

        self._model = get_or_create_global_instance(checkpoint, lambda: AutoModelForCausalLM.from_pretrained(
            checkpoint,
            model_type=llm_config["model_type"],
            gpu_layers=llm_config["gpu_layers"],
            context_length=llm_config["context_length"],
        ))

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return token_count < self.config["config"]["context_length"]

    def count_tokens(self, source_text: str) -> int:
        return len(self._model.tokenize(source_text))

    def _to_user_prompt(self, user: str) -> str:
        prompt_template = self.config["config"]["prompt_template"]
        return prompt_template.replace("${PROMPT}", user)
