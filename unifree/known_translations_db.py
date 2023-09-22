#!/usr/bin/env python3

# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

from __future__ import annotations

import os
from typing import Dict, Optional, List, Iterable

import chromadb
import yaml
from attr import dataclass
from sentence_transformers import SentenceTransformer

import unifree
from unifree import log


@dataclass
class KnownTranslation:
    source: str
    target: str

    @classmethod
    def from_dict(cls, input_dict: Dict) -> KnownTranslation:
        return KnownTranslation(
            source=input_dict['source'],
            target=input_dict['target'],
        )


class KnownTranslationsDb:
    _class_instance: Optional[KnownTranslationsDb] = None

    _config: Dict

    _chroma_client: Optional[chromadb.Client]
    _collection: Optional[chromadb.Collection]
    _sentence_transformer: Optional[SentenceTransformer]
    _default_n_results: Optional[int]

    def __init__(self, config: Dict) -> None:
        self._config = config
        self._collection = None
        self._sentence_transformer = None
        self._default_n_results = None

    def fetch_nearest_as_query_history(self, query: str, count: Optional[int] = None) -> List[unifree.QueryHistoryItem]:
        result = []
        known_translations = self.fetch_nearest_known_translations(query, count)
        if len(known_translations) > 0:
            translations_config = self._config["known_translations"]
            assistant_response = translations_config["assistant_response"]
            user_request_template = translations_config["user_request"]

            for known_translation in known_translations:
                user_request = user_request_template \
                    .replace("${SOURCE}", known_translation.source) \
                    .replace("${TARGET}", known_translation.target)

                result.append(unifree.QueryHistoryItem(
                    role="user",
                    content=user_request
                ))
                result.append(unifree.QueryHistoryItem(
                    role="assistant",
                    content=assistant_response
                ))

        return result

    def fetch_nearest_known_translations(self, query: str, count: Optional[int] = None) -> List[KnownTranslation]:
        if self._collection:
            if not count:
                count = self._default_n_results

            results = self._collection.query(
                query_embeddings=[self._sentence_transformer.encode(query).tolist()],
                n_results=count,
            )

            documents = results['documents']
            metadatas = results['metadatas']

            if len(metadatas) > 0 and len(documents) > 0:
                return [KnownTranslation(
                    source=document,
                    target=metadata['target'],

                ) for document, metadata in zip(documents[0], metadatas[0])]

        log.debug("Known translations DB was not initialized, not returning anything")
        return []

    def initialize(self) -> None:
        if self._collection is not None:
            return  # Already initialized

        if self._config["known_translations"]:
            translations_config = self._config["known_translations"]
            target_engine = translations_config["target_engine"]

            self._default_n_results = translations_config["result_count"]

            log.debug("Loading sentence transformer...")
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            self._sentence_transformer = self._create_sentence_transformer(translations_config)

            log.debug("Creating and filling up sentence DB...")
            self._chroma_client = chromadb.Client()
            self._collection = self._chroma_client.create_collection(
                name=f"{target_engine}-known-translations",
                embedding_function=self._sentence_transformer
            )
            self._upsert_translations_from_yaml(target_engine)

    def _create_sentence_transformer(self, translations_config: Dict) -> SentenceTransformer:
        embedding_function_name = translations_config["embedding_function"]

        return SentenceTransformer(embedding_function_name)

    def _upsert_translations_from_yaml(self, target_engine: str) -> None:
        known_translations_file_path = os.path.join(unifree.project_root, "known_translations", f"{target_engine}.yaml")
        if not os.path.exists(known_translations_file_path) or not os.path.isfile(known_translations_file_path):
            log.warn(f"No requested known translations found at '{known_translations_file_path}'")
            return

        with open(known_translations_file_path, 'r') as known_translations_file:
            known_translations = yaml.safe_load(known_translations_file)

        if "translations" in known_translations:
            translations = map(KnownTranslation.from_dict, known_translations['translations'])
            self._upsert_translations(translations)

        else:
            log.warn(f"'{known_translations_file_path}' is malformed: no root node called 'translations' found")

    def _upsert_translations(self, translations: Iterable[KnownTranslation]) -> None:
        documents = []
        metadatas = []
        ids = []

        for translation in translations:
            documents.append(translation.source)
            metadatas.append({
                'target': translation.target,
            })
            ids.append(str(len(ids) + 1))

        embeddings = self._sentence_transformer.encode(documents).tolist()

        self._collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        log.debug(f"Inserted {len(ids):,} known translations")

    @classmethod
    def instance(cls) -> KnownTranslationsDb:
        if not cls.is_instance_initialized():
            raise RuntimeError(f"Known translations DB is not initialized")

        return cls._class_instance

    @classmethod
    def is_instance_initialized(cls) -> bool:
        return cls._class_instance is not None

    @classmethod
    def initialize_instance(cls, config: Dict) -> None:
        cls._class_instance = KnownTranslationsDb(config)
        cls._class_instance.initialize()
