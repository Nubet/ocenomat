import unicodedata
from uuid import NAMESPACE_URL, UUID, uuid5

CATALOG_NAMESPACE = uuid5(NAMESPACE_URL, "urn:kompas:competency-model")


def stable_id(text: str, parent: UUID = CATALOG_NAMESPACE) -> UUID:
    return uuid5(
        parent, " ".join(unicodedata.normalize("NFC", text).split()).casefold()
    )
