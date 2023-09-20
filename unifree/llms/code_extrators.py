#!/usr/bin/env python3

# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

from typing import Tuple


def extract_first_source_code(response: str, code_delimiter: str = "```") -> str:
    """
    Parse response and find the first occurrence of text separated with `code_delimiter`
    :param response:        Response from the model
    :param code_delimiter:  Delimiter that is used to separate the code. Default is ````
    :return: String with the first occurrence or whole response if no delimiters found
    """
    result = ''

    starting_ix = response.find(code_delimiter)
    if starting_ix >= 0:
        starting_ix = response.find("\n", starting_ix)  # Move to the new line
        ending_ix = response.find(code_delimiter, starting_ix)
        if ending_ix > 0 and starting_ix > 0:
            result = response[starting_ix:ending_ix]

    if len(result) == 0:
        result = response

    return result.rstrip().lstrip()


def extract_header_implementation(response: str, header_ext: str = '.h', implementation_ext='.cpp', code_delimiter: str = "```") -> Tuple[str, str]:
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
    :param code_delimiter:  Delimiter that is used to separate the code. Default is ````

    :return: Best attempt at parsed header/implementation
    """
    header = ''
    is_in_header = False

    implementation = ''
    is_in_implementation = False

    # True in case header and implementation are separated by '// Filename.h' comment
    is_comment_based_delimiter = False

    for line in response.splitlines():
        if line.lstrip().startswith(code_delimiter):
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
