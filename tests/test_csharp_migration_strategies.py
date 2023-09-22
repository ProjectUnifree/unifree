#!/usr/bin/env python3
# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)
import os
import re
import unittest
from typing import Dict, TypeVar, Optional, List, Any

import unifree
from unifree import LLM, QueryHistoryItem
from unifree.csharp_migration_strategies import CSharpCompilationUnitMigrationStrategy, CSharpCompilationUnitMigrationWithLLM, CSharpCompilationUnitToSingleFileWithLLM
from unifree.llms import TrivialLLM
from unifree.utils import to_default_dict


class CSharpCompilationUnitMigrationWithLLMProxy(CSharpCompilationUnitMigrationWithLLM):
    def execute(self) -> None:
        pass

    def load_llm(self) -> unifree.LLM:
        return TrivialLLM(self.config)


class TestCSharpCompilationUnitMigrationWithLLM(unittest.TestCase):
    def test_create_code_prompt(self):
        strategy = CSharpCompilationUnitMigrationWithLLMProxy(unifree.FileMigrationSpec('', '', ''), to_default_dict({
            "prompts": {
                "test": "This is a ${CODE}"
            },
            "llm": {
                "class": "TrivialLLM"
            }
        }))

        self.assertTrue("This is a test with 01010", strategy.create_code_prompt('test', "01010"))

    def test_create_prompt(self):
        strategy = CSharpCompilationUnitMigrationWithLLMProxy(unifree.FileMigrationSpec('', '', ''), to_default_dict({
            "prompts": {
                "test": "This is a ${TEST} with ${MACRO}"
            },
            "llm": {
                "class": "TrivialLLM"
            }
        }))

        self.assertTrue("This is a test with ${MACRO}", strategy.create_prompt('test', {"TEST": "test"}))
        self.assertTrue("This is a test with 111", strategy.create_prompt('test', {"TEST": "test", "MACRO": "111"}))

    def test_create_prompt_missing(self):
        strategy = CSharpCompilationUnitMigrationWithLLMProxy(unifree.FileMigrationSpec('', '', ''), to_default_dict({
            "prompts": {
                "test": "This is a ${TEST} with ${MACRO}"
            },
            "llm": {
                "class": "TrivialLLM"
            }

        }))

        try:
            strategy.create_prompt('missing', {})
            self.fail("Exception should have been thrown")
        except RuntimeError:
            pass  # expected


class CSharpCompilationUnitMigrationStrategyProxy(CSharpCompilationUnitMigrationStrategy):
    def execute(self) -> None:
        pass


class TestCSharpCompilationUnitMigrationStrategy(unittest.TestCase):
    config: Dict

    def test_source_text(self):
        for source_file_name in ['MalformedShortClass.cs', 'ShortClassWithNamespace.cs']:
            strategy = CSharpCompilationUnitMigrationStrategyProxy(_load_file_migration_spec(source_file_name), self.config)
            source_text = _load_source_file(source_file_name)

            self.assertEqual(_normalize_definition(source_text), _normalize_definition(strategy.source_text), f"Source: {source_file_name}")

    def test_method_definitions(self):
        reference_methods = [
            """
                public void setRevenue(double amount, string currency)
                {
                    this.revenue = amount;
                    this.currency = currency;
                }
            """,
            """            
                public void setAdImpressionsCount(int adImpressionsCount)
                {
                    this.adImpressionsCount = adImpressionsCount;
                }
            """,
            """            
                public void setAdRevenueNetwork(string adRevenueNetwork)
                {
                    this.adRevenueNetwork = adRevenueNetwork;
                }
            """]
        norm_reference_methods = [_normalize_definition(r) for r in reference_methods]

        strategy = CSharpCompilationUnitMigrationStrategyProxy(_load_file_migration_spec('ShortClassNoNamespace.cs'), self.config)
        method_definitions = strategy.method_declarations

        for method_definition in method_definitions:
            norm_method_definition = _normalize_definition(method_definition)
            self.assertTrue(norm_method_definition in norm_reference_methods, f"Missing {method_definition}")

    def test_method_definitions_from_malformed(self):
        reference_methods = [
            """
                public void CloseBracketMissing(string key, string value)
                {
                    partnerList.Add(key);
                    partnerList.Add(value);
            """,
        ]
        norm_reference_methods = [_normalize_definition(r) for r in reference_methods]

        strategy = CSharpCompilationUnitMigrationStrategyProxy(_load_file_migration_spec('MalformedShortClass.cs'), self.config)
        method_definitions = strategy.method_declarations

        for method_definition in method_definitions:
            norm_method_definition = _normalize_definition(method_definition)
            self.assertTrue(norm_method_definition in norm_reference_methods, f"Missing {method_definition}")

    def test_create_destination_file_path(self):
        strategy = CSharpCompilationUnitMigrationStrategyProxy(unifree.FileMigrationSpec(
            source_file_path="/Test/Folder/source/Assets/sub/SomeFile.cs",
            source_project_path="/Test/Folder/source/",
            destination_project_path="/Test/Folder/destination",

        ), self.config)
        self.assertEqual("/Test/Folder/destination/Assets/sub/SomeFile.gd", strategy.create_destination_file_path('.gd'))

        strategy._config = to_default_dict({
            "target": {
                "convert_filename_to_camelcase": True
            }
        })
        self.assertEqual("/Test/Folder/destination/Assets/sub/SomeFile.gd", strategy.create_destination_file_path('.gd'))

        strategy._config = to_default_dict({
            "target": {
                "convert_filename_to_snake_case": True
            }
        })
        self.assertEqual("/Test/Folder/destination/Assets/sub/some_file.gd", strategy.create_destination_file_path('.gd'))

        strategy._config = to_default_dict({
            "target": {
                "lower_folder_names": True
            }
        })
        self.assertEqual("/Test/Folder/destination/assets/sub/SomeFile.gd", strategy.create_destination_file_path('.gd'))

    def test_class_definition(self):
        class_definitions = {
            'ShortClassNoNamespace.cs': """
                using System;
                using System.Collections.Generic;
                
                public class AdjustAdRevenue 
                {
                    internal string source;
                    internal double? revenue;
                    internal string currency;
                    internal int? adImpressionsCount;
                    internal string adRevenueNetwork;
                    internal string adRevenueUnit;
                    internal string adRevenuePlacement;
                    internal List<string> partnerList;
                    internal List<string> callbackList;
                public AdjustAdRevenue(string source)
                    {
                        this.source = source;
                // #if UNITY_EDITOR
                        this.callbackList = []
                // #endif
                
                    } // #region Revenue // #endregion 
                }
            """,
            'ShortClassWithNamespace.cs': """
                        using System;
                        using System.Collections.Generic;

                        namespace com.adjust.sdk
                        {
                            public class AdjustAdRevenue
                            {
                                internal string source;
                                internal double? revenue;
                                internal string currency;
                                internal int? adImpressionsCount;
                                internal string adRevenueNetwork;
                                internal string adRevenueUnit;
                                internal string adRevenuePlacement;
                                internal List<string> partnerList;
                                internal List<string> callbackList;

                                public AdjustAdRevenue(string source)
                                {
                                    this.source = source;
                                }
                            }
                        }
            """
        }
        norm_class_definitions = {n: _normalize_definition(d) for n, d in class_definitions.items()}

        for source_file, norm_class_definition in norm_class_definitions.items():
            strategy = CSharpCompilationUnitMigrationStrategyProxy(_load_file_migration_spec(source_file), self.config)
            class_definition = strategy.everything_except_method_declarations

            self.assertEqual(norm_class_definition, _normalize_definition(class_definition), f"Source: {source_file}")

    @classmethod
    def setUpClass(cls) -> None:
        _setup_test_config(cls)


class CSharpCompilationUnitToSingleFileWithLLMProxy(CSharpCompilationUnitToSingleFileWithLLM):
    saved_content: str
    saved_path: str

    batch_count: int = 0

    ResultType = TypeVar('ResultType')

    def save_content(self, content: str, target_file_path: str):
        self.saved_content = content
        self.saved_path = target_file_path

    def load_llm(self) -> LLM:
        class LocalLLM(LLM):
            _parent: Any

            def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
                self._parent.batch_count += 1
                return f"TRANSLATED {user} {self._parent.batch_count}"

            def fits_in_one_prompt(self, token_count: int) -> bool:
                return token_count < 1_000

            def count_tokens(self, source_text: str) -> int:
                return len(source_text)

            def initialize(self) -> None:
                pass

        local_llm = LocalLLM(self.config)
        local_llm._parent = self

        return local_llm


class TestCSharpCompilationUnitToSingleFileWithLLM(unittest.TestCase):
    config: Dict

    def test_execute_small_file(self):
        strategy = CSharpCompilationUnitToSingleFileWithLLMProxy(_load_file_migration_spec('ShortClassNoNamespace.cs'), self.config)
        strategy.execute()

        self.assertEqual("TRANSLATED full 1", strategy.saved_content)
        self.assertEqual("na/resources/ShortClassNoNamespace.gd", strategy.saved_path)

    def test_execute_large_file(self):
        expected_class = "TRANSLATED class_only 1"

        for ix in range(2, 45):
            expected_class += f"\nTRANSLATED methods_only {ix}\n"

        strategy = CSharpCompilationUnitToSingleFileWithLLMProxy(_load_file_migration_spec('LongClassWithNamespace.cs'), self.config)
        strategy.execute()

        self.assertEqual(_normalize_definition(expected_class), _normalize_definition(strategy.saved_content))
        self.assertEqual("na/resources/LongClassWithNamespace.gd", strategy.saved_path)

    @classmethod
    def setUpClass(cls) -> None:
        _setup_test_config(cls)


def _load_file_migration_spec(source_file_name: str) -> unifree.FileMigrationSpec:
    dir_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_path, 'resources', source_file_name)

    if not os.path.exists(file_path):
        raise RuntimeError(f"'{source_file_name}' not found")

    return unifree.FileMigrationSpec(
        source_file_path=file_path,
        source_project_path=dir_path,
        destination_project_path="na"
    )


def _load_source_file(source_file_name: str) -> str:
    file_path = _load_file_migration_spec(source_file_name)

    with open(file_path.source_file_path, 'r') as source_file:
        return source_file.read()


def _normalize_definition(s: str) -> str:
    return re.sub(r'\s+', ' ', s).lstrip().rstrip()


def _setup_test_config(target) -> None:
    target.config = to_default_dict({
        "source": {
            "csharp": {
                "convert_macros_to_comments": True
            }
        },
        "target": {
            "convert_tabs_to_spaces": True,
            "extension": ".gd"
        },
        "prompts": {
            "system": "System Prompt",
            "full": "full",
            "class_only": "class_only",
            "methods_only": "methods_only",
        },
        "llm": {
            "class": "TrivialLLM"
        }
    })


if __name__ == '__main__':
    unittest.main()
