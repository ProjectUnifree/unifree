#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
import unittest

import yaml

from unifree.unity_objects import UBase


class TestUBase(unittest.TestCase):
    def test_str_property(self):
        obj = UBase({"abcd": "b", "c": {"d": "e"}})
        self.assertEqual("b", obj.property("abcd"))
        self.assertEqual("e", obj.property("c", "d"))

        self.assertEqual("b", obj["abcd"])
        self.assertEqual("e", obj["c", "d"])

        self.assertIsNone(obj["f"])

    def test_json_property(self):
        properties = """
        a:
            b: {"c": "d", "e": "f"}
        """

        obj = UBase(yaml.safe_load(properties))
        self.assertEqual({"c": "d", "e": "f"}, obj["a", "b"])


if __name__ == '__main__':
    unittest.main()
