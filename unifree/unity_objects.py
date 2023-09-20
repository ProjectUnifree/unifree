#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
from __future__ import annotations

import os.path
from typing import Dict, Any, Optional, Union, TypeVar, Type

from unifree.unity_object_type import UnityObjectType


class UBase:
    _properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self._properties = properties

    def property(self, *path) -> Optional[Any]:
        path = list(path)

        current = self._properties
        for path_element in path:
            for path_option in [str(path_element), f"m_{path_element}"]:
                if path_option in current:
                    path_element = path_option
                    break

            if path_element in current:
                current = current[path_element]
            else:
                return None

        return current

    def __getitem__(self, *index):
        if len(index) == 1:
            if isinstance(index[0], str):
                index = [index[0]]  # handles object["prop"]
            else:
                index = list(index[0])  # handles object["prop1", "prop2"]

        return self.property(*index)


class UMeta(UBase):
    _file_path: str

    def __init__(self, file_path: str, properties: Dict[str, Any]) -> None:
        super().__init__(properties)

        format_version = self["fileFormatVersion"]
        if format_version != 2:
            raise AssertionError(f"Only 'fileFormatVersion' = 2 is supported, but got {format_version} please update your project in Unity")

        if not os.path.exists(file_path):
            raise AssertionError(f"Parsing error: meta file path '{file_path}' does not exist")

        if not file_path.endswith(".meta"):
            raise AssertionError(f"File path '{file_path}' is not a meta file")

        self._file_path = file_path[:-5]  # Strip .meta
        if not os.path.exists(self._file_path):
            raise AssertionError(f"Parsing error: target file path '{self._file_path}' does not exist")

        _register_umeta(self)

    def __str__(self) -> str:
        return f"[UMeta {self._file_path}']"

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def meta_file_path(self) -> str:
        return self._file_path + ".meta"

    @property
    def extension(self) -> str:
        _, file_extension = os.path.splitext(os.path.basename(self.file_path))
        return file_extension

    @property
    def guid(self) -> str:
        return self["guid"]

    def is_folder(self) -> bool:
        is_folder = os.path.isdir(self.file_path)
        is_folder_asset = self["folderAsset"]
        if is_folder != is_folder_asset:
            raise AssertionError(f"{self.file_path} is not consistent: is folder = {is_folder}, folderAsset = {is_folder_asset}")

        return is_folder

    def copy_to(self, destination_path: str) -> None:
        if self.is_folder():
            raise NotImplementedError("Copying folders is not supported")

        try:
            import shutil
            shutil.copy2(self._file_path, destination_path)
        except Exception as e:
            print(f"Unable to copy '{self._file_path}' to '{destination_path}': {e}")


class UObject(UBase):
    _file_id: int
    _object_type: UnityObjectType
    _is_stripped: bool
    _umeta: UMeta

    def __init__(
            self,
            file_id: int,
            object_type: UnityObjectType,
            umeta: UMeta,
            is_stripped: bool,
            properties: Dict[str, Any],
    ) -> None:
        super().__init__(properties)

        self._file_id = file_id
        self._object_type = object_type
        self._is_stripped = is_stripped
        self._umeta = umeta

        _register_uobject(self)

    @property
    def umeta(self) -> UMeta:
        return self._umeta

    @property
    def is_stripped(self) -> bool:
        return self._is_stripped

    @property
    def object_type(self) -> UnityObjectType:
        return self._object_type

    @property
    def file_id(self) -> int:
        return self._file_id

    def __str__(self) -> str:
        return f"[{self.object_type.value} {self.file_id}]"


_global_object_registry: Dict[str, UBase] = {}


def uobject_for_file_id(file_id: int) -> Optional[UObject]:
    return _get('o', file_id, UObject)


def umeta_for_guid(guid: str) -> Optional[UMeta]:
    return _get('m', guid, UMeta)


def _register_uobject(uobject: UObject) -> None:
    _register('o', uobject.file_id, uobject)


def _register_umeta(uMeta: UMeta) -> None:
    _register('m', uMeta.guid, uMeta)


def _register(prefix: str, obj_id: Union[int, str], target: UBase) -> None:
    global _global_object_registry
    _global_object_registry[f"{prefix}:{obj_id}"] = target


ResultType = TypeVar('ResultType')


def _get(prefix: str, obj_id: Union[int, str], expected_type: Type[ResultType]) -> Optional[ResultType]:
    global _global_object_registry
    ubase = _global_object_registry[f"{prefix}:{obj_id}"] if f"{prefix}:{obj_id}" in _global_object_registry else None
    if ubase is not None:
        if not isinstance(ubase, expected_type):
            raise AssertionError(f"{ubase} is not {expected_type}")

        return ubase

    return None
