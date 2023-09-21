#!/usr/bin/env python3

# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

from typing import Dict, Optional, List

import openai
import tiktoken

from unifree import LLM, log, QueryHistoryItem


class ChatGptLLM(LLM):
    """
    This class adds a capability to query chat GPT for a completion.

    The configuration looks like:

    ```
    llm:
      class: ChatGptLLM
      config:
          secret_key: <INSERTED DYNAMICALLY BY free.py>
          model: gpt-4
          max_tokens: 4000
    ```

    """

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

    def initialize(self) -> None:
        pass

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        openai.api_key = self.config["config"]['secret_key']

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
                model=self.config["config"]["model"],
                messages=messages
            )

            if len(completion.choices) < 1 or len(completion.choices[0].message.content) < 1:
                raise RuntimeError(f"ChatGPT returned malformed response: {completion}")

            response = completion.choices[0].message.content

            if log.is_debug():
                messages_str = [f"> {m['role']}: {m['content']}" for m in messages]
                messages_str = "\n\n".join(messages_str)

                log.debug(f"\n==== GPT REQUEST ====\n{messages_str}\n\n==== GPT RESPONSE ====\n{response}\n")

            return response
        except Exception as e:
            raise RuntimeError(f"ChatGPT query failed: {e}")

    def fits_in_one_prompt(self, token_count: int) -> bool:
        return token_count < self.config["config"]["max_tokens"]

    def count_tokens(self, source_text: str) -> int:
        encoding = tiktoken.encoding_for_model(self.config["config"]["model"])
        num_tokens = len(encoding.encode(source_text))

        return num_tokens
