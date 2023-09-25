#!/usr/bin/env python3
import sys
# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Optional, List, Dict

from unifree import LLM, QueryHistoryItem, log
from unifree.utils import load_llm


class MultiprocessLocalLLM(LLM):
    """
    This class wraps an LLM implementation and run inference (aka 'query' method) in separate processes on the local box.

    The configuration would look like:

    ```
    llm:
      class: MultiprocessLocalLLM
      llm_config:
          class: <wrapped LLM class>
          config <wrapped LLM config>

        wrapper_config:
          num_workers: 5
          query_timeout_sec: 10
    ```
    """
    _shared_executor: Optional[ProcessPoolExecutor] = None
    _query_timeout_sec: int = 20

    _local_model: Optional[LLM]

    def __init__(self, config: Dict) -> None:
        super().__init__(config)

        self._local_model = None

    def initialize(self) -> None:
        llm_config = self.config["llm_config"]

        self._local_model = load_llm(llm_config)
        self._local_model.initialize()

    def query(self, user: str, system: Optional[str] = None, history: Optional[List[QueryHistoryItem]] = None) -> str:
        self.maybe_initialize_shared_executor(self.config)

        result_future = self._shared_executor.submit(_multi_process_worker_translate, _QueryRequest(
            user=user,
            system=system,
            history=history
        ))
        try:
            result = result_future.result(timeout=self._query_timeout_sec)
            if result.is_success():
                return result.response
            else:
                raise RuntimeError(f"LocalLLM query failed: {result.exception}")
        except Exception as e:
            raise RuntimeError(f"LocalLLM query failed: {e}")

    def fits_in_one_prompt(self, token_count: int) -> bool:
        assert self._local_model is not None
        return self._local_model.fits_in_one_prompt(token_count)

    def count_tokens(self, source_text: str) -> int:
        assert self._local_model is not None
        return self._local_model.count_tokens(source_text)

    @classmethod
    def maybe_initialize_shared_executor(cls, config: Dict):
        if not cls._shared_executor:
            wrapper_config = config["wrapper_config"]
            llm_config = config["llm_config"]
            # cls._shared_executor = ProcessPoolExecutor(
            cls._shared_executor = ProcessPoolExecutor(
                max_workers=wrapper_config["num_workers"],
                initializer=_multi_process_worker_init,
                initargs=(llm_config,)
            )
            cls._query_timeout_sec = wrapper_config["query_timeout_sec"]


@dataclass
class _QueryRequest:
    """
    This class represents a request ot make a query to the LLM.
    """
    user: str
    system: Optional[str] = None
    history: Optional[List[QueryHistoryItem]] = None


@dataclass
class _QueryResult:
    """
    This object represents response to a given query
    """
    response: str
    exception: Optional[Exception] = None

    def is_success(self) -> bool:
        return self.exception is None


_process_local_llm: Optional[LLM] = None


def _multi_process_worker_init(config: Dict):
    global _process_local_llm

    try:
        _process_local_llm = load_llm(config)
        _process_local_llm.initialize()
    except Exception as e:
        log.error(f"Failed to load local LLM model with: {e}", exc_info=e)
        _process_local_llm = None


def _multi_process_worker_translate(query: _QueryRequest) -> _QueryResult:
    global _process_local_llm

    try:
        return _QueryResult(
            response=_process_local_llm.query(
                user=query.user,
                system=query.system,
                history=query.history,
            )
        )
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)

        log.error(f"Failed to query local LLM: {e}")
        return _QueryResult(
            response='',
            exception=e
        )
    except:
        log.error(f"Failed to query local LLM with unknown exception")
        return _QueryResult(
            response='',
            exception=Exception("Unknown exception")
        )
