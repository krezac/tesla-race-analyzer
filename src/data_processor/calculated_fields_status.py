from typing import Optional, NamedTuple, List, Dict, Any
import pendulum
from geopy.distance import distance as geopy_distance

from src.data_models import CalculatedFieldDescription
from src.data_models import Configuration


def calc_fn_distance(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                     lap_list, forecast, configuration: Configuration,
                     current_item_index: Optional[int]) -> Optional[float]:
    initial_odo = initial_status['odometer'] if 'odometer' in initial_status else None
    current_odo = current_status['odometer'] if 'odometer' in current_status else None
    return current_odo - initial_odo if current_odo is not None and initial_odo is not None else None


def calc_fn_air_distance(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                         lap_list, forecast, configuration: Configuration,
                         current_item_index: Optional[int]) -> Optional[float]:
    return geopy_distance(
        (configuration.start_latitude, configuration.start_longitude),
        (current_status['latitude'], current_status['longitude'])
    ).km if current_status['latitude'] is not None and current_status['longitude'] is not None else None


def calc_fn_start_time(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                       lap_list, forecast, configuration: Configuration,
                       current_item_index: Optional[int]) -> Optional[float]:
    return configuration.start_time


def calc_fn_end_time(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                     lap_list, forecast, configuration: Configuration,
                     current_item_index: Optional[int]) -> Optional[float]:
    return configuration.start_time.add(hours=configuration.hours)


def calc_fn_time_since_start(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                             lap_list, forecast, configuration: Configuration,
                             current_item_index: Optional[int]) -> Optional[float]:
    start_time = configuration.start_time
    now = pendulum.now(tz='utc')
    return pendulum.period(start_time, now, True) if now >= start_time else pendulum.period(now, now, True)


def calc_fn_time_to_end(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                        lap_list, forecast, configuration: Configuration,
                        current_item_index: Optional[int]) -> Optional[float]:
    end_time = configuration.start_time.add(hours=configuration.hours)
    now = pendulum.now(tz='utc')
    return pendulum.period(now, end_time, True) if now <= end_time else pendulum.period(now, now, True)


def calc_fn_lap_number(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                       lap_list, forecast, configuration: Configuration,
                       current_item_index: Optional[int]) -> Optional[float]:
    return lap_list[-1]['id'] if lap_list else None


_calculated_status_fields: List[CalculatedFieldDescription] = [
    CalculatedFieldDescription(
        name='distance',
        description="Distance from start points [km]",
        return_type="float",
        calc_fn="calc_fn_distance",
    ),
    CalculatedFieldDescription(
        name='air_distance',
        description="Air Distance from start points [km]",
        return_type="float",
        calc_fn="calc_fn_air_distance",
    ),
    CalculatedFieldDescription(
        name='start_time',
        description="Start time",
        return_type="pendulum.DateTime",
        calc_fn="calc_fn_start_time",
    ),
    CalculatedFieldDescription(
        name='end_time',
        description="End time",
        return_type="pendulum.DateTime",
        calc_fn="calc_fn_end_time",
    ),
    CalculatedFieldDescription(
        name='time_since_start',
        description="Time since start",
        return_type="pendulum.Period",
        calc_fn="calc_fn_time_since_start",
    ),
    CalculatedFieldDescription(
        name='time_to_end',
        description="Time to end",
        return_type="pendulum.Period",
        calc_fn="calc_fn_time_to_end",
    ),
    CalculatedFieldDescription(
        name='lap_number',
        description="Lap Number",
        return_type="str",
        calc_fn="calc_fn_lap_number",
    ),
]


def get_calculated_fields_status():
    return _calculated_status_fields
