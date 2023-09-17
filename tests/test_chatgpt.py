#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.

import unittest

from unifree.chatgpt import ChatGptMixin
from unifree.utils import to_default_dict


class TestChatGptMixin(unittest.TestCase, ChatGptMixin):

    def test_extract_first_source_code(self):
        target_code = "some code here!"
        responses = [
            f"""
```
{target_code}
```
""",
            f"""
```
{target_code}
```
Some ending comment
""",
            f"""
Some beginning comment
```
{target_code}
```
Some ending comment
""",
            f"""
Some beginning comment
```cpp
{target_code}
```
Some ending comment
""",
            f"""
        Some beginning comment
        ```h
        {target_code}
        ```
        ```cpp
        code we don't care about
        ```
        """,
            f"""
{target_code}
""",
        ]

        for response in responses:
            extracted_code = self.extract_first_source_code(response)
            self.assertEqual(target_code, extracted_code)

    def test_extract_header_implementation(self):
        target_header = "header here!"
        target_implementation = "implementation here!"
        responses = [
            f"""
    ```cpp
    {target_header}
    ```
    ```cpp
    {target_implementation}
    ```
    """,
            f"""
// Header:
    ```
    {target_header}
    ```
// Implementation:
    ```
    {target_implementation}
    ```
    Some ending comment
    """,
            f"""
    // Header.h
    ```
    {target_header}
    ```
    // Implementation.cpp
    ```
    {target_implementation}
    ```
    """,
            f"""
    
    // Header.h
    
    {target_header}
    
    // Implementation.cpp
    
    {target_implementation}
    """,
        ]

        for response in responses:
            extracted_header, extracted_implementation = self.extract_header_implementation(response)
            self.assertEqual(target_header, extracted_header, f"Response: {response}")
            self.assertEqual(target_implementation, extracted_implementation, f"Response: {response}")

    def test_fits_in_one_translation(self):
        self.config = to_default_dict({
            "chatgpt": {
                "model": "gpt-3.5-turbo"
            }
        })

        self.assertTrue(self.fits_in_one_translation("x " * 400))
        self.assertFalse(self.fits_in_one_translation("x " * 5_000))

    def test_create_code_prompt(self):
        self.config = to_default_dict({
            "prompts": {
                "test": "This is a ${CODE}"
            }
        })

        self.assertTrue("This is a test with 01010", self.create_code_prompt('test', "01010"))

    def test_create_prompt(self):
        self.config = to_default_dict({
            "prompts": {
                "test": "This is a ${TEST} with ${MACRO}"
            }
        })

        self.assertTrue("This is a test with ${MACRO}", self.create_prompt('test', {"TEST": "test"}))
        self.assertTrue("This is a test with 111", self.create_prompt('test', {"TEST": "test", "MACRO": "111"}))

    def test_create_prompt_missing(self):
        self.config = to_default_dict({
            "prompts": {
                "test": "This is a ${TEST} with ${MACRO}"
            }
        })

        try:
            self.create_prompt('missing', {})
            self.fail("Exception should have been thrown")
        except RuntimeError:
            pass  # expected


if __name__ == '__main__':
    unittest.main()
