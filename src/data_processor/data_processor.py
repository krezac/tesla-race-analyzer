import pendulum
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
import src.data_source.teslamate
from src.data_processor.database_fields import get_database_fields_status
from src.data_processor.labels import generate_labels
from src.data_models import LabelGroup, DatabaseFieldDescription, CalculatedFieldDescription, FieldDescriptionList, \
    JsonStatusResponse
from src.utils import function_timer, function_timer_block
from collections import namedtuple

from src.enums import LabelFormatGroupEnum, CalculatedFieldScopeEnum
from src import config  # imports global configuration
import src.data_processor.calculated_fields_status
import src.data_processor.calculated_fields_position
import src.data_processor.calculated_fields_laps
import src.data_processor.calculated_fields_forecast
from src.db_models import LabelFormat, CalculatedField
from src.data_processor import lap_analyzer

# TODO add background loading
_initial_status_raw = None

_current_status_raw = None
_current_status_formatted = None

_car_positions_raw = None

_lap_list_raw = None
_lap_list_formatted = None

_forecast_raw = None


def _retype_data_field(v):
    if isinstance(v, Decimal):
        return float(v)
    elif isinstance(v, datetime):
        return pendulum.from_timestamp(v.timestamp(), tz='utc')
    return v


def _retype_dict(d : Dict[str, Any]):
    for k, v in d.items():
        d[k] = _retype_data_field(v)


@function_timer()
def _retype_dict_list(data: List[Dict[str, Any]]):
    for d in data:
        _retype_dict(d)


def _add_hardcoded_calculated_field(field_description: CalculatedFieldDescription, current_item: Dict[str, Any],
                                    function_package, *,
                                    initial_status, current_status, position_list, lap_list, forecast,
                                    current_item_index: Optional[int]):
    name = field_description.name
    fn = getattr(function_package, field_description.calc_fn)  # get calculate function
    value = fn(current_item=current_item,
               initial_status=initial_status,
               current_status=current_status,
               position_list=position_list,
               lap_list=lap_list,
               forecast=forecast,
               current_item_index=current_item_index,
               )  # calculate new value
    current_item[name] = value


def _add_user_defined_calculated_field(field_description: CalculatedFieldDescription, current_item: Dict[str, Any], *,
                                       initial_status, current_status, position_list, lap_list, forecast,
                                       current_item_index: Optional[int]):
        name = field_description.name
        code = field_description.calc_fn
        value = eval(code, {}, {
            'current_item': current_item,
            'initial_status': initial_status,
            'current_status': current_status,
            'position_list': position_list,
            'lap_list': lap_list,
            'forecast': forecast,
            'current_item_index': current_item_index,
        })  # calculate new value
        current_item[name] = value


@function_timer()
def _update_car_status():
    global _initial_status_raw
    global _initial_status_formatted
    global _current_status_raw
    global _current_status_formatted
    global _car_positions_raw
    global _lap_list_raw
    global _forecast_raw

    now = pendulum.now(tz='utc')

    if not _initial_status_raw:
        _initial_status_raw = src.data_source.teslamate.get_car_status(config.car_id, config.start_time)
        _retype_dict(_initial_status_raw)
    _current_status_raw = src.data_source.teslamate.get_car_status(config.car_id, now)
    _retype_dict(_current_status_raw)

    # add hardcoded calculated fields
    calculated_fields = src.data_processor.calculated_fields_status.get_calculated_fields_status()
    for field_description in calculated_fields:
        _add_hardcoded_calculated_field(field_description, _current_status_raw,
                                        src.data_processor.calculated_fields_status,
                                        initial_status=_initial_status_raw,
                                        current_status=_current_status_raw,
                                        position_list=_car_positions_raw,
                                        lap_list=_lap_list_raw,
                                        forecast=_forecast_raw,
                                        current_item_index=None,
                                        )

    # add user-defined (db) calculated fields
    db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.STATUS.value)
    for field_description in db_calculated_fields:
        _add_user_defined_calculated_field(field_description, _current_status_raw,
                                           initial_status=_initial_status_raw,
                                           current_status=_current_status_raw,
                                           position_list=_car_positions_raw,
                                           lap_list=_lap_list_raw,
                                           forecast=_forecast_raw,
                                           current_item_index=None,
                                           )

    # now generate the formatted one
    formatted_map_items = generate_labels(LabelFormat.get_all_by_group(LabelFormatGroupEnum.MAP.value),
                                      _current_status_raw)

    formatted_status_items = generate_labels(LabelFormat.get_all_by_group(LabelFormatGroupEnum.STATUS.value),
                                      _current_status_raw)

    formatted_forecast_items = generate_labels(LabelFormat.get_all_by_group(LabelFormatGroupEnum.FORECAST.value),
                                      _current_status_raw)

    db_label_group_map = src.db_models.LabelGroup.query.filter_by(code=LabelFormatGroupEnum.MAP.value).first()
    db_label_group_status = src.db_models.LabelGroup.query.filter_by(code=LabelFormatGroupEnum.STATUS.value).first()
    db_label_group_forecast = src.db_models.LabelGroup.query.filter_by(code=LabelFormatGroupEnum.FORECAST.value).first()

    _current_status_formatted = JsonStatusResponse(
        lat=_current_status_raw['latitude'],
        lon=_current_status_raw['longitude'],
        mapLabels=LabelGroup(title=db_label_group_map.title, items=formatted_map_items),
        textLabels=LabelGroup(title=db_label_group_status.title, items=formatted_status_items),
        forecastLabels=LabelGroup(title=db_label_group_forecast.title, items=formatted_forecast_items))



@function_timer()
def _update_car_positions():
    global _initial_status_raw
    global _initial_status_formatted
    global _current_status_raw
    global _current_status_formatted
    global _car_positions_raw
    global _lap_list_raw
    global _forecast_raw

    _car_positions_raw = src.data_source.teslamate.get_car_positions(config.car_id, config.start_time, config.hours)
    _retype_dict_list(_car_positions_raw)

    # add calculated fields
    # !! note this operation is expensive as it runs on lot of records
    hardcoded_calculated_fields = src.data_processor.calculated_fields_position.get_calculated_fields_position()
    db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.POSITION.value)
    for pt in range(len(_car_positions_raw)):
        for field_description in hardcoded_calculated_fields:
            _add_hardcoded_calculated_field(field_description, _car_positions_raw[pt],
                                            src.data_processor.calculated_fields_position,
                                            initial_status=_initial_status_raw,
                                            current_status=_current_status_raw,
                                            position_list=_car_positions_raw,
                                            lap_list=_lap_list_raw,
                                            forecast=_forecast_raw,
                                            current_item_index=pt,
                                            )
        for field_description in db_calculated_fields:
            _add_user_defined_calculated_field(field_description, _car_positions_raw[pt],
                                               initial_status=_initial_status_raw,
                                               current_status=_current_status_raw,
                                               position_list=_car_positions_raw,
                                               lap_list=_lap_list_raw,
                                               forecast=_forecast_raw,
                                               current_item_index=None,
                                               )

    # now split to laps


@function_timer()
def _update_car_laps():
    global _initial_status_raw
    global _initial_status_formatted
    global _current_status_raw
    global _current_status_formatted
    global _car_positions_raw
    global _lap_list_raw
    global _forecast_raw

    if not _car_positions_raw:
        _update_car_positions()

    _lap_list_raw = lap_analyzer.find_laps(config, _car_positions_raw, config.start_radius, 0, 0)

    # add calculated fields
    hardcoded_calculated_fields = src.data_processor.calculated_fields_laps.get_calculated_fields_laps()
    db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.LAP.value)


    for idx in range(len(_lap_list_raw)):
        for field_description in hardcoded_calculated_fields:
            _add_hardcoded_calculated_field(field_description, _lap_list_raw[idx],
                                            src.data_processor.calculated_fields_laps,
                                            initial_status=_initial_status_raw,
                                            current_status=_current_status_raw,
                                            position_list=_car_positions_raw,
                                            lap_list=_lap_list_raw,
                                            forecast=_forecast_raw,
                                            current_item_index=idx,
                                            )
        for field_description in db_calculated_fields:
            _add_user_defined_calculated_field(field_description, _lap_list_raw[idx],
                                               initial_status=_initial_status_raw,
                                               current_status=_current_status_raw,
                                               position_list=_car_positions_raw,
                                               lap_list=_lap_list_raw,
                                               forecast=_forecast_raw,
                                               current_item_index=None,
                                               )


@function_timer()
def _update_forecast():
    global _initial_status_raw
    global _initial_status_formatted
    global _current_status_raw
    global _current_status_formatted
    global _car_positions_raw
    global _lap_list_raw
    global _forecast_raw

    forecast = {}

    # add hardcoded calculated fields
    calculated_fields = src.data_processor.calculated_fields_forecast.get_calculated_fields_forecast()
    for field_description in calculated_fields:
        _add_hardcoded_calculated_field(field_description, forecast,
                                        src.data_processor.calculated_fields_status,
                                        initial_status=_initial_status_raw,
                                        current_status=_current_status_raw,
                                        position_list=_car_positions_raw,
                                        lap_list=_lap_list_raw,
                                        forecast=_forecast_raw,
                                        current_item_index=None,
                                        )

    # add user-defined (db) calculated fields
    db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.FORECAST.value)
    for field_description in db_calculated_fields:
        _add_user_defined_calculated_field(field_description, forecast,
                                           initial_status=_initial_status_raw,
                                           current_status=_current_status_raw,
                                           position_list=_car_positions_raw,
                                           lap_list=_lap_list_raw,
                                           forecast=_forecast_raw,
                                           current_item_index=None,
                                           )

    _forecast_raw = forecast  # publish once ready

    # # now generate the formatted one
    # formatted_items = generate_labels(LabelFormat.get_all_by_group(LabelFormatGroupEnum.FORECAST.value),
    #                                   _forecast_raw)
    # _current_status_formatted = LabelGroup(title=config.status_formatted_fields.title, items=formatted_items)


def get_car_status(dt: pendulum.DateTime) -> Dict[str, Any]:
    global _current_status_raw

    # TODO for the development time, update on every try if not _current_status_raw:
    _update_car_status()

    return _current_status_raw


def get_car_positions(dt: pendulum.DateTime) -> Dict[str, Any]:
    global _car_positions_raw

    # TODO for the development time, update on every try if not _car_positions_raw:
    _update_car_positions()

    return _car_positions_raw


def get_car_laps(dt: pendulum.DateTime) -> Dict[str, Any]:
    global _lap_list_raw

    # TODO for the development time, update on every try if not _lap_list_raw:
    _update_car_laps()

    return _lap_list_raw


def get_forecast(dt: pendulum.DateTime) -> Dict[str, Any]:
    global _forecast_raw

    # TODO for the development time, update on every try if not _lap_list_raw:
    _update_forecast()

    return _forecast_raw


def get_car_status_formatted(dt: pendulum.DateTime) -> JsonStatusResponse:
    global _current_status_formatted

    # TODO for the development time, update on every try if not _current_status_formatted:
    _update_car_status()

    return _current_status_formatted


def describe_status_fields() -> List[DatabaseFieldDescription]:
    global _current_status_raw

    # TODO for the development time, update on every try if not _current_status_raw:
    _update_car_status()

    out = FieldDescriptionList(items=[])
    if not _current_status_raw:
        return out

    database_raw_fields = get_database_fields_status()
    hardcoded_calculated_fields = {cf.name: cf for cf in
                                   src.data_processor.calculated_fields_status.get_calculated_fields_status()}
    database_calculated_fields = {cf.name: cf for cf in
                                  CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.STATUS.value)}

    # remember the order (custom, hardcoded, db) as the names may be overridden
    for key in _current_status_raw:
        if key in hardcoded_calculated_fields:
            cf = hardcoded_calculated_fields[key]
            out.items.append(DatabaseFieldDescription(
                name=cf.name, description=cf.description, return_type=cf.return_type))
        elif key in database_raw_fields:
            out.items.append(database_raw_fields[key])
        elif key in database_calculated_fields:
            cf = database_calculated_fields[key]
            out.items.append(DatabaseFieldDescription(
                name=cf.name, description=cf.description, return_type=cf.return_type))
        else:
            # fallback
            out.items.append(DatabaseFieldDescription(name=key, description="__fallback__"))

    return out

