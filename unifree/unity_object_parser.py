#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
import fileinput
from typing import Dict, List

import yaml

from unifree import log
from unifree.unity_object_type import UnityObjectType
from unifree.unity_objects import UObject, UMeta


class UObjectParser:
    _config: Dict

    def __init__(self, config: Dict) -> None:
        self._config = config

    @property
    def config(self) -> Dict:
        return self._config

    def parse_uobjects(self, file_path: str) -> List[UObject]:
        umeta_file_path = file_path + ".meta"
        umeta = self.parse_umeta(umeta_file_path)

        # Unity objects are not simple YAML files: they have essential headers
        # that we need to parse out manually
        current_object_header = ''
        current_object_body = ''
        result = []

        def save_current_uobject_to_result():
            nonlocal umeta
            nonlocal current_object_header
            nonlocal current_object_body
            nonlocal result

            # First, parse the header
            header_parts = current_object_header.split(" ")
            assert len(header_parts) > 1
            assert header_parts[0] == "---"
            assert header_parts[1].startswith('!u!')
            assert header_parts[2].startswith('&')

            object_type_int = int(header_parts[1][3:])
            object_type = UnityObjectType.from_enum_int(object_type_int)

            file_id = int(header_parts[2][1:])
            is_stripped = current_object_header.endswith("stripped")

            properties_with_top_level = yaml.safe_load(current_object_body)

            if object_type is not None and object_type.value in properties_with_top_level:
                properties = properties_with_top_level[object_type.value]

                result.append(UObject(
                    file_id=file_id,
                    object_type=object_type,
                    umeta=umeta,
                    is_stripped=is_stripped,
                    properties=properties,
                ))
            else:
                log.warn(f"File '{umeta.file_path}' contains an object with header '{current_object_header}', but object type {object_type} is not valid")

        for line in fileinput.input(files=[file_path], encoding="utf-8"):
            if line.startswith("--- "):
                # If we have an old object
                if len(current_object_header) > 0:
                    save_current_uobject_to_result()

                current_object_header = line.rstrip()
            elif line.startswith("%"):
                line = line.rstrip()
                if line != "%YAML 1.1" and line != "%TAG !u! tag:unity3d.com,2011:":
                    raise ValueError(f"Unable to parse unknown file '{file_path}': header '{line}' is not recognized")
            else:
                current_object_body += line

        # Potentially save the last object in file
        if len(current_object_header) > 0:
            save_current_uobject_to_result()

        return result

    def parse_umeta(self, file_path: str) -> UMeta:
        if not file_path.endswith(".meta"):
            raise ValueError(f"Not a unity meta file: '{file_path}'")

        # Unity .meta files are simple YAML dictionaries
        with open(file_path, 'r') as properties_file:
            properties = yaml.safe_load(properties_file)

        return UMeta(file_path, properties)
