#!/usr/bin/env python3
from typing import Optional, List, Dict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

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
        with torch.no_grad():
            pipe = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                max_new_tokens=self.config["config"]["max_new_tokens"],
                do_sample=True,
                temperature=self.config["config"]["temperature"],
                top_p=self.config["config"]["top_p"],
                top_k=self.config["config"]["top_k"],
                repetition_penalty=self.config["config"]["repeat_penalty"],
            )

            # TODO FORMULATE PROPER PROMPT WITH ALL OF THE INPUTS ABOVE
            prompt = user
            result = pipe(prompt)

            if len(result) > 0:
                response = result[0]["generated_text"]

                log.debug(f"\n==== GPT REQUEST ====\n{user}\n\n==== GPT RESPONSE ====\n{response}\n")

                return response
            else:
                raise RuntimeError("Model returned no results")

    def initialize(self) -> None:
        checkpoint = self.config["config"]["checkpoint"]

        self._tokenizer = AutoTokenizer.from_pretrained(checkpoint, use_fast=True)

        self._model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=checkpoint,
            device_map="auto",
            trust_remote_code=False,
            revision="main"
        )
        self._model.eval()

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return token_count < self.config["config"]["max_tokens"]

    def count_tokens(self, source_text: str) -> int:
        assert self._tokenizer is not None
        tokenized = self._tokenizer(source_text)

        return len(tokenized)
