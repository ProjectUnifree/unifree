#!/usr/bin/env python3

# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

import argparse
import os.path
import platform
import sys
from typing import Optional

import unifree
from unifree import utils, log


def run_migration(
        config: str,
        source: str,
        destination: str,
        llm_secret_key: Optional[str] = None,
        verbose: bool = False,
):
    if verbose:
        unifree.log_level = 'debug'

    try:
        config = utils.load_config(config)
        config["verbose"] = verbose

        if llm_secret_key and "llm" in config and "config" in config["llm"]:
            config["llm"]["config"]["secret_key"] = llm_secret_key

    except Exception as e:
        log.error(f"Unable to start: {config} is invalid: {e}", exc_info=e)
        return 78 # os.EX_CONFIG

    if not os.path.exists(source):
        log.error(f"Unable to start: source folder does not exist ('{source}')")
        return 78 # os.EX_CONFIG

    if not os.path.isdir(source):
        log.error(f"Unable to start: source folder is not a folder ('{source}')")
        return 78 # os.EX_CONFIG

    if os.path.exists(destination):
        log.info(f"Using existing destination folder '{destination}'")
    else:
        log.info(f"Creating destination folder '{destination}'...")

        try:
            os.makedirs(destination)
        except Exception as e:
            log.error(f"Unable to create destination folder '{destination}': {e}", exc_info=e)
            return 74 # os.EX_IOERR

    from unifree.project_migration_strategies import CreateMigrations, ExecuteMigrations

    try:
        create_migrations = CreateMigrations(source, destination, config)
        create_migrations.execute()

        execute_migrations = ExecuteMigrations(create_migrations.migrations(), config)
        execute_migrations.execute()

        log.info("Migration completed successfully")

        return os.EX_OK
    except Exception as e:
        log.error(f"Unable to migrate: {e}", exc_info=e)
        return 70 # os.EX_SOFTWARE


def migrate():
    system_platform = platform.system()
    args_parser = argparse.ArgumentParser(
        description="Run a migration of a Unity project",
        usage=f"""\npython3 unifree/free.py -c Config_Name -k ChatGPT_Key -s Source_Location  -d Destination_Location [-v]
            \nExample call: python3 unifree/free.py -c godot_with_gds -k sk-5X8...3L2a -s /Users/john/Unity/FlappyBird -s /Users/john/Godot/FlappyBird
        """
    )
    args_parser.add_argument(
        '--config', '-c',
        required=True,
        type=str,
        help=f"Name of the migration configuration. Must match file name in the ./configs folder",
    )
    args_parser.add_argument(
        '--source', '-s',
        required=True,
        type=str,
        help=f"Path to the source Unity project",
    )
    args_parser.add_argument(
        '--destination', '-d',
        required=True,
        type=str,
        help=f"Path to the destination project folder. Migrated files would be stored there",
    )
    args_parser.add_argument(
        '--llm_secret_key', '-k',
        required=False,
        type=str,
        help=f"Secret key for the current LLM (optional)",
    )
    args_parser.add_argument(
        '--verbose', '-v',
        required=False,
        default=False,
        action='store_true',
        help=f"Print verbose information about the migration process")

    try:
        args, _ = args_parser.parse_known_args()
    except SystemExit:
        args_parser.print_usage()
        sys.exit(78) # os.EX_CONFIG

    args = vars(args)

    status_code = run_migration(
        **args
    )
    sys.exit(status_code)


if __name__ == '__main__':
    migrate()
