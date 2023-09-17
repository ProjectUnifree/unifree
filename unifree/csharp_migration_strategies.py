#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
import os
from abc import ABC
from typing import Dict, Optional

import tree_sitter

from unifree import log, MigrationStrategy, FileMigrationSpec, utils
from unifree.chatgpt import ChatGptMixin
from unifree.source_code_parsers import CSharpCodeParser


class CSharpCompilationUnitMigrationStrategy(MigrationStrategy, ABC):
    """
    Strategy to migrate a compilation unit
    """

    _tree: Optional[tree_sitter.Tree]
    _file_migration_spec: FileMigrationSpec

    def __init__(self, file_migration_spec: FileMigrationSpec, config: Dict) -> None:
        super().__init__(config)
        self._file_migration_spec = file_migration_spec
        self._tree = None

    @property
    def source_file_path(self) -> str:
        return self._file_migration_spec.source_file_path

    @property
    def source_project_path(self) -> str:
        return self._file_migration_spec.source_project_path

    @property
    def destination_project_path(self) -> str:
        return self._file_migration_spec.destination_project_path

    @property
    def tree(self) -> tree_sitter.Tree:
        if self._tree is None:
            self._tree = CSharpCodeParser(self.config).parse(self.source_file_path)

        return self._tree

    @property
    def source_text(self) -> str:
        return self.tree.text.decode('utf-8')

    @property
    def everything_except_method_declarations(self) -> str:
        recurse_into_types = ['compilation_unit', 'namespace_declaration', 'class_declaration', 'declaration_list']
        ignore_types = ['method_declaration']
        result = ''

        def everything_except_method_declarations(node):
            nonlocal recurse_into_types
            nonlocal result

            if node.type in recurse_into_types:
                for child in node.children:
                    everything_except_method_declarations(child)

            elif node.type in ignore_types:
                pass
            elif node.type == "{" or node.type == "}":
                result += f"\n{node.type}\n"
            else:
                text = node.text.decode('utf-8')
                text += "\n" if text.endswith(";") else " "

                result += text

        everything_except_method_declarations(self.tree.root_node)

        return result

    @property
    def method_declarations(self) -> [str]:
        result = []

        def extract_methods(node):
            nonlocal result
            if node.type == "method_declaration":
                result.append(node.text.decode('utf-8'))

            for child in node.children:
                extract_methods(child)

        extract_methods(self.tree.root_node)

        return result

    def create_destination_file_path(self, extension: str) -> str:
        relative_path = os.path.relpath(self.source_file_path, self.source_project_path)
        relative_folder_path = os.path.dirname(relative_path)

        if self.config["target"]["lower_folder_names"]:
            relative_folder_path = relative_folder_path.lower()

        target_folder = os.path.join(self.destination_project_path, relative_folder_path)
        try:
            os.makedirs(target_folder, exist_ok=True)
        except Exception:
            pass  # Ignore

        source_filename = os.path.basename(relative_path)
        file_name, file_extension = os.path.splitext(os.path.basename(source_filename))

        if self.config["target"]["convert_filename_to_camelcase"]:
            file_name = utils.snake_to_camel(file_name)
        elif self.config["target"]["convert_filename_to_snake_case"]:
            file_name = utils.camel_to_snake(file_name)

        return os.path.join(target_folder, file_name + extension)

    def maybe_convert_tabs_and_spaces(self, source: str) -> str:
        result = source

        if self.config["target"]["convert_tabs_to_spaces"]:
            result = self.replace_tabs_with_spaces(result)

        if self.config["target"]["convert_spaces_to_tabs"]:
            result = self.replace_spaces_with_tabs(result)

        return result

    def save_content(self, content: str, target_file_path: str):
        if len(target_file_path) > 0:
            log.debug(f"Saving {len(content):,} bytes to '{target_file_path}'...")

            with open(target_file_path, 'w') as output_file:
                output_file.write(content)

    @staticmethod
    def replace_tabs_with_spaces(s: str) -> str:
        return s.replace("\t", "    ")

    @staticmethod
    def replace_spaces_with_tabs(s: str) -> str:
        return s.replace("    ", "\t")


class CSharpCompilationUnitToSingleFileWithChatGpt(CSharpCompilationUnitMigrationStrategy, ChatGptMixin):
    def __init__(self, file_migration_spec: FileMigrationSpec, destination: Dict) -> None:
        super().__init__(file_migration_spec, destination)

    def execute(self) -> None:
        system = self.config['prompts']['system']

        # Chat GPT is sometimes not very good at handling large input source code. So if a code is
        # beyond a certain threshold, translate each method individually
        if self.fits_in_one_translation(self.source_text):
            response = self.translate_code_in_chatgpt(self.source_text, 'full', system, ChatGptMixin.extract_first_source_code)
        else:
            translated_class_only = self.translate_code_in_chatgpt(self.everything_except_method_declarations, 'class_only', system, ChatGptMixin.extract_first_source_code)

            current_methods = ''
            translated_methods = ''
            for method_declaration in self.method_declarations:
                updated_current_methods = current_methods + "\n\n" + method_declaration

                if self.fits_in_one_translation(updated_current_methods):
                    current_methods = updated_current_methods
                else:
                    translated_methods += "\n\n" + self.translate_code_in_chatgpt(current_methods, 'methods_only', system, ChatGptMixin.extract_first_source_code)
                    current_methods = method_declaration

            if len(current_methods) > 0:
                translated_methods += "\n\n" + self.translate_code_in_chatgpt(current_methods, 'methods_only', system, ChatGptMixin.extract_first_source_code)

            if "${METHODS}" in translated_class_only:
                response = translated_class_only.replace("${METHODS}", translated_methods)
            else:
                response = translated_class_only + translated_methods

        response = self.maybe_convert_tabs_and_spaces(response)

        output_file_name = self.create_destination_file_path(self.config["target"]["extension"])
        self.save_content(content=response, target_file_path=output_file_name)

    def __str__(self) -> str:
        output_file_name = self.create_destination_file_path(self.config["target"]["extension"])
        return f"[Migrate '{self.source_file_path}' to '{output_file_name}']"


class CSharpCompilationUnitToInterfaceImplementationWithChatGpt(CSharpCompilationUnitMigrationStrategy, ChatGptMixin):
    def execute(self) -> None:
        system = self.config['prompts']['system']

        # Chat GPT is sometimes not very good at handling large input source code. So if a code is
        # beyond a certain threshold, translate each method individually
        if self.fits_in_one_translation(self.source_text):
            header, implementation = self.translate_code_in_chatgpt(self.source_text, 'full', system, ChatGptMixin.extract_header_implementation)
        else:
            class_header, class_implementation = self.translate_code_in_chatgpt(self.everything_except_method_declarations, 'class_only', system, ChatGptMixin.extract_header_implementation)

            current_methods = ''
            method_headers, method_implementations = '', ''

            def translate_current_methods_and_append():
                nonlocal current_methods, method_headers, method_implementations
                translated_header, translated_implementation = self.translate_code_in_chatgpt(current_methods, 'methods_only', system, ChatGptMixin.extract_header_implementation)
                method_headers += "\n\n" + translated_header
                method_implementations += "\n\n" + translated_implementation

            for method_declaration in self.method_declarations:
                updated_current_methods = current_methods + "\n\n" + method_declaration

                if self.fits_in_one_translation(updated_current_methods):
                    current_methods = updated_current_methods
                else:
                    translate_current_methods_and_append()
                    current_methods = method_declaration

            if len(current_methods) > 0:
                translate_current_methods_and_append()

            if "${METHODS}" in class_header:
                header = class_header.replace("${METHODS}", method_headers)
            else:
                header = class_header + method_headers

            implementation = class_implementation + "\n\n" + method_implementations

        header = self.maybe_convert_tabs_and_spaces(header)
        implementation = self.maybe_convert_tabs_and_spaces(implementation)

        self.save_content(content=header, target_file_path=self.create_destination_file_path(self.config["target"]["header_extension"]))
        self.save_content(content=implementation, target_file_path=self.create_destination_file_path(self.config["target"]["implementation_extension"]))

    def __str__(self) -> str:
        output_file_name = self.create_destination_file_path(self.config["target"]["header_extension"])
        implementation_ext = self.config["target"]["implementation_extension"]
        return f"[Migrate '{self.source_file_path}' to '{output_file_name}/{implementation_ext}']"
