from dataclasses import dataclass
from typing import Any


@dataclass
class Base:
    id: str
    name: str
    permissionLevel: str


@dataclass
class Field:
    id: str
    name: str
    type: str
    description: str | None = None
    options: dict[str, Any] | None = None


@dataclass
class View:
    id: str
    name: str
    type: str


@dataclass
class Table:
    id: str
    name: str
    description: str | None = None
    primaryFieldId: str
    fields: list[Field]
    views: list[View]


@dataclass
class Record:
    id: str
    fields: dict[str, Any]


@dataclass
class ListBasesResponse:
    bases: list[Base]
    offset: str | None = None


@dataclass
class TableSchemaResponse:
    tables: list[Table]


@dataclass
class DeleteRecordResponse:
    id: str
    deleted: bool = True