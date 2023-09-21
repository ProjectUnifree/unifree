#!/usr/bin/env python3

# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

import importlib
import os
import re
from collections import defaultdict
from typing import Type, Dict, Any

import yaml

from unifree import LLM


def load_config(config_name: str) -> Dict[str, Any]:
    from unifree import log
    import unifree

    config_folder_path = os.path.join(unifree.project_root, "configs")
    config_file_name = os.path.join(config_folder_path, f"{config_name}.yaml")
    if not os.path.exists(config_file_name) or not os.path.isfile(config_file_name):
        supported_destinations = []
        for config_file_name in os.listdir(config_folder_path):
            if config_file_name.endswith(".yaml"):
                supported_destinations.append(config_file_name.replace(".yaml", ""))

        log.error(f"{config_name} is not a supported config. All supported configs: " + ", ".join(supported_destinations))
        raise RuntimeError("Config name not supported")

    with open(config_file_name, 'r') as config_file:
        result = yaml.safe_load(config_file)
        result = to_default_dict(result)

        log.debug(f"Loaded config from '{config_file_name}'")

    return result


def load_class(class_name: str, module: str) -> Type:
    module = importlib.import_module('.' + module, package='unifree')

    # Load the class dynamically
    loaded_class = getattr(module, class_name)
    if not loaded_class:
        raise RuntimeError(f"Class {class_name} not found")

    return loaded_class


def load_llm(config: Dict) -> LLM:
    llm_class = load_class(config["class"], "llms")
    return llm_class(config)


def camel_to_snake(camel_case_str: str) -> str:
    snake_case_str = re.sub(r'([a-z])([A-Z])', r'\1_\2', camel_case_str)
    return snake_case_str.lower()


def snake_to_camel(snake_case_str: str) -> str:
    words = snake_case_str.split('_')
    camel_case_str = words[0] + ''.join(word.capitalize() for word in words[1:])
    return camel_case_str


def to_default_dict(d):
    if isinstance(d, dict):
        return defaultdict(_return_none, {k: to_default_dict(v) for k, v in d.items()})
    elif isinstance(d, list):
        return [to_default_dict(e) for e in d]
    else:
        return d


def _return_none():
    return None
