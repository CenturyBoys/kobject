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