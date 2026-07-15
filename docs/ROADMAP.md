# Roadmap & design decisions

This document records what has recently shipped, what is intentionally **deferred**,
and what is **rejected by design** — the latter so the rationale is not re-litigated in
every feature request.

Kobject's guiding principle: **types describe and enforce their own validity.** Kobject
checks that a value *is of the declared type*; any richer "is this value acceptable?"
logic belongs in the type itself (typically a small subclass), not in extra declarative
metadata layered onto the model.

## Recently shipped

- **`typing.Literal`** — validated by membership (value + type identity, per PEP 586),
  supported in `from_dict`/`from_json` and JSON Schema (`enum`).
- **Tagged discriminated unions** — a union of Kobjects that share a unique `Literal` tag
  field is discriminated automatically; the tag selects the member during deserialization.
- **Generic models (`TypeVar`)** — parametrized generics (`Box[int]`) used as fields are
  bound and validated/deserialized/schema-generated with their type variables substituted.
- **Optional `orjson` backend** — `pip install "kobject[orjson]"`; used automatically for
  `to_json()`/`from_json()` when present.
- **JSON Schema Draft 2020-12** with a `mode` argument: `"validation"` (defaulted fields
  optional) vs `"serialization"` (every field required).

## Deferred (wanted, not yet built)

### Field aliases
Mapping an external JSON key to a differently-named attribute (e.g. JSON `"userId"` →
attribute `user_id`), for `from_dict`/`from_json`/`to_dict`/`json_schema`.

- **Status:** deferred, not rejected. It is pure name mapping, not value validation, so it
  does not conflict with the design principle.
- **Open questions:** how to declare the alias without pulling in a heavy `Field(...)`
  descriptor layer; whether aliases are bidirectional; how they interact with
  `json_schema()` (`propertyNames` / `required`).

### OpenAPI 3.1 schema output
An `openapi_schema()` variant emitting a Schema Object with `#/components/schemas/` refs
(OpenAPI 3.1 is a superset of JSON Schema 2020-12, which is already emitted).

- **Status:** deferred. The current `json_schema()` output is already 2020-12 and close to
  OpenAPI-compatible; a dedicated method can be added when there is a concrete need.

## Rejected by design

These are **not** planned. They conflict with the principle that value validation lives in
the type's `__init__`.

### Custom field validators
E.g. per-field validator callbacks / decorators (`@field_validator`-style).

- **Why rejected:** if a value needs validation beyond "is this type", create the type and
  validate in *its* constructor. Example: instead of attaching a phone-number validator to a
  `str` field, define `class Phone(str)` that checks itself in `__init__`, and annotate the
  field as `Phone`. Kobject then enforces it for free, and the rule is reusable everywhere
  the type is used.

### Declarative value constraints (`Annotated` metadata)
E.g. `Annotated[int, Gt(0)]`, `Annotated[str, MinLen(3)]`, regex constraints, etc.

- **Why rejected:** same reasoning. Constraints such as "positive int" or "3+ chars" are
  properties of a *type* (`PositiveInt`, `ShortStr`), and belong in that type's `__init__`.
  Encoding them as declarative metadata on the model duplicates a type system kobject
  deliberately keeps thin, and splits validation logic away from the type it describes.

The payoff of this stance: validation is defined once, on the type; it composes (a
`Phone` inside a `list[Phone]`, a union, or another model works automatically); and the
model stays a plain description of *which types* go where.
