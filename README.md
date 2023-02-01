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
By default, dataclass calls ```self.__post_init__()``` at the end of the ```__init__``` declaration.


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
  File "/snap/pycharm-community/312/plugins/python-ce/helpers/pydev/pydevconsole.py", line 364, in runcode
    coro = func()
  File "<input>", line 10, in <module>
  File "<string>", line 5, in __init__
  File "/home/marco/projects/kobject/kobject/__init__.py", line 67, in __post_init__
    raise TypeError(message)
TypeError: Validation Errors:
    'a_list_int' : Wrong type! Expected (<class 'int'>,) but giving <class 'str'> on index 1
    'a_list_int' : Wrong type! Expected (<class 'int'>,) but giving <class 'str'> on index 3
    'a_tuple_bool' : Wrong type! Expected <class 'tuple'> but giving <class 'list'>
    'a_tuple_bool' : Wrong type! Expected (<class 'bool'>,) but giving <class 'str'> on index 0
```

### Default value

Kobject supports default values and will check them before any validation, that means if you declare a ```a_bool: bool = None``` it will not raise an error.

```python
from dataclasses import dataclass
from kobject import Kobject

class StubClass(Kobject):
    a_bool: bool = None

    def __init__(self, a_bool: bool = 2):
        self.a_bool = a_bool
        self.__post_init__()

@dataclass
class StubDataClass(Kobject):
    a_bool: bool = None
```

### Custom exception

By default Kobject raise a ```TypeError``` but you can override this exception using ```set_custom_exception```

```python
from dataclasses import dataclass
from kobject import Kobject

class CustomException(Exception):
    pass


Kobject.set_custom_exception(CustomException)


@dataclass
class StubClass(Kobject):
    a__int: int

instance = StubClass(a__int="")
```
```bash
Traceback (most recent call last):
  File "/snap/pycharm-community/312/plugins/python-ce/helpers/pydev/pydevconsole.py", line 364, in runcode
    coro = func()
  File "<input>", line 15, in <module>
  File "<string>", line 4, in __init__
  File "/home/marco/projects/kobject/kobject/__init__.py", line 79, in __post_init__
    raise exception(message)
__main__.CustomException: Validation Errors:
    'a__int' : Wrong type! Expected <class 'int'> but giving <class 'str'>
```

### ToJSON

Kobject has his own implementation to parse class instance to a JSON representation. 

```python
from dataclasses import dataclass
from typing import List, Tuple

from kobject import Kobject, ToJSON
    
@dataclass
class BaseC(Kobject, ToJSON):
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

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID

from kobject import Kobject, ToJSON, FromJSON


@dataclass
class BaseA(Kobject, ToJSON):
    a_datetime: datetime


@dataclass
class BaseB:
    a_uuid: UUID


@dataclass
class BaseC(Kobject, ToJSON, FromJSON):
    a_base_a: BaseA
    a_base_b: BaseB
    a_list_of_base_a: List[BaseA]

ToJSON.set_encoder_resolver(datetime, lambda value: str(value))
ToJSON.set_encoder_resolver(BaseB, lambda value: {"a_uuid": str(value.a_uuid)})

instance = BaseC(
    a_base_a=BaseA(a_datetime=datetime.fromisoformat("2023-02-01 17:38:45.389426")),
    a_base_b=BaseB(a_uuid=UUID("1d9cf695-c917-49ce-854b-4063f0cda2e7")),
    a_list_of_base_a=[BaseA(a_datetime=datetime.fromisoformat("2023-02-01 17:38:45.389426"))]
)

json_bytes = instance.to_json()

print(json_bytes)
```
```bash
b'{"a_base_a": {"a_datetime": "2023-02-01 17:38:45.389426"}, "a_base_b": {"a_uuid": "1d9cf695-c917-49ce-854b-4063f0cda2e7"}, "a_list_of_base_a": [{"a_datetime": "2023-02-01 17:38:45.389426"}]}'
```

### FromJSON

Kobject has his own implementation to parse JSON to a class instance. 

```python
from dataclasses import dataclass
from typing import List, Tuple

from kobject import Kobject
from kobject.from_json import FromJSON


@dataclass
class BaseC(Kobject, FromJSON):
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
from kobject.from_json import FromJSON


@dataclass
class BaseA(Kobject, FromJSON):
    a_datetime: datetime


@dataclass
class BaseB:
    a_uuid: UUID


@dataclass
class BaseC(Kobject, FromJSON):
    a_base_a: BaseA
    a_base_b: BaseB
    a_list_of_base_a: List[BaseA]

FromJSON.set_decoder_resolver(
    datetime,
    lambda attr_type, value: datetime.fromisoformat(value)
    if isinstance(value, str)
    else value,
)
FromJSON.set_decoder_resolver(
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