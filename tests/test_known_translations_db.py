#!/usr/bin/env python3
import unittest

from unifree.known_translations_db import KnownTranslationsDb, KnownTranslation
from unifree.utils import to_default_dict


# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)


class KnownTranslationsDbProxy(KnownTranslationsDb):
    def _upsert_translations_from_yaml(self, language: str) -> None:
        # Do not lookup yaml file, instead upsert manually
        self._upsert_translations([
            KnownTranslation(
                source="Hello, world!",
                target="Sentence One",
            ),
            KnownTranslation(
                source="Sator arepo tenet opera rotas",
                target="Sentence Two",
            ),
        ])


class TestKnownTranslationsDb(unittest.TestCase):
    _db: KnownTranslationsDbProxy

    def test_fetch_nearest(self):
        self._db.initialize()

        result = self._db.fetch_nearest_known_translations("Sator arepo", count=1)
        self.assertEqual(1, len(result))
        self.assertEqual("Sator arepo tenet opera rotas", result[0].source)
        self.assertEqual("Sentence Two", result[0].target)

    def test_fetch_nearest_as_query_history(self):
        self._db.initialize()

        result = self._db.fetch_nearest_as_query_history("Hello")
        self.assertEqual(4, len(result))

        self.assertEqual("user", result[0].role)
        self.assertEqual("'Hello, world!' is 'Sentence One'", result[0].content)

        self.assertEqual("assistant", result[1].role)
        self.assertEqual("!OK!", result[1].content)

        self.assertEqual("user", result[2].role)
        self.assertEqual("'Sator arepo tenet opera rotas' is 'Sentence Two'", result[2].content)

        self.assertEqual("assistant", result[3].role)
        self.assertEqual("!OK!", result[3].content)

    @classmethod
    def setUpClass(cls) -> None:
        cls._db = KnownTranslationsDbProxy(to_default_dict({
            "known_translations": {
                "language": "trivial",
                "embedding_function": "all-MiniLM-L6-v2",
                "result_count": 2,
                "assistant_response": "!OK!",
                "user_request": "'${SOURCE}' is '${TARGET}'",
            }
        }))
