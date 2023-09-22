#!/usr/bin/env python3

# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

import os.path
from abc import ABC
from typing import List, Union, Dict, Optional, Iterable

from tqdm.contrib.concurrent import thread_map

from unifree import log, MigrationStrategy, utils, FileMigrationSpec


class ConcurrentMigrationStrategy(MigrationStrategy, ABC):

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

    def map_concurrently(self, fn, iterables, **tqdm_kwargs) -> Iterable:
        return thread_map(fn, iterables, **tqdm_kwargs)


class CreateMigrations(ConcurrentMigrationStrategy):
    _source_path: str
    _destination_path: str

    _migrations: List[MigrationStrategy]
    _errors: List[str]

    def __init__(
            self,
            source_path: str,
            destination_path: str,
            config: Dict,
    ) -> None:
        super().__init__(config)

        self._source_path = source_path
        self._destination_path = destination_path

        self._migrations = []
        self._errors = []

        if not os.path.exists(source_path) or not os.path.isdir(source_path):
            log.error(f"Invalid source path: {source_path}")
            raise RuntimeError("Source path invalid. Please select a folder with Unity project")

        if not os.path.exists(destination_path):
            os.makedirs(destination_path, exist_ok=True)

        self._initialize_shared_objects()

    def migrations(self) -> List[MigrationStrategy]:
        return self._migrations

    def execute(self) -> None:
        log.info(f"Loading source files from '{self._source_path}'...")

        self._check_if_source_is_unity_project()

        project_files = self._load_source_file_paths()

        log.info(f"Computing migration strategies for {len(project_files):,} files...")
        results = self.map_concurrently(
            self._map_file_path_to_migration,
            project_files,
            max_workers=self.config["concurrency"]["create_strategy_worker"] if self.config["concurrency"]["create_strategy_worker"] else 1,
            unit='path',
            chunksize=1,
        )

        warnings = []
        for result in results:
            if isinstance(result, str):
                warnings.append(result)
            elif result is None:
                pass
            elif isinstance(result, MigrationStrategy):
                self._migrations.append(result)
            else:
                raise RuntimeError(f"Programming error: unknown migration {result}")

        for warning in warnings:
            log.warn(warning)

    def _load_source_file_paths(self) -> List[str]:
        absolute_paths = []

        ignored_locations = self.config["source"]["ignore_locations"]
        ignored_locations = [os.path.join(self._source_path, il) for il in ignored_locations] if ignored_locations else []

        # Walk through the folder and its sub-folders
        for root, _, files in os.walk(self._source_path):
            for file in files:
                should_include = True
                for ignored_location in ignored_locations:
                    if root.startswith(ignored_location):
                        should_include = False
                        break

                if should_include:
                    file_path = os.path.join(root, file)
                    absolute_paths.append(file_path)

        return absolute_paths

    def _map_file_path_to_migration(self, file_path: str) -> Union[MigrationStrategy, str, None]:
        try:
            if os.path.isfile(file_path):
                _, file_extension = os.path.splitext(file_path)
                strategy_name = self.config["strategies"][file_extension]
                if strategy_name:
                    spec = FileMigrationSpec(
                        source_file_path=file_path,
                        source_project_path=self._source_path,
                        destination_project_path=self._destination_path
                    )

                    return self._create_migration_strategy(strategy_name, spec)
            return None
        except Exception as e:
            return f"'{file_path}' failed to create strategy: {e}"

    def _create_migration_strategy(self, strategy_name: str, spec: FileMigrationSpec) -> MigrationStrategy:
        loaded_class = utils.load_class(strategy_name, 'migration_strategies')
        result = loaded_class(spec, self.config)
        if not isinstance(result, MigrationStrategy):
            raise RuntimeError(f"Loaded {strategy_name} is not a migration strategy")

        return result

    def _initialize_shared_objects(self):
        from unifree.source_code_parsers import CSharpCodeParser
        CSharpCodeParser.initialize()

        from unifree.known_translations_db import KnownTranslationsDb
        KnownTranslationsDb.initialize_instance(self.config)

    def _check_if_source_is_unity_project(self):
        files = os.listdir(self._source_path)
        for required_file in ['Assets', 'ProjectSettings']:
            if required_file not in files:
                log.error(f"Unable to find '{required_file}' folder in '{self._source_path}'")
                raise RuntimeError(f"Source is not a valid Unity project")


class ExecuteMigrations(ConcurrentMigrationStrategy):
    _strategies: List[MigrationStrategy]

    def __init__(self, strategies: List[MigrationStrategy], config: Dict) -> None:
        super().__init__(config)

        self._strategies = strategies

    def execute(self) -> None:
        log.info(f"Executing {len(self._strategies):,} migration strategies...")

        results = self.map_concurrently(
            self._execute_strategy, self._strategies,
            max_workers=self.config["concurrency"]["execute_strategy_workers"] if self.config["concurrency"]["execute_strategy_workers"] else 1,
            unit='file',
            chunksize=1,
        )

        warnings = []
        for result in results:
            if isinstance(result, str):
                warnings.append(result)
            elif result is None:
                pass
            else:
                raise RuntimeError(f"Programming error: unknown migration {result}")

        for warning in warnings:
            log.warn(warning)

    def _execute_strategy(self, strategy: MigrationStrategy) -> Optional[str]:
        try:
            strategy.execute()
        except Exception as e:
            return f"Failed to execute {strategy}: {e}"
