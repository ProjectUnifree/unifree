#!/usr/bin/env python3
import unittest

from unifree.llms import HuggingfaceLLM
from unifree.utils import to_default_dict


# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

class TestHuggingfaceLLM(unittest.TestCase):

    def test_translate(self):
        config = to_default_dict({
            "class": "HuggingfaceLLM",
            "config": {
                "checkpoint": "codellama/CodeLlama-7b-hf",
                "max_tokens": 1024,
                "max_new_tokens": 1024,
            },
        })

        llm = HuggingfaceLLM(config)
        llm.initialize()

        response = llm.query("hello?")
        print(f">>> {response}")
