```
                       ▄▄          ▄▄                      
▀████▀ ▀███▀          ▄██          ██                 ██   
  ██   ▄█▀             ██                             ██   
  ██ ▄█▀      ▄██▀██▄  ██▄████▄  ▀███  ▄▄█▀██ ▄██▀████████ 
  █████▄     ██▀   ▀██ ██    ▀██   ██ ▄█▀   ███▀  ██  ██   
  ██  ███    ██     ██ ██     ██   ██ ██▀▀▀▀▀▀█       ██   
  ██   ▀██▄  ██▄   ▄██ ██▄   ▄██   ██ ██▄    ▄█▄    ▄ ██   
▄████▄   ███▄ ▀█████▀  █▀█████▀    ██  ▀█████▀█████▀  ▀████
                                ██ ██                      
                                ▀███                       By CenturyBoys
                                
Know your object is a __init__ type validator for class and dataclass
```

## Usage

Kobject can be use inside default class declaration and with dataclasses. Kobject uses the ```__init__``` signature to check types.

### Default classes

```python
from kobject import Kobject

class StubClass(Kobject):
    a_int: int
    a_bool: bool
    
    def __init__(
        self,
        a_int: int,
        a_bool: bool
    ):
        self.a_int = a_int
        self.a_bool = a_bool
        self.__post_init__()

instance = StubClass(a_int=1, a_bool=True)
```
Notice that in the default class declaration you need to call ```self.__post_init__()``` at the end of the ```__init__``` declaration.


### Dataclass

```python
from dataclasses import dataclass
from kobject import Kobject

@dataclass
class StubClass(Kobject):
    a_int: int
    a_bool: bool

instance = StubClass(a_int=1, a_bool=True)
```
By default, dataclass calls ```self.__post_init__()``` at the end of the ```__init__``` declaration [doc](https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__). 


### Exception

Kobject raises ```TypeError``` with all validation errors, that means it checks all your object's attributes before raising the ```TypeError```. Types like List and Tuple will have all their elements checked.

```python
from dataclasses import dataclass
from kobject import Kobject
from typing import List, Tuple

@dataclass
class StubClass(Kobject):
    a_list_int: List[int]
    a_tuple_bool: Tuple[bool]

instance = StubClass(a_list_int=[1, "", 2, ""], a_tuple_bool=["", True])
```
```bash
Traceback (most recent call last):
...
TypeError: Class 'StubClass' type error:
 Wrong type for a_list_int: typing.List[int] != `[1, '', 2, '']`
 Wrong type for a_tuple_bool: typing.Tuple[bool] != `['', True]`
```

You can retrieve the structured error by calling `json_error` method

```python
try:
    instance = StubClass(a_list_int=[1, "", 2, ""], a_tuple_bool=["", True])
except TypeError as _error:
    print(_error.json_error())
```

Output:

```bash
[{'field': 'a_list_int', 'type': typing.List[int], 'value': "[1, '', 2, '']"}, {'field': 'a_tuple_bool', 'type': typing.Tuple[bool], 'value': "['', True]"}]
```

You can use lazy validation to improve performance, the code will stop in the first found error for this use

```python
from kobject import Kobject

Kobject.set_lazy_type_check(status=True)
```

### Default value

Kobject supports default values and will check them before any validation, that means if you declare a ```a_bool: bool = None``` it will not raise an error.

```python
from dataclasses import dataclass
from kobject import Kobject

class StubClass(Kobject):
    a_bool: bool = None

    def __init__(self, a_bool: bool = 10):
        self.a_bool = a_bool
        self.__post_init__()

@dataclass
class StubDataClass(Kobject):
    a_bool: bool = 10
```

### Custom exception

By default, Kobject raise a ```TypeError``` but you can override this exception using `set_validation_custom_exception` for type validation or `set_content_check_custom_exception` for field check on from JSON operation.

```python
from dataclasses import dataclass
from kobject import Kobject


class CustomException(Exception):
    pass


Kobject.set_validation_custom_exception(CustomException)
#Kobject.set_content_check_custom_exception(CustomException)

@dataclass
class StubClass(Kobject):
    a__int: int


instance = StubClass(a__int="")
```
```bash
Traceback (most recent call last):
...
CustomException: Class 'StubClass' type error:
 Wrong type for a__int: <class 'int'> != `''`
```

### ToJSON

Kobject has his own implementation to parse class instance to a JSON representation. 

```python
from dataclasses import dataclass
from typing import List, Tuple

from kobject import Kobject
    
@dataclass
class BaseC(Kobject):
    a_int: int
    a_str: str
    a_list_of_int: List[int]
    a_tuple_of_bool: Tuple[bool]
    
instance = BaseC(
    a_int=1,
    a_str="lala",
    a_list_of_int=[1, 2, 3],
    a_tuple_of_bool=(True,)
)

json_bytes = instance.to_json()

print(json_bytes)
```
```bash
b'{"a_int": 1, "a_str": "lala", "a_list_of_int": [1, 2, 3], "a_tuple_of_bool": [true]}'
```

For complex values ToJSON expose ```set_encoder_resolver``` to handler it. 

Notest, Before encoding the object to JSON bytes, it will be represented by `self.dict()`. Some objects, such as `datetime.datetime`, can be useful in dictionary structures but are not JSON serializable. In such cases, you can use the `on_dict: bool` parameter in the `Kobject.set_encoder_resolver()` method to encode only when JSON bytes are required, not in its dictionary representation.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID

from kobject import Kobject


@dataclass
class BaseA(Kobject):
    a_datetime: datetime


@dataclass
class BaseB:
    a_uuid: UUID


@dataclass
class BaseC(Kobject):
    a_base_a: BaseA
    a_base_b: BaseB
    a_list_of_base_a: List[BaseA]

Kobject.set_encoder_resolver(datetime, lambda value: str(value), False)
Kobject.set_encoder_resolver(BaseB, lambda value: {"a_uuid": str(value.a_uuid)})

instance = BaseC(
    a_base_a=BaseA(a_datetime=datetime.fromisoformat("2023-02-01 17:38:45.389426")),
    a_base_b=BaseB(a_uuid=UUID("1d9cf695-c917-49ce-854b-4063f0cda2e7")),
    a_list_of_base_a=[BaseA(a_datetime=datetime.fromisoformat("2023-02-01 17:38:45.389426"))]
)

dict_repr = instance.dict()

isinstance(dict_repr["a_base_a"]["a_datetime"], datetime)

json_bytes = instance.to_json()

print(json_bytes)
```
```bash
b'{"a_base_a": {"a_datetime": "2023-02-01 17:38:45.389426"}, "a_base_b": {"a_uuid": "1d9cf695-c917-49ce-854b-4063f0cda2e7"}, "a_list_of_base_a": [{"a_datetime": "2023-02-01 17:38:45.389426"}]}'
```

#### Remove None values

Both `dict()` and `to_json()` methods support the `remove_nones` parameter to recursively strip `None` values from the output.

```python
from dataclasses import dataclass
from typing import List, Dict

from kobject import Kobject


@dataclass
class Inner(Kobject):
    value: str | None


@dataclass
class Outer(Kobject):
    a_int: int
    a_str: str | None
    a_list: List[int | None]
    a_dict: Dict[str, int | None]
    inner: Inner


instance = Outer(
    a_int=1,
    a_str=None,
    a_list=[1, None, 2],
    a_dict={"a": 1, "b": None},
    inner=Inner(value=None)
)

# Default behavior preserves None values
print(instance.dict())
# {'a_int': 1, 'a_str': None, 'a_list': [1, None, 2], 'a_dict': {'a': 1, 'b': None}, 'inner': {'value': None}}

# With remove_nones=True, None values are recursively removed
print(instance.dict(remove_nones=True))
# {'a_int': 1, 'a_list': [1, 2], 'a_dict': {'a': 1}, 'inner': {}}

# Also works with to_json()
print(instance.to_json(remove_nones=True))
# b'{"a_int":1,"a_list":[1,2],"a_dict":{"a":1},"inner":{}}'
```

### FromJSON

Kobject has his own implementation to parse JSON to a class instance.

```python
from dataclasses import dataclass
from typing import List, Tuple

from kobject import Kobject


@dataclass
class BaseC(Kobject):
    a_int: int
    a_str: str
    a_list_of_int: List[int]
    a_tuple_of_bool: Tuple[bool]

payload = (
    b'{"a_int": 1,"a_str": "lala","a_list_of_int": [1,2,3],'
    b'"a_tuple_of_bool": [true]}'
)
instance = BaseC.from_json(payload=payload)

print(instance)
```
```bash
BaseC(a_int=1, a_str='lala', a_list_of_int=[1, 2, 3], a_tuple_of_bool=(True,))
```

For complex values FromJSON expose ```set_decoder_resolver``` to handler it.

```python
from datetime import datetime
from dataclasses import dataclass
from typing import List
from uuid import UUID

from kobject import Kobject


@dataclass
class BaseA(Kobject):
    a_datetime: datetime


@dataclass
class BaseB:
    a_uuid: UUID


@dataclass
class BaseC(Kobject):
    a_base_a: BaseA
    a_base_b: BaseB
    a_list_of_base_a: List[BaseA]

Kobject.set_decoder_resolver(
    datetime,
    lambda attr_type, value: datetime.fromisoformat(value)
    if isinstance(value, str)
    else value,
)
Kobject.set_decoder_resolver(
    BaseB,
    lambda attr_type, value: attr_type(a_uuid=UUID(value["a_uuid"]))
    if isinstance(value, dict)
    else value,
)
payload = (
    b'{"a_base_a": {"a_datetime": "2023-02-01 17:38:45.389426"},"a_base_b": {"a_'
    b'uuid":"1d9cf695-c917-49ce-854b-4063f0cda2e7"}, "a_lis'
    b't_of_base_a": [{"a_datetime": "2023-02-01 17:38:45.389426"}]}'
)
instance = BaseC.from_json(payload=payload)

print(instance)
```
```bash
BaseC(a_base_a=BaseA(a_datetime=datetime.datetime(2023, 2, 1, 17, 38, 45, 389426)), a_base_b=BaseB(a_uuid=UUID('1d9cf695-c917-49ce-854b-4063f0cda2e7')), a_list_of_base_a=[BaseA(a_datetime=datetime.datetime(2023, 2, 1, 17, 38, 45, 389426))])
```

### JSON Schema

Kobject can generate JSON Schema Draft 7 from your class definition. This is useful for API documentation, validation, and integration with tools like MCP servers.

```python
from dataclasses import dataclass
from kobject import Kobject
import json

@dataclass
class User(Kobject):
    """
    User model for the application.

    :param name: The user's full name.
    :param age: The user's age in years.
    :param email: Optional email address.
    :example: {"name": "Alice", "age": 30}
    """
    name: str
    age: int
    email: str | None = None

schema = User.json_schema()
print(json.dumps(schema, indent=2))
```
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "The user's full name."
    },
    "age": {
      "type": "integer",
      "description": "The user's age in years."
    },
    "email": {
      "anyOf": [{"type": "string"}, {"type": "null"}],
      "description": "Optional email address.",
      "default": null
    }
  },
  "additionalProperties": false,
  "title": "User model for the application.",
  "required": ["name", "age"],
  "examples": [{"name": "Alice", "age": 30}]
}
```

#### Docstring Metadata

Kobject extracts metadata from reST-style docstrings:

- **Title**: First line of the docstring
- **Description**: Text between title and first directive (if different from title)
- **Field descriptions**: `:param field_name: description`
- **Examples**: `:example: {"json": "object"}`

#### Supported Types

| Python Type | JSON Schema |
|-------------|-------------|
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `None` | `{"type": "null"}` |
| `list[T]` | `{"type": "array", "items": {...}}` |
| `dict[K, V]` | `{"type": "object", "additionalProperties": {...}}` |
| `tuple[X, Y]` | `{"type": "array", "prefixItems": [...], "minItems": N, "maxItems": N}` |
| `set[T]` | `{"type": "array", "items": {...}, "uniqueItems": true}` |
| `T \| None` | `{"anyOf": [{...}, {"type": "null"}]}` |
| `Enum` | `{"type": "string/integer", "enum": [...]}` |
| `Kobject` subclass | `{"$ref": "#/$defs/ClassName"}` |
| `datetime` | `{"type": "string", "format": "date-time"}` |
| `date` | `{"type": "string", "format": "date"}` |
| `time` | `{"type": "string", "format": "time"}` |
| `UUID` | `{"type": "string", "format": "uuid"}` |
| `Decimal` | `{"type": "string", "pattern": "..."}` |

#### Nested Kobjects

Nested Kobject classes are handled using JSON Schema `$ref` and `$defs`:

```python
from dataclasses import dataclass
from kobject import Kobject

@dataclass
class Address(Kobject):
    """
    Address information.

    :param street: Street name and number.
    :param city: City name.
    """
    street: str
    city: str

@dataclass
class Person(Kobject):
    """
    A person with an address.

    :param name: Person's name.
    :param address: Person's home address.
    """
    name: str
    address: Address

schema = Person.json_schema()
# schema["properties"]["address"] == {"$ref": "#/$defs/Address", "description": "..."}
# schema["$defs"]["Address"] contains the Address schema
```

#### Custom Schema Resolvers

For custom types, you can register schema resolvers using `set_schema_resolver`:

```python
from dataclasses import dataclass
from kobject import Kobject

class Money:
    def __init__(self, amount: int, currency: str):
        self.amount = amount
        self.currency = currency

# Register a custom schema resolver
Kobject.set_schema_resolver(
    Money,
    lambda t: {
        "type": "object",
        "properties": {
            "amount": {"type": "integer"},
            "currency": {"type": "string", "minLength": 3, "maxLength": 3}
        },
        "required": ["amount", "currency"]
    }
)

@dataclass
class Invoice(Kobject):
    total: Money

schema = Invoice.json_schema()
# schema["properties"]["total"] contains the custom Money schema
```