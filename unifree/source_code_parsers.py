#!/usr/bin/env python3

# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

import os.path
from typing import Dict

import tree_sitter

import unifree
from unifree import log


class CSharpCodeParser:
    _parser: tree_sitter.Parser
    _config: Dict[str, any]

    def __init__(self, config: Dict) -> None:
        self._config = config
        self.initialize()

        self._parser = tree_sitter.Parser()
        self._parser.set_language(tree_sitter.Language(self._c_sharp_library_path(), "c_sharp"))

    @classmethod
    def initialize(cls) -> None:
        c_sharp_library_path = cls._c_sharp_library_path()
        if not os.path.exists(c_sharp_library_path):
            c_sharp_library_folder_path = os.path.dirname(c_sharp_library_path)
            log.debug(f"C# library not found at '{c_sharp_library_path}', building...")

            tree_sitter_csharp_folder_path = os.path.join(unifree.project_root, 'vendor', 'tree-sitter-c-sharp')
            if not os.path.exists(tree_sitter_csharp_folder_path):
                log.error(f"CSharp implementation of the tree sitter is not found at {tree_sitter_csharp_folder_path}")
                raise RuntimeError(f"CSharp tree sitter not found in {tree_sitter_csharp_folder_path}")

            os.makedirs(c_sharp_library_folder_path, exist_ok=True)
            tree_sitter.Language.build_library(c_sharp_library_path, [tree_sitter_csharp_folder_path])

    def parse(self, file_path: str) -> tree_sitter.Tree:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise RuntimeError(f"File {file_path} does not exist")

        with open(file_path, 'r') as source_file:
            source_str = source_file.read()
            if len(source_str) < 1:
                raise RuntimeError(f"File {file_path} is empty")

            if self._config["source"]["csharp"]["convert_macros_to_comments"]:
                source_str = self._replace_macros_with_comments(source_str)

            source_bytes = bytes(source_str, "utf8")

            try:

                result: tree_sitter.Tree = self._parser.parse(source_bytes)
                if result.root_node:
                    return result
                else:
                    raise RuntimeError(f"Failed to parse '{file_path}': no root node found")

            except Exception as ex:
                raise RuntimeError(f"Failed to parse '{file_path}': threw exception while parsing", ex)

    @classmethod
    def _c_sharp_library_path(cls) -> str:
        c_sharp_library_folder_path = os.path.join(unifree.project_root, 'vendor', 'build', 'libraries')
        return os.path.join(c_sharp_library_folder_path, 'c-sharp.so')

    @classmethod
    def _find_vendor_folder(cls, current_folder_path: str, remaining_depth: int) -> str:
        if remaining_depth <= 0:
            log.error("Unable to locate 'vendor' folder that is necessary for reading the code. Please make sure your project is setup correctly")
            raise RuntimeError(f"Can't locate 'vendor' folder")

        if os.path.isdir(current_folder_path):
            for file_name in os.listdir(current_folder_path):
                if os.path.isdir(os.path.join(current_folder_path, file_name)) and file_name == 'vendor':
                    return current_folder_path

        return cls._find_vendor_folder(os.path.dirname(current_folder_path), remaining_depth - 1)

    def _replace_macros_with_comments(self, source_str : str) -> str:
        result = []
        lines = [line.strip() for line in source_str.split("\n") if line.strip() != '']
        for line in lines:
            if line.startswith("#"):
                result.append("// " + line)
            else:
                result.append(line)

        return "\n".join(result)
