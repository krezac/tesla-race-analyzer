import pytest
from collections import namedtuple
from src.data_processor.data_processor import _retype_tuple
from decimal import Decimal
from datetime import datetime
from pendulum import DateTime


def test_tuple_retype():
    row_type = namedtuple('row_type', ['a', 'b', 'c'])
    new_row = row_type(1, 2.0, 'tri')
    retyped_row = _retype_tuple(new_row)
    assert  new_row == retyped_row

    new_row = row_type(1.2, Decimal(2.3), datetime.now())
    retyped_row = _retype_tuple(new_row)
    assert  new_row == retyped_row