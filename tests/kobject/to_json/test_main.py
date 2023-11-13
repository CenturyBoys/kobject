from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Dict
from uuid import UUID

from kobject import Kobject, ToJSON


@dataclass
class BaseA(Kobject):
    a_datetime: datetime


@dataclass
class BaseB:
    a_uuid: UUID


@dataclass
class BaseC(Kobject):
    a_int: int
    a_str: str
    a_list_of_int: List[int]
    a_tuple_of_bool: Tuple[bool]
    a_base_a: BaseA
    a_base_b: BaseB
    a_list_of_base_a: List[BaseA]
    a_dict_str_b: Dict[str, BaseB]


def test_to_dict():
    ToJSON.set_encoder_resolver(datetime, lambda value: str(value))
    ToJSON.set_encoder_resolver(BaseB, lambda value: {"a_uuid": str(value.a_uuid)})
    instance = BaseC(
        a_int=1,
        a_str="lala",
        a_list_of_int=[1, 2, 3],
        a_tuple_of_bool=(True,),
        a_base_a=BaseA(a_datetime=datetime.fromisoformat("2023-02-01 17:38:45.389426")),
        a_base_b=BaseB(a_uuid=UUID("1d9cf695-c917-49ce-854b-4063f0cda2e7")),
        a_list_of_base_a=[
            BaseA(a_datetime=datetime.fromisoformat("2023-02-01 17:38:45.389426"))
        ],
        a_dict_str_b={"a": BaseB(a_uuid=UUID("1d9cf695-c917-49ce-854b-4063f0cda2e7"))},
    )
    dict_representation = instance.dict()
    assert dict_representation == {
        "a_int": 1,
        "a_str": "lala",
        "a_list_of_int": [1, 2, 3],
        "a_tuple_of_bool": [
            True,
        ],
        "a_base_a": {"a_datetime": "2023-02-01 17:38:45.389426"},
        "a_base_b": {"a_uuid": "1d9cf695-c917-49ce-854b-4063f0cda2e7"},
        "a_list_of_base_a": [{"a_datetime": "2023-02-01 17:38:45.389426"}],
        "a_dict_str_b": {"a": {"a_uuid": "1d9cf695-c917-49ce-854b-4063f0cda2e7"}},
    }


def test_from_json():
    ToJSON.set_encoder_resolver(datetime, lambda value: str(value))
    ToJSON.set_encoder_resolver(BaseB, lambda value: {"a_uuid": str(value.a_uuid)})
    instance = BaseC(
        a_int=1,
        a_str="lala",
        a_list_of_int=[1, 2, 3],
        a_tuple_of_bool=(True,),
        a_base_a=BaseA(a_datetime=datetime.fromisoformat("2023-02-01 17:38:45.389426")),
        a_base_b=BaseB(a_uuid=UUID("1d9cf695-c917-49ce-854b-4063f0cda2e7")),
        a_list_of_base_a=[
            BaseA(a_datetime=datetime.fromisoformat("2023-02-01 17:38:45.389426"))
        ],
        a_dict_str_b={"a": BaseB(a_uuid=UUID("1d9cf695-c917-49ce-854b-4063f0cda2e7"))},
    )
    json_payload = (
        b'{"a_int": 1, "a_str": "lala", "a_list_of_int": [1, 2, 3], "a_tuple_of_bool": [true]'
        b', "a_base_a": {"a_datetime": "2023-02-01 17:38:45.389426"}, "a_base_b": {"a_uuid": '
        b'"1d9cf695-c917-49ce-854b-4063f0cda2e7"}, "a_list_of_base_a": [{"a_datetime": "2023-'
        b'02-01 17:38:45.389426"}], "a_dict_str_b": {"a": {"a_uuid": "1d9cf695-c917-49ce-854b'
        b'-4063f0cda2e7"}}}'
    )
    json_bytes = instance.to_json()
    assert json_bytes == json_payload
