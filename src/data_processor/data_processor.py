import pendulum
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
import src.data_source.teslamate
from src.data_processor.calculated_fields_status import get_calculated_fields_status
from src.data_processor.labels import generate_labels
from src.data_models import LabelGroup

from src import config  # imports global configuration

_initial_status = None
_current_status = None


def _retype_status(data):
    if not data or not isinstance(data, dict):
        return data
    # transform fields not json compatible
    for k, v in data.items():
        if isinstance(v, Decimal):
            data[k] = float(v)
        elif isinstance(v, datetime):
            data[k] = pendulum.from_timestamp(v.timestamp(), tz='utc')
    return data


def _calculate_fields(initial_status, current_status) -> Dict[str, Any]:
    calculated_fields = get_calculated_fields_status()
    new_fields = {}
    for name, fn in calculated_fields.items():
        new_fields[name] = fn(initial_status, current_status)
    return new_fields


def get_car_status(car_id: int, dt: pendulum.DateTime) -> Dict[str, Any]:
    global _initial_status
    global _current_status

    if not _initial_status:
        _initial_status = _retype_status(src.data_source.teslamate.get_car_status(car_id, pendulum.parse('2021-01-02T12:30:00', tz='utc')))  # TODO configurable
    _current_status = _retype_status(src.data_source.teslamate.get_car_status(car_id, dt))

    new_fields = _calculate_fields(_initial_status, _current_status)
    _current_status.update(new_fields)

    # TODO read from config
    _current_status["distance_double"] = eval("current_status['distance'] * 2 if 'distance' in current_status and current_status['distance'] is not None else None", {},  # no globals at all
                                              {  # explicitly allowed stuff local stuff only
                                                  'initial_status': _initial_status,
                                                  'current_status': _current_status,
                                              })

    return _current_status


def get_car_status_formatted(car_id: int, dt: pendulum.DateTime) -> LabelGroup:
    car_status = get_car_status(car_id, dt)
    items = generate_labels(config.status_formatted_fields.items, car_status)
    return LabelGroup(title=config.status_formatted_fields.title, items=items)
