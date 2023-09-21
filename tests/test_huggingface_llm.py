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
                "checkpoint": "TheBloke/CodeLlama-34B-Instruct-GGUF",
                "max_tokens": 1024,
                "model_type": "llama",
                "gpu_layers": 50,
            },
        })

        llm = HuggingfaceLLM(config)
        llm.initialize()

        response = llm.query("hello?")
        print(f">>> {response}")
