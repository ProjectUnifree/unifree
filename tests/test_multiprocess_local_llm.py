#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
import unittest
from concurrent.futures import ThreadPoolExecutor

from unifree.llms import MultiprocessLocalLLM


class TestMultiprocessLocalLLM(unittest.TestCase):

    def test_translate(self):
        config = {
            "class": "MultiprocessLocalLLM",
            "llm_config": {
                "class": "TrivialLLM",
                "config": {
                    "key": "value"
                }
            },

            "wrapper_config": {
                "num_workers": 5,
                "query_timeout_sec": 1,
            }
        }

        mp_llm = MultiprocessLocalLLM(config)
        mp_llm.initialize()

        count = mp_llm.count_tokens("some text")
        self.assertEqual(9, count)

        self.assertTrue(mp_llm.fits_in_one_prompt(123))

        def map_func(query_ix_loc):
            nonlocal mp_llm
            return query_ix_loc, mp_llm.query(f"QUERY {query_ix_loc}")

        inputs = range(200)
        with ThreadPoolExecutor(max_workers=4) as e:
            results = e.map(map_func, inputs)

        results_count = 0
        for query_ix, response in results:
            self.assertEqual(f"QUERY {query_ix}", response)
            results_count += 1

        self.assertEqual(200, results_count)
