"""Memory Module for SOMS
Persistent vector memory using ChromaDB — offline, local, semantic recall
"""

import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger('MemoryLayer')

PROJECT_ROOT = Path(__file__).resolve().parent
MEMORY_DIR = PROJECT_ROOT / 'soms_memory'

try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    logger.warning("chromadb not installed — using dict-based fallback")

try:
    from chromadb.config import Settings  # type: ignore
except ImportError:
    Settings = None

class MemoryLayer:
    """Persistent memory for SOMS agents — stores interactions, reflections, and project context."""

    def __init__(self, config):
        self.config = config
        self.is_running = False
        self._client = None
        self._collections = {}
        self._fallback_store = {}
        self._init_store()

    def _init_store(self):
        if HAS_CHROMA:
            try:
                MEMORY_DIR.mkdir(parents=True, exist_ok=True)
                if Settings is not None:
                    self._client = chromadb.PersistentClient(
                        path=str(MEMORY_DIR),
                        settings=Settings(anonymized_telemetry=False),
                    )
                else:
                    self._client = chromadb.PersistentClient(path=str(MEMORY_DIR))
                logger.info(f"ChromaDB initialized at {MEMORY_DIR}")
            except Exception as e:
                logger.warning(f"ChromaDB init failed: {e}")
                self._client = None
        if self._client is None:
            logger.info("Using in-memory fallback store")

    def start(self):
        self.is_running = True
        logger.info("MemoryLayer online")

    def stop(self):
        self.is_running = False
        if self._client:
            self._client = None
        logger.info("MemoryLayer offline")

    def _get_collection(self, name):
        if name in self._collections:
            return self._collections[name]
        if self._client:
            try:
                col = self._client.get_or_create_collection(name)
                self._collections[name] = col
                return col
            except Exception:
                return None
        return None

    def store(self, collection, document, metadata=None, doc_id=None):
        metadata = metadata or {}
        metadata['timestamp'] = metadata.get('timestamp', time.time())
        if doc_id is None:
            doc_id = f"{collection}_{int(time.time() * 1e6)}_{hash(document) & 0xffffffff}"
        if self._client:
            col = self._get_collection(collection)
            if col:
                try:
                    col.add(
                        documents=[document],
                        metadatas=[metadata],
                        ids=[doc_id],
                    )
                    return doc_id
                except Exception as e:
                    logger.debug(f"ChromaDB store error: {e}")
        if collection not in self._fallback_store:
            self._fallback_store[collection] = []
        self._fallback_store[collection].append({
            'id': doc_id,
            'document': document,
            'metadata': metadata,
            'timestamp': time.time(),
        })
        if len(self._fallback_store[collection]) > 1000:
            self._fallback_store[collection] = self._fallback_store[collection][-500:]
        return doc_id

    def query(self, collection, query_text, n_results=5):
        if self._client:
            col = self._get_collection(collection)
            if col:
                try:
                    n_results = min(n_results, max(col.count(), 1))
                    results = col.query(query_texts=[query_text], n_results=n_results)
                    if results and results.get('documents'):
                        docs = []
                        for i, doc in enumerate(results['documents'][0]):
                            meta = (results['metadatas'][0][i] if results.get('metadatas') else {}) or {}
                            docs.append({'document': doc, 'metadata': meta, 'id': results['ids'][0][i] if results.get('ids') else ''})
                        return docs
                except Exception as e:
                    logger.debug(f"ChromaDB query error: {e}")
        if collection in self._fallback_store:
            docs = self._fallback_store[collection][-n_results:]
            return [{'document': d['document'], 'metadata': d['metadata'], 'id': d['id']} for d in docs]
        return []

    def recall_recent(self, collection, limit=10):
        if self._client:
            col = self._get_collection(collection)
            if col:
                try:
                    res = col.get(include=['documents', 'metadatas'], limit=limit)
                    docs = res.get('documents') or []
                    metas = res.get('metadatas') or []
                    ids = res.get('ids') or []
                    return [
                        {'document': d, 'metadata': (metas[i] if i < len(metas) else {}), 'id': (ids[i] if i < len(ids) else '')}
                        for i, d in enumerate(docs)
                    ]
                except Exception:
                    pass
        if collection in self._fallback_store:
            docs = self._fallback_store[collection][-limit:]
            return [{'document': d['document'], 'metadata': d['metadata'], 'id': d['id']} for d in docs]
        return []

    def count(self, collection):
        if self._client:
            col = self._get_collection(collection)
            if col:
                try:
                    return col.count()
                except Exception:
                    pass
        if collection in self._fallback_store:
            return len(self._fallback_store[collection])
        return 0

    def clear_collection(self, name):
        """Permanently delete all documents in a collection (local only)."""
        if self._client:
            try:
                try:
                    self._client.delete_collection(name)
                except Exception:
                    pass
                self._collections.pop(name, None)
            except Exception as e:
                logger.warning(f"Failed to clear collection {name}: {e}")
        if name in self._fallback_store:
            self._fallback_store[name] = []

    def clear_all(self):
        """Wipe every stored collection — erases all of SOMS's memory of you."""
        for name in list(self._collections.keys()) + list(self._fallback_store.keys()):
            self.clear_collection(name)

    def prune_old(self, limit=500):
        """Keep only the most recent `limit` entries per collection.

        Returns the number of entries removed. Keeps memory lean for
        efficiency without erasing everything (use clear_* to wipe).
        """
        removed = 0
        if self._client:
            for name in list(self._collections.keys()):
                col = self._get_collection(name)
                if not col:
                    continue
                try:
                    total = col.count()
                    if total <= limit:
                        continue
                    res = col.get(include=['metadatas'], limit=total)
                    ids = res.get('ids') or []
                    # Sort by timestamp (oldest first) and drop the excess.
                    items = []
                    for i, cid in enumerate(ids):
                        meta = (res.get('metadatas') or [{}])[i] or {}
                        ts = meta.get('timestamp', 0)
                        items.append((ts, cid))
                    items.sort(key=lambda x: x[0])
                    to_drop = [cid for _, cid in items[:total - limit]]
                    if to_drop:
                        col.delete(ids=to_drop)
                        removed += len(to_drop)
                except Exception:
                    pass
        for name in list(self._fallback_store.keys()):
            store = self._fallback_store[name]
            if len(store) > limit:
                drop = len(store) - limit
                self._fallback_store[name] = store[drop:]
                removed += drop
        if removed:
            logger.info(f"Pruned {removed} old memory entries")
        return removed

    def repair(self):
        """Attempt to recover from a corrupted/unavailable ChromaDB store.

        Re-initializes the client and drops any collection that fails to load,
        falling back to the in-memory store so SOMS keeps running.
        """
        self._client = None
        self._collections = {}
        try:
            self._init_store()
            if self._client:
                for col in self._client.list_collections() or []:
                    name = col.name if hasattr(col, 'name') else col
                    try:
                        self._client.get_or_create_collection(name)
                    except Exception:
                        try:
                            self._client.delete_collection(name)
                        except Exception:
                            pass
            logger.info("MemoryLayer repaired")
            return True
        except Exception as e:
            logger.warning(f"MemoryLayer repair failed: {e}")
            self._client = None
            return False

    def get_collections(self):
        if self._client:
            try:
                return self._client.list_collections() or []
            except Exception:
                pass
        return list(self._fallback_store.keys())

    def get_status(self):
        if self._client:
            collections = self.get_collections()
            total = sum(self.count(c.name if hasattr(c, 'name') else c) for c in collections)
            return {
                'engine': 'chromadb',
                'path': str(MEMORY_DIR),
                'collections': len(collections),
                'total_documents': total,
            }
        return {
            'engine': 'fallback',
            'collections': len(self._fallback_store),
            'total_documents': sum(len(v) for v in self._fallback_store.values()),
        }
