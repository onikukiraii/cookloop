from enum import Enum


class IngredientCategory(str, Enum):
    ingredient = "ingredient"
    condiment = "condiment"

    @property
    def label(self) -> str:
        return {"ingredient": "食材", "condiment": "調味料"}[self.value]


class QuantityStatus(str, Enum):
    full = "full"
    half = "half"
    little = "little"

    @property
    def label(self) -> str:
        return {"full": "たっぷり", "half": "半分", "little": "少し"}[self.value]


class ShoppingSource(str, Enum):
    manual = "manual"
    recipe = "recipe"
    staple_auto = "staple_auto"

    @property
    def label(self) -> str:
        return {"manual": "手動追加", "recipe": "レシピから追加", "staple_auto": "定番自動追加"}[self.value]
