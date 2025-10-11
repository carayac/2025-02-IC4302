import logging
import os
import sys
import time
from contextlib import contextmanager
from queue import Empty, Queue
from typing import Iterator, List, Optional

from elasticsearch import (ConnectionError,ConnectionTimeout,Elasticsearch,TransportError,)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Environment variables for Elasticsearch connection
ELASTIC_HOST = os.getenv("ELASTIC_HOST", "localhost")
ELASTIC_PORT = os.getenv("ELASTIC_PORT", "9200")
ELASTIC_USER = os.getenv("ELASTIC_USER", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")
ELASTIC_POOL_SIZE = int(os.getenv("ELASTIC_POOL_SIZE", "4"))
ELASTIC_ACQUIRE_TIMEOUT = float(os.getenv("ELASTIC_ACQUIRE_TIMEOUT", "5.0"))


def _build_client() -> Optional[Elasticsearch]:
    """Instantiate an Elasticsearch client using env configuration."""
    try:
        try:
            return Elasticsearch(
                hosts=[{"host": ELASTIC_HOST, "port": int(ELASTIC_PORT)}],
                basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
                request_timeout=30,
                max_retries=10,
                retry_on_timeout=True
            )
        except TypeError:
            url = f"http://{ELASTIC_USER}:{ELASTIC_PASSWORD}@{ELASTIC_HOST}:{ELASTIC_PORT}"
            return Elasticsearch(
                [url],
            )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Elasticsearch constructor failed: %s", exc)
        return None


def connect_elastic() -> Optional[Elasticsearch]:
    """Create a ready-to-use Elasticsearch client, falling back on info()."""
    client = _build_client()
    if client is None:
        return None

    try:
        if client.ping():
            logger.info("Connected to Elasticsearch")
            return client
        logger.warning("Elasticsearch ping returned False; attempting info() fallback")
    except Exception as exc:  # pragma: no cover - elastic raises
        logger.warning("Elasticsearch ping raised %s; attempting info() fallback", exc)

    try:
        info = client.info()
        if isinstance(info, dict):
            logger.info("Connected to Elasticsearch (info() fallback)")
            return client
    except TransportError as terr:
        status = getattr(terr, "status_code", None)
        if status in (400, 401):
            logger.warning(
                "Elasticsearch info() returned status %s; treating cluster as reachable",
                status,
            )
            return client
        logger.error("Elasticsearch info() transport error: %s", terr)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Elasticsearch info() fallback failed: %s", exc)

    logger.error("Could not connect to Elasticsearch after ping/info() checks")
    return None


class ElasticsearchPool:
    """Simple connection pool for Elasticsearch clients."""

    def __init__(self, pool_size: int, acquire_timeout: float) -> None:
        self.pool_size = pool_size
        self.acquire_timeout = acquire_timeout
        self._pool: Queue[Elasticsearch] = Queue(maxsize=pool_size)
        self._initialized = False
        self._clients: List[Elasticsearch] = []
        self._max_retries = 5
        self._base_backoff_seconds = 1

    def _fill_pool(self) -> bool:
        created = 0
        attempt = 0
        backoff = self._base_backoff_seconds
        while created < self.pool_size and attempt < self._max_retries:
            client = connect_elastic()
            if client is None:
                attempt += 1
                logger.warning(
                    "Elasticsearch client creation failed on attempt %d/%d; retrying in %ds",
                    attempt,
                    self._max_retries,
                    backoff,
                )
                if attempt >= self._max_retries:
                    break
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            self._pool.put(client)
            self._clients.append(client)
            created += 1

        if created == 0:
            logger.error("Initialized Elasticsearch pool with 0 clients after %d attempts", attempt)
            return False

        logger.info("Initialized Elasticsearch pool with %d clients", created)
        return True

    @contextmanager
    def get_client(self) -> Iterator[Elasticsearch]:
        if not self._initialized:
            if not self._fill_pool():
                raise RuntimeError(
                    "Elasticsearch pool could not initialize any clients; ensure Elasticsearch is reachable"
                )
            self._initialized = True

        try:
            client = self._pool.get(timeout=self.acquire_timeout)
        except Empty as exc:
            raise RuntimeError("Timed out acquiring Elasticsearch client from pool") from exc

        try:
            yield client
        finally:
            self._pool.put(client)

    def close(self) -> None:
        while not self._pool.empty():
            try:
                client = self._pool.get_nowait()
            except Empty:
                break
            try:
                if hasattr(client, "close"):
                    client.close()
            except Exception:  # pragma: no cover - best effort
                pass

        for client in self._clients:
            try:
                if hasattr(client, "close"):
                    client.close()
            except Exception:  # pragma: no cover - best effort
                pass

        self._clients.clear()
        self._initialized = False


default_pool = ElasticsearchPool(
    pool_size=ELASTIC_POOL_SIZE,
    acquire_timeout=ELASTIC_ACQUIRE_TIMEOUT,
)


def execute_query_es(index, body, params=None, fetch_one=False):
    with default_pool.get_client() as es:
        try:
            response = es.search(index=index, body=body, params=params or {})
            hits = response.get("hits", {}).get("hits", [])
            if fetch_one:
                return hits[0] if hits else None
            return hits
        except Exception as exc:
            logger.error("Error executing query: %s", exc)
            raise


def execute_text_search_by_title(index, title_query, size=10, match_phrase=False, fuzziness=None, fields=None):
    if fields is None:
        fields = ["title"]

    if match_phrase:
        query = {"match_phrase": {fields[0]: {"query": title_query}}}
    else:
        if len(fields) == 1:
            match_body = {"query": title_query}
            if fuzziness is not None:
                match_body["fuzziness"] = fuzziness
            query = {"match": {fields[0]: match_body}}
        else:
            match_body = {"query": title_query, "fields": fields}
            if fuzziness is not None:
                match_body["fuzziness"] = fuzziness
            query = {"multi_match": match_body}

    body = {"size": size, "query": query}

    try:
        return execute_query_es(index, body)
    except Exception as exc:
        logger.error("Error executing text search by title: %s", exc)
        raise


def execute_vector_query(index, query_vector, k=10, vector_field="embeddings", num_candidates=50):
    try:
        if hasattr(query_vector, "tolist"):
            query_vector = query_vector.tolist()
        vector = [float(x) for x in query_vector]
    except Exception as exc:
        logger.error("Invalid query_vector provided to execute_vector_query: %s", exc)
        raise ValueError("query_vector must be an iterable of numbers") from exc

    body = {
        "size": k,
        "query": {
            "knn": {
                "field": vector_field,
                "query_vector": vector,
                "k": k,
                "num_candidates": num_candidates,
            }
        },
    }

    logger.debug(
        "Executing vector query on index=%s field=%s k=%s num_candidates=%s",
        index,
        vector_field,
        k,
        num_candidates,
    )

    with default_pool.get_client() as es:
        try:
            response = es.search(index=index, body=body)
            return response.get("hits", {}).get("hits", [])
        except Exception as exc:
            logger.error("Error executing vector query: %s", exc)
            raise