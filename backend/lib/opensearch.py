import os
from typing import Any

from opensearchpy import OpenSearch

INGREDIENTS_INDEX = "ingredients"

INGREDIENTS_MAPPING: dict[str, Any] = {
    "settings": {
        "analysis": {
            "analyzer": {
                "kuromoji_normalize": {
                    "type": "custom",
                    "tokenizer": "kuromoji_tokenizer",
                    "filter": [
                        "kuromoji_baseform",
                        "kuromoji_part_of_speech",
                        "cjk_width",
                        "ja_stop",
                        "lowercase",
                    ],
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "text", "analyzer": "kuromoji_normalize"},
            "aliases": {"type": "text", "analyzer": "kuromoji_normalize"},
            "yomi": {"type": "text", "analyzer": "kuromoji_normalize"},
        }
    },
}


class IngredientSearchClient:
    def __init__(self, client: OpenSearch) -> None:
        self._client = client

    def ensure_index(self) -> None:
        if not self._client.indices.exists(index=INGREDIENTS_INDEX):
            self._client.indices.create(index=INGREDIENTS_INDEX, body=INGREDIENTS_MAPPING)

    def upsert(self, ingredient_id: int, name: str, aliases: list[str] | None = None, yomi: str | None = None) -> None:
        doc: dict[str, Any] = {"id": ingredient_id, "name": name}
        if aliases is not None:
            doc["aliases"] = aliases
        if yomi is not None:
            doc["yomi"] = yomi
        self._client.index(index=INGREDIENTS_INDEX, id=str(ingredient_id), body=doc)

    def search(self, query: str, size: int = 10) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name", "aliases", "yomi"],
                            }
                        },
                        {"wildcard": {"name": {"value": f"*{query}*"}}},
                        {"wildcard": {"yomi": {"value": f"*{query}*"}}},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "size": size,
        }
        resp = self._client.search(index=INGREDIENTS_INDEX, body=body)
        return [hit["_source"] for hit in resp["hits"]["hits"]]

    def delete(self, ingredient_id: int) -> None:
        self._client.delete(index=INGREDIENTS_INDEX, id=str(ingredient_id), ignore=[404])


def create_opensearch_client() -> OpenSearch:
    url = os.environ.get("OPENSEARCH_URL", "http://localhost:9205")
    return OpenSearch(hosts=[url], use_ssl=False, verify_certs=False)


def create_ingredient_search_client() -> IngredientSearchClient:
    client = create_opensearch_client()
    return IngredientSearchClient(client)
