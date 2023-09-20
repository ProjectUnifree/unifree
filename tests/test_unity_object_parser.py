#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
import unittest

from tests.test_utils import load_resource_migration_spec
from unifree.unity_object_parser import UObjectParser
from unifree.unity_object_type import UnityObjectType


class TestUnityObjectParser(unittest.TestCase):
    def test_parse_scene(self):
        scene_spec = load_resource_migration_spec("3DScene.unity")

        parser = UObjectParser({})
        uobjects = parser.parse_uobjects(scene_spec.source_file_path)
        self.assertEqual(12, len(uobjects))

        obj = uobjects[0]

        # Check object type
        self.assertEqual(UnityObjectType.OcclusionCullingSettings, obj.object_type)

        # Check properties
        self.assertEqual(0, obj["m_ObjectHideFlags"])
        self.assertEqual(2, obj["serializedVersion"])
        self.assertEqual(5, obj["m_OcclusionBakeSettings", "smallestOccluder"])
        self.assertEqual(5, obj["OcclusionBakeSettings", "smallestOccluder"])  # Should work without "m_" to ease addressing
        self.assertEqual(0.25, obj["m_OcclusionBakeSettings", "smallestHole"])
        self.assertEqual(100, obj["m_OcclusionBakeSettings", "backfaceThreshold"])
        self.assertEqual(0, obj["m_SceneGUID"])
        self.assertEqual({'fileID': 0}, obj["m_OcclusionCullingData"])

        # Check meta
        self.assertEqual(scene_spec.source_file_path, obj.umeta.file_path)
        self.assertEqual(scene_spec.source_file_path + ".meta", obj.umeta.meta_file_path)
        self.assertEqual("c838e8266293d44a5aaa33c254fdd938", obj.umeta.guid)


if __name__ == '__main__':
    unittest.main()
