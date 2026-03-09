import os
from typing import Any

from opensearchpy import OpenSearch

INGREDIENTS_INDEX = "ingredients"
RECIPES_INDEX = "recipes"

_COMMON_ANALYSIS: dict[str, Any] = {
    "tokenizer": {
        "ngram_tokenizer": {
            "type": "ngram",
            "min_gram": 1,
            "max_gram": 3,
            "token_chars": [],
        }
    },
    "filter": {
        "kana_to_hiragana": {
            "type": "icu_transform",
            "id": "Katakana-Hiragana",
        }
    },
    "analyzer": {
        "kuromoji_normalize": {
            "type": "custom",
            "tokenizer": "kuromoji_tokenizer",
            "filter": [
                "kuromoji_baseform",
                "kuromoji_part_of_speech",
                "cjk_width",
                "kana_to_hiragana",
                "ja_stop",
                "lowercase",
            ],
        },
        "ngram_kana": {
            "type": "custom",
            "tokenizer": "ngram_tokenizer",
            "filter": ["kana_to_hiragana", "cjk_width", "lowercase"],
        },
        "kana_search": {
            "type": "custom",
            "tokenizer": "keyword",
            "filter": ["kana_to_hiragana", "cjk_width", "lowercase"],
        },
    },
}

_TEXT_FIELD: dict[str, Any] = {
    "type": "text",
    "analyzer": "kuromoji_normalize",
    "fields": {
        "partial": {
            "type": "text",
            "analyzer": "ngram_kana",
            "search_analyzer": "kana_search",
        }
    },
}

INGREDIENTS_MAPPING: dict[str, Any] = {
    "settings": {
        "index": {"max_ngram_diff": 2},
        "analysis": _COMMON_ANALYSIS,
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "name": _TEXT_FIELD,
            "aliases": _TEXT_FIELD,
            "yomi": _TEXT_FIELD,
        }
    },
}


RECIPES_MAPPING: dict[str, Any] = {
    "settings": {
        "index": {"max_ngram_diff": 2},
        "analysis": _COMMON_ANALYSIS,
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "name": _TEXT_FIELD,
            "name_yomi": _TEXT_FIELD,
            "name_aliases": _TEXT_FIELD,
            "ingredient_names": _TEXT_FIELD,
            "category": {"type": "keyword"},
            "code": {"type": "keyword"},
            "menu_num": {"type": "keyword"},
            "image_url": {"type": "keyword", "index": False},
        }
    },
}


class IngredientSearchClient:
    def __init__(self, client: OpenSearch) -> None:
        self._client = client

    def ensure_index(self, *, recreate: bool = False) -> None:
        if recreate and self._client.indices.exists(index=INGREDIENTS_INDEX):
            self._client.indices.delete(index=INGREDIENTS_INDEX)
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
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name.partial", "aliases.partial", "yomi.partial"],
                            }
                        },
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


class RecipeSearchClient:
    def __init__(self, client: OpenSearch) -> None:
        self._client = client

    def ensure_index(self, *, recreate: bool = False) -> None:
        if recreate and self._client.indices.exists(index=RECIPES_INDEX):
            self._client.indices.delete(index=RECIPES_INDEX)
        if not self._client.indices.exists(index=RECIPES_INDEX):
            self._client.indices.create(index=RECIPES_INDEX, body=RECIPES_MAPPING)

    def upsert(
        self,
        recipe_id: int,
        name: str,
        ingredient_names: list[str],
        category: str | None = None,
        code: str | None = None,
        menu_num: str | None = None,
        image_url: str | None = None,
        name_yomi: str | None = None,
        name_aliases: list[str] | None = None,
    ) -> None:
        doc: dict[str, Any] = {
            "id": recipe_id,
            "name": name,
            "ingredient_names": " ".join(ingredient_names),
        }
        if category is not None:
            doc["category"] = category
        if code is not None:
            doc["code"] = code
        if menu_num is not None:
            doc["menu_num"] = menu_num
        if image_url is not None:
            doc["image_url"] = image_url
        if name_yomi is not None:
            doc["name_yomi"] = name_yomi
        if name_aliases is not None:
            doc["name_aliases"] = " ".join(name_aliases)
        self._client.index(index=RECIPES_INDEX, id=str(recipe_id), body=doc)

    def search(
        self,
        query: str,
        size: int = 50,
        ingredient_expansions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        should: list[dict[str, Any]] = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["name^2", "name_yomi^2", "name_aliases^2", "ingredient_names"],
                }
            },
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "name.partial^2",
                        "name_yomi.partial^2",
                        "name_aliases.partial^2",
                        "ingredient_names.partial",
                    ],
                }
            },
        ]
        if ingredient_expansions:
            for ing_name in ingredient_expansions:
                should.append({"match": {"ingredient_names": {"query": ing_name}}})
        body: dict[str, Any] = {
            "query": {
                "bool": {
                    "should": should,
                    "minimum_should_match": 1,
                }
            },
            "size": size,
        }
        resp = self._client.search(index=RECIPES_INDEX, body=body)
        return [hit["_source"] for hit in resp["hits"]["hits"]]

    def delete(self, recipe_id: int) -> None:
        self._client.delete(index=RECIPES_INDEX, id=str(recipe_id), ignore=[404])


def create_opensearch_client() -> OpenSearch:
    url = os.environ.get("OPENSEARCH_URL", "http://localhost:9205")
    return OpenSearch(hosts=[url], use_ssl=False, verify_certs=False)


def create_ingredient_search_client() -> IngredientSearchClient:
    client = create_opensearch_client()
    return IngredientSearchClient(client)


def create_recipe_search_client() -> RecipeSearchClient:
    client = create_opensearch_client()
    return RecipeSearchClient(client)
