#!/usr/bin/env python3
# Copyright (c) AppLovin. and its affiliates. All rights reserved.
import os

import unifree


def load_resource_migration_spec(source_file_name: str) -> unifree.FileMigrationSpec:
    dir_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_path, 'resources', source_file_name)

    if not os.path.exists(file_path):
        raise RuntimeError(f"'{source_file_name}' not found")

    return unifree.FileMigrationSpec(
        source_file_path=file_path,
        source_project_path=dir_path,
        destination_project_path="na"
    )


def load_resource_file(resource_file_name: str) -> str:
    file_path = load_resource_migration_spec(resource_file_name)

    with open(file_path.source_file_path, 'r') as source_file:
        return source_file.read()
