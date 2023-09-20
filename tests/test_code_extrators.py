#!/usr/bin/env python3
# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

import unittest

from unifree.llms.code_extrators import extract_first_source_code, extract_header_implementation


class TestCodeExtractors(unittest.TestCase):

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
            extracted_code = extract_first_source_code(response)
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
            extracted_header, extracted_implementation = extract_header_implementation(response)
            self.assertEqual(target_header, extracted_header, f"Response: {response}")
            self.assertEqual(target_implementation, extracted_implementation, f"Response: {response}")


if __name__ == '__main__':
    unittest.main()
