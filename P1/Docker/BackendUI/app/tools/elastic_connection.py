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


def execute_vector_query(index, query_vector, k=10, vector_field="embeddings", num_candidates=20, filter_query=None):
    """Run a vector (kNN) search against `index` using `query_vector`.

    Returns the raw hits list from Elasticsearch (list of hit dicts).
    """
    #Allow the caller to pass either:
    # - a raw iterable of numbers (list/tuple/np.array), or
    # - a dict-like payload containing the embedding under the key 'embedding' or 'embeddings'


    # Normalize input: accept raw iterables or dict-like payloads containing
    # the embedding under 'embedding' or 'embeddings'. Coerce numpy arrays
    # or similar via tolist() when available.
    field_def = None
    try:
        # If a dict-like payload is passed, extract its embedding
        if isinstance(query_vector, dict):
            vec = None
            # prefer common keys
            for key in ("embedding", "embeddings", "vector"):
                if key in query_vector:
                    vec = query_vector.get(key)
                    break
            # If nothing found, maybe the dict stores the embedding under a nested key
            if vec is None:
                # attempt to find the first list-like value
                for v in query_vector.values():
                    if isinstance(v, (list, tuple)) or hasattr(v, "tolist"):
                        vec = v
                        break
            if vec is None:
                logger.warning("execute_vector_query: no embedding found in payload for index=%s", index)
                return []
            query_vector = vec

        # If it's a numpy array or other array-like, convert to list
        if hasattr(query_vector, "tolist") and not isinstance(query_vector, list):
            try:
                query_vector = query_vector.tolist()
            except Exception:
                # fallback to iterating
                query_vector = list(query_vector)

        # If the embedding value is None (e.g. null in ES _source), return empty
        if query_vector is None:
            logger.info("execute_vector_query: received null embedding for index=%s; returning empty results", index)
            return []

        # Ensure we have a plain list of floats
        if isinstance(query_vector, (list, tuple)):
            query_vector = [float(x) for x in query_vector]
        else:
            # last resort: try to coerce to list
            try:
                query_vector = list(query_vector)
                query_vector = [float(x) for x in query_vector]
            except Exception:
                raise TypeError("query_vector must be a list/tuple or dict containing an 'embedding' key")

    except Exception as norm_exc:
        logger.error("Error normalizing embedding input for index=%s: %s", index, norm_exc)
        raise

    # Prepare kNN body (Elasticsearch 8 expects knn at top-level)
    body = {
        "size": k,
        "knn": {
            "field": vector_field,
            "query_vector": query_vector,
            "k": k,
            "num_candidates": num_candidates,
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
        # Validate mapping exists and field is dense_vector
        try:
            mapping = es.indices.get_mapping(index=index)
            mapping_item = mapping.get(index)
            if mapping_item is None:
                mapping_item = next(iter(mapping.values())) if mapping else {}
            props = mapping_item.get("mappings", {}).get("properties", {})
            field_def = props.get(vector_field)
            if field_def is None:
                # case-insensitive fallback
                for fk, fv in props.items():
                    if fk.lower() == vector_field.lower():
                        field_def = fv
                        break

            if not field_def or field_def.get("type") != "dense_vector":
                logger.warning(
                    "Index '%s' does not expose dense_vector field '%s'; skipping vector search. Mapping sample keys: %s",
                    index,
                    vector_field,
                    list(props.keys())[:20],
                )
                logger.debug("Full mapping properties for index %s: %s", index, props)
                return []

            # If the field exists but index=true is not set, kNN won't be usable (Elasticsearch requires index:true).
            if field_def and field_def.get("type") == "dense_vector":
                if not field_def.get("index", False):
                    logger.warning(
                        "dense_vector field '%s' in index '%s' does not have index:true; kNN will be unavailable and searches may fall back to slower script scoring",
                        vector_field,
                        index,
                    )

            # dims check if present
            dims = field_def.get("dims")
            if dims is not None and len(query_vector) != int(dims):
                logger.error(
                    "Query vector length %d does not match mapping dims %s for index=%s field=%s",
                    len(query_vector),
                    dims,
                    index,
                    vector_field,
                )
                raise ValueError(f"Vector length {len(query_vector)} does not match mapping dims {dims}")
        except Exception as mm_exc:
            logger.debug("Could not retrieve mapping for index %s: %s", index, mm_exc)

        # Try kNN search first
        try:
            resp = es.search(index=index, body=body)
            return resp.get("hits", {}).get("hits", [])
        except Exception as exc:
            msg = str(exc)
            logger.warning("kNN search failed for index=%s: %s", index, msg)
            # If knn is rejected by cluster despite mapping, try script_score fallback
            if field_def and ("only supported on [dense_vector] fields" in msg or "failed to create query" in msg):
                logger.info("Falling back to script_score cosineSimilarity for index=%s field=%s", index, vector_field)
                # Use a guarded painless script: check for missing/empty fields and catch any runtime
                # exceptions from cosineSimilarity (for example when field type is incompatible).
                # This prevents the whole search request failing with a runtime error.
                script_source = (
                    "double score = 0.0;"
                    "try {"
                    f" if (doc['{vector_field}'].size() == 0) {{ return 0; }}"
                    f" return cosineSimilarity(params.query_vector, '{vector_field}') + 1.0;"
                    "} catch (Exception e) { return 0; }"
                )

                # If the caller provided a filter_query, use it to limit the documents that
                # are scored by the script_score fallback. This can drastically reduce CPU
                # when dense_vector indexing is not available.
                fallback_query = filter_query if filter_query is not None else {"match_all": {}}

                script_body = {
                    "size": k,
                    "query": {
                        "script_score": {
                            "query": fallback_query,
                            "script": {
                                "source": script_source,
                                "params": {"query_vector": query_vector},
                            },
                        }
                    },
                }
                try:
                    resp2 = es.search(index=index, body=script_body)
                    return resp2.get("hits", {}).get("hits", [])
                except Exception as exc2:
                    logger.error("Fallback script_score vector query also failed for index=%s: %s", index, exc2)
                    raise
            logger.error("Error executing vector query for index=%s: %s", index, exc)
            raise


def vector_search(index: str, embedding, k: int = 10, vector_field: str = "embeddings", num_candidates: int = 50, return_scores: bool = False):
    """Convenience wrapper: run a vector search and return normalized hits.

    Returns a list of dicts with keys: '_id', '_source' and optional '_score'.
    """
    hits = execute_vector_query(index, embedding, k=k, vector_field=vector_field, num_candidates=num_candidates) or []
    results = []
    for h in hits:
        item = {"_id": h.get("_id"), "_source": h.get("_source")}
        if return_scores:
            item["_score"] = h.get("_score")
        results.append(item)
    return results
