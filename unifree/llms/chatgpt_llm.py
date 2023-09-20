#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
from typing import Dict, Optional, List

import openai
import tiktoken

from unifree import LLM, log, QueryHistoryItem


class ChatGptLLM(LLM):
    """
    This class adds a capability to query chat GPT for a completion
    """
    _llm_config: Dict
    _config: Dict

    def __init__(self, config: Dict) -> None:
        super().__init__()

        self._config = config
        self._llm_config = config["llm"]["config"]

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        openai.api_key = self._config['openai_key']

        if log.is_debug():
            short_user_query = user[:50].replace("\n", " ")
            token_count = self.count_tokens(user)
            log.debug(f"Requesting running a query for {token_count:,} tokens ('{short_user_query}...')...")

        try:
            messages = []

            if system:
                messages.append({
                    "role": "system",
                    "content": system
                })

            if history:
                for history_item in history:
                    messages.append({
                        "role": history_item.role,
                        "content": history_item.content
                    })

            messages.append({
                "role": "user",
                "content": user
            })

            completion = openai.ChatCompletion.create(
                model=self._llm_config["model"],
                messages=messages
            )

            if len(completion.choices) < 1 or len(completion.choices[0].message.content) < 1:
                raise RuntimeError(f"ChatGPT returned malformed response: {completion}")

            response = completion.choices[0].message.content

            log.debug(f"\n==== GPT REQUEST ====\n{user}\n\n==== GPT RESPONSE ====\n{response}\n")

            return response
        except Exception as e:
            raise RuntimeError(f"ChatGPT query failed: {e}")

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return token_count < self._llm_config["max_tokens"]

    def count_tokens(self, source_text: str) -> int:
        encoding = tiktoken.encoding_for_model(self._llm_config["model"])
        num_tokens = len(encoding.encode(source_text))

        return num_tokens
