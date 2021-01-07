import pendulum
from typing import Dict, Any, List, NamedTuple
from decimal import Decimal
from datetime import datetime
import src.data_source.teslamate
from src.data_processor.database_fields import get_database_fields_status
from src.data_processor.labels import generate_labels
from src.data_models import LabelGroup, DatabaseFieldDescription, CalculatedFieldDescription, FieldDescriptionList
from src.utils import function_timer
from collections import namedtuple

from src import config  # imports global configuration
import src.data_processor.calculated_fields_status

# TODO add background loading
_initial_status_raw = None

_current_status_raw = None
_current_status_formatted = None

_lap_list_raw = None
_lap_list_formatted = None


def _sum_nt_classes(*args):
    return namedtuple('_', ' '.join(sum(map(lambda t:t._fields, args), ())))


def _sum_nt_instances(*args):
    return _sum_nt_classes(*args)(*sum(args,()))


def _retype_data_field(v):
    if isinstance(v, Decimal):
        return float(v)
    elif isinstance(v, datetime):
        return pendulum.from_timestamp(v.timestamp(), tz='utc')
    return v


def _retype_tuple(t : NamedTuple):
    new_data = [_retype_data_field(d) for d in list(t)]
    return t._make(new_data)


def _retype_tuple_list(tl: List[NamedTuple]):
    return [_retype_tuple(t) for t in tl]


def _update_car_status():
    global _initial_status_raw
    global _initial_status_formatted
    global _current_status_raw
    global _current_status_formatted
    global _lap_list_raw

    now = pendulum.now(tz='utc')

    if not _initial_status_raw:
        _initial_status_raw = _retype_tuple(src.data_source.teslamate.get_car_status(config.car_id, config.start_time))
        #_initial_status = _retype_tuple(_initial_db_status)  # TODO configurable
    _current_status_raw = _retype_tuple(src.data_source.teslamate.get_car_status(config.car_id, now))
    #_current_status = _retype_tuple(_current_db_status)

    calculated_fields = src.data_processor.calculated_fields_status.get_calculated_fields_status()
    for field_description in calculated_fields:
        name = field_description.name
        fn = getattr(src.data_processor.calculated_fields_status, field_description.calc_fn)  # get calculate function
        value = fn(_initial_status_raw, _current_status_raw, _lap_list_raw)  # calculate new value
        row_type = namedtuple('row_type', [name])
        new_field_tuple = row_type(value)
        _current_status_raw = _sum_nt_instances(_current_status_raw, new_field_tuple)

    # TODO read from config
    # _current_status["distance_double"] = eval("current_status['distance'] * 2 if 'distance' in current_status and current_status['distance'] is not None else None", {},  # no globals at all
    #                                           {  # explicitly allowed stuff local stuff only
    #                                               'initial_status': _initial_status,
    #                                               'current_status': _current_status,
    #                                           })


@function_timer()
def _update_car_laps():
    global _lap_list_raw

    start = pendulum.parse('2021-01-02T12:30:00Z',tz='utc')

    _lap_list_raw = src.data_source.teslamate.get_car_positions(config.car_id, start, 24)
    _lap_list_raw = _retype_tuple_list(_lap_list_raw)


def get_car_status(dt: pendulum.DateTime) -> Dict[str, Any]:
    global _current_status_raw

    if not _current_status_raw:
        _update_car_status()

    return _current_status_raw


def get_car_laps(dt: pendulum.DateTime) -> Dict[str, Any]:
    global _lap_list_raw

    if not _lap_list_raw:
        _update_car_laps()

    return _lap_list_raw


def get_car_status_formatted(dt: pendulum.DateTime) -> LabelGroup:
    global _current_status_formatted

    if not _current_status_formatted:
        _update_car_status()

    items = generate_labels(config.status_formatted_fields.items, _current_status_formatted)
    return LabelGroup(title=config.status_formatted_fields.title, items=items)


def describe_status_fields() -> List[DatabaseFieldDescription]:
    global _current_status_raw

    if not _current_status_raw:
        _update_car_status()

    out = FieldDescriptionList(items=[])
    if not _current_status_raw:
        return out

    calculated_fields = src.data_processor.calculated_fields_status.get_calculated_fields_status()
    database_fields = get_database_fields_status()

    # remember the order (custom, hardcoded, db) as the names may be overridden
    for key in _current_status_raw:
        if key in calculated_fields:
            out.items.append(calculated_fields[key])
        elif key in database_fields:
            out.items.append(database_fields[key])
        else:
            # fallback
            out.items.append( DatabaseFieldDescription(name=key))

    return out

