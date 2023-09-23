#!/usr/bin/env python3
from typing import Optional, List, Dict

from unifree import LLM, QueryHistoryItem, log


# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

global_model = None


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

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        prompt = """[INST] Write code to solve the following coding problem that obeys the constraints and passes the example test cases. Please wrap your code answer using ```
:
"""
        if system:
            prompt += "> user: Remember these rules: \n" + system + "\n\n"
            prompt += "> assistant: Certainly, I will remember and follow these rules. \n\n"

        if history:
            history_str = [f"> {h.role}: {h.content}" for h in history]
            history_str = "\n\n".join(history_str)

            prompt += history_str + "\n\n"

        prompt += "> user: " + user + "\n\n"
        prompt += "> assistant: "
        prompt += "\n[/INST]"

        log.debug(f"\n==== LLM REQUEST ====\n{prompt}\n")

        global global_model
        response = global_model(prompt)
        print(response)

        log.debug(f"\n==== LLM RESPONSE ====\n{response}\n")

        return response

    def initialize(self) -> None:
        from ctransformers import AutoModelForCausalLM

        global global_model
        if global_model:
            return

        llm_config = self.config["config"]
        checkpoint = llm_config["checkpoint"]

        global_model = AutoModelForCausalLM.from_pretrained(
            checkpoint,
            model_type=llm_config["model_type"],
            gpu_layers=llm_config["gpu_layers"],
            context_length=llm_config["context_length"],
        )

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return token_count < self.config["config"]["context_length"]

    def count_tokens(self, source_text: str) -> int:
        global global_model
        return len(global_model.tokenize(source_text))
