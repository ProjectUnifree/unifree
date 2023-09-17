#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
from typing import Dict, TypeVar, Callable

import openai
import tiktoken

import unifree
from unifree import log


class ChatGptMixin:
    CODE_DELIMITER = "```"
    MAX_TOKENS = 3500  # Chat GPT limit is 4097, reduce by 25% to leave some room for mis-counting
    TOKEN_SPECIAL_CHARACTERS = [" ", "\n", "\t"]

    """
    This mixin add a capability to query chat GPT for a completion
    """
    config: Dict

    ResultType = TypeVar('ResultType')

    def translate_code_in_chatgpt(self, code: str, prompt_type: str, system: str, extractor_fn: Callable[[str], ResultType]) -> ResultType:
        user = self.create_code_prompt(prompt_type, code)
        response = self.query_chatgpt(user, system)
        return extractor_fn(response)

    def query_chatgpt(self, user: str, system: str) -> str:
        openai.api_key = self.config['chatgpt']['key']

        if unifree.log_level == 'debug':
            short_user_query = user[:50].replace("\n", " ")
            token_count = self.count_tokens(user)
            log.debug(f"Requesting running a query for {token_count:,} tokens ('{short_user_query}...')...")

        try:
            completion = openai.ChatCompletion.create(
                model=self.config['chatgpt']["model"],
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}, ]
            )

            if len(completion.choices) < 1 or len(completion.choices[0].message.content) < 1:
                raise RuntimeError(f"ChatGPT returned malformed response: {completion}")

            response = completion.choices[0].message.content

            log.debug(f"\n==== GPT REQUEST ====\n{user}\n\n==== GPT RESPONSE ====\n{response}\n")

            return response
        except Exception as e:
            raise RuntimeError(f"ChatGPT query failed: {e}")

    def create_code_prompt(self, prompt_type: str, code: str) -> str:
        return self.create_prompt(prompt_type, {"CODE": code})

    def create_prompt(self, prompt_type: str, replacements: Dict[str, str]) -> str:
        text: str = self.config['prompts'][prompt_type]

        if not text:
            raise RuntimeError(f"Prompt '{prompt_type}' is not defined. Please confirm it is set in the destination YAML file under 'prompts'")

        for key, value in replacements.items():
            text = text.replace('${' + key + '}', value)

        return text

    def fits_in_one_translation(self, source_text: str) -> bool:
        token_count = self.count_tokens(source_text)
        return token_count < self.MAX_TOKENS

    def count_tokens(self, source_text: str) -> int:
        encoding = tiktoken.encoding_for_model(self.config['chatgpt']["model"])
        num_tokens = len(encoding.encode(source_text))

        return num_tokens

    @classmethod
    def extract_first_source_code(cls, response: str) -> str:
        result = ''

        starting_ix = response.find(cls.CODE_DELIMITER)
        if starting_ix >= 0:
            starting_ix = response.find("\n", starting_ix)  # Move to the new line
            ending_ix = response.find(cls.CODE_DELIMITER, starting_ix)
            if ending_ix > 0 and starting_ix > 0:
                result = response[starting_ix:ending_ix]

        if len(result) == 0:
            result = response

        return result.rstrip().lstrip()

    @classmethod
    def extract_header_implementation(cls, response: str, header_ext: str = '.h', implementation_ext='.cpp') -> [str, str]:
        """
        This is a hacky attempt to parse ChatGPT response that contain both header an implementation. Sometimes the result
        would be something like:
            Player.h:

            ```cpp
                    ... header code ...
            ```

            Player.cpp:

            ```cpp
                    ... implementation code ...
            ```

        But other times it is:
            // Player.h
                    ... header code ...

            // Player.cpp:
                    ... implementation code ...

        :param response:            Full ChatGPT response
        :param header_ext:          Extension of the expected header file (default '.h')
        :param implementation_ext:  Extension of the implementation file (default '.cpp')

        :return: Best attempt at parsed header/implementation
        """
        header = ''
        is_in_header = False

        implementation = ''
        is_in_implementation = False

        # True in case header and implementation are separated by '// Filename.h' comment
        is_comment_based_delimiter = False

        for line in response.splitlines():
            if line.lstrip().startswith(cls.CODE_DELIMITER):
                if is_comment_based_delimiter:
                    continue

                is_opening_delimiter = not is_in_header and not is_in_implementation
                if is_opening_delimiter:
                    is_header_present = len(header) > 0
                    if is_header_present:
                        is_in_implementation = True
                        is_in_header = False
                    else:
                        is_in_header = True
                        is_in_implementation = False
                else:  # Closing delimiter
                    if is_in_header:
                        is_in_header = False
                    if is_in_implementation:
                        is_in_implementation = False
            elif line.lstrip().startswith("//") and line.rstrip().endswith(header_ext):
                is_in_header = True
                is_in_implementation = False
                is_comment_based_delimiter = True
            elif line.lstrip().startswith("//") and line.rstrip().endswith(implementation_ext):
                is_in_header = False
                is_in_implementation = True
                is_comment_based_delimiter = True
            else:
                if is_in_header:
                    header += line + "\n"
                elif is_in_implementation:
                    implementation += line + "\n"

        # If we couldn't parse the response, just return everything in the header
        if len(header) < 1 and len(implementation) < 1:
            header = response
            implementation = "SEE HEADER FOR FULL RESPONSE"

        return header.rstrip().lstrip(), implementation.rstrip().lstrip()
