from time import time
from typing import Any

from fastembed import SparseTextEmbedding, SparseEmbedding
from qdrant_client import QdrantClient, models as m
from glab.comm.library import VdbClient, LlmClient

class VdbQdrantClient(VdbClient):

  def __init__(self, host: str, vector_size: int, collection_name: str, sparse_model: str | None = None):
    self.host = host
    self.vector_size = vector_size
    self.collection_name = collection_name
    self.sparse_model = SparseTextEmbedding(
      sparse_model if sparse_model is not None else "prithivida/Splade_PP_en_v1"
    )
    self.client = QdrantClient(url=host, check_compatibility=False, prefer_grpc=False)

  def info(self) -> str:
    return str(self.client.info())

  def reset_collection(self, index_fields: list[str]):
    self.delete_collection()
    self.client.create_collection(
      collection_name = self.collection_name,
      vectors_config = { "dense": m.VectorParams(size=self.vector_size, distance=m.Distance.COSINE) },
      sparse_vectors_config = { "splade_sparse": m.SparseVectorParams(index=m.SparseIndexParams()) }
    )
    for field in index_fields:
      self.client.create_payload_index(
        collection_name = self.collection_name,
        field_name = field,
        field_schema = m.PayloadSchemaType.KEYWORD
      )

  def delete_collection(self):
    if self.client.collection_exists(self.collection_name):
      self.client.delete_collection(self.collection_name)

  def import_collection(self, llm_client: LlmClient, entries: list[dict[str, Any]]):
    total = len(entries)
    step_count = 30
    for start in range(0, total, step_count):
      batch_entries = entries[start:start + step_count]
      points = self._make_search_points(start, llm_client, batch_entries)
      self.client.upsert(
        collection_name=self.collection_name,
        points=points,
        wait=True
      )
      finished_count = min(start + len(batch_entries), total)
      print(f"imported: {finished_count}/{total}")

  def add_entry(self, llm_client: LlmClient, entry: dict[str, Any]) -> int | str:
    pid = int(time()/1000)
    vector = self._get_dense_vector(llm_client, _make_search_text(entry))
    text = _make_search_text(entry)
    pt = self._make_search_point(pid=pid, text=text, vector=vector, **entry)
    self.client.upsert(
      collection_name=self.collection_name,
      points=[pt],
      wait=True
    )
    return pid

  def neural_search(self, llm_client: LlmClient, text: str, **params) -> list[dict[str, Any] | None]:
    dense_vector = self._get_dense_vector(llm_client, text)
    sparse_vector = self._get_sparse_vector(text)
    query_filter = _get_filter(params)
    # noinspection bad-argument-type
    search_result = self.client.query_points(
      collection_name = self.collection_name,
      prefetch = [
        m.Prefetch(query=dense_vector, using="dense", limit=10),
        m.Prefetch(query=sparse_vector, using="splade_sparse", limit=10),
      ],
      query=m.FusionQuery(fusion=m.Fusion.RRF),
      query_filter=query_filter,
      limit = 5
    ).points
    return [hit.payload for hit in search_result]

  def _make_search_points(self, start: int, llm_client: LlmClient, batch_entries: list[dict[str, Any]]):
    batch_texts = [_make_search_text(entry) for entry in batch_entries]
    batch_dense_vectors = self._get_dense_vectors(llm_client, batch_texts)
    points = []
    for idx, (entry, text, dense_vector) in enumerate(
      zip(batch_entries, batch_texts, batch_dense_vectors)
    ):
      pid = start + idx
      pt = self._make_search_point(pid, text, dense_vector, **entry)
      points.append(pt)
    return points

  def _make_search_point(self, pid: int | str, text: str, vector: Any, **entry):
    _payload = {**entry, "search_text": text}
    _sparse_vector = list(self.sparse_model.embed(text))[0]
    _vector = {
      "dense": vector,
      "splade_sparse": m.SparseVector(
        indices=_sparse_vector.indices.tolist(),
        values=_sparse_vector.values.tolist()
      )
    }
    return m.PointStruct(id=pid, vector=_vector, payload=_payload)

  def _get_dense_vectors(self, llm_client: LlmClient, texts) -> Any:
    vectors = llm_client.embed(texts)
    if len(vectors) != len(texts):
      raise RuntimeError(
        f"LLM return unexpected number of embeddings "
        f"input {len(texts)}，output {len(vectors)}"
      )
    actual_size = len(vectors[0])
    if actual_size != self.vector_size:
      raise RuntimeError(
        f"Unexpected vector size：expected {self.vector_size}，Actual {actual_size}"
      )
    return vectors

  def _get_dense_vector(self, llm_client: LlmClient, text: str) -> Any:
    vectors = self._get_dense_vectors(llm_client, [text])
    return vectors[0]

  def _get_sparse_vector(self, text) -> m.SparseVector:
    sparse_emb: SparseEmbedding = list(self.sparse_model.embed(text))[0]
    return m.SparseVector(
      indices=sparse_emb.indices.tolist(),
      values=sparse_emb.values.tolist()
    )


def _get_filter(params: dict[str, Any]) -> m.Filter:
  must_conditions: list[m.FieldCondition] = []
  for field, value in params.items():
    if value is None: continue
    must_conditions.append(
      m.FieldCondition(
        key=field, match=m.MatchValue(value=value)
      )
    )
  return m.Filter(must=must_conditions)


def _make_search_text(entry):
  name = (entry.get("name") or "").strip()
  description = (entry.get("description") or "").strip()
  return f"{name}\n{description}".strip()
