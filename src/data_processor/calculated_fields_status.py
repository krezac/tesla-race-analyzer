from typing import Optional, NamedTuple, List
import pendulum

from src.data_models import CalculatedFieldDescription
from src import config


def calc_fn_distance(initial_status: NamedTuple, current_status: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    initial_odo = initial_status.odometer if 'odometer' in initial_status._fields else None
    current_odo = current_status.odometer if 'odometer' in current_status._fields else None
    return current_odo - initial_odo if current_odo is not None and initial_odo is not None else None


def calc_fn_start_time(initial_status: NamedTuple, current_status: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    return config.start_time


def calc_fn_end_time(initial_status: NamedTuple, current_status: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    return config.start_time.add(hours=config.hours)


def calc_fn_time_since_start(initial_status: NamedTuple, current_status: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    start_time = config.start_time
    now = pendulum.now(tz='utc')
    return pendulum.period(start_time, now, True) if now >= start_time else pendulum.period(now, now, True)


def calc_fn_time_to_end(initial_status: NamedTuple, current_status: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    end_time = config.start_time.add(hours=config.hours)
    now = pendulum.now(tz='utc')
    return pendulum.period(now, end_time, True) if now <= end_time else pendulum.period(now, now, True)


_calculated_status_fields: List[CalculatedFieldDescription] = [
    CalculatedFieldDescription(
        name='zza_distance',
        description="Distance from start points [km]",
        return_type="float",
        calc_fn="calc_fn_distance",
    ),
    CalculatedFieldDescription(
        name='zza_start_time',
        description="Start time",
        return_type="pendulum.DateTime",
        calc_fn="calc_fn_start_time",
    ),
    CalculatedFieldDescription(
        name='zza_end_time',
        description="End time",
        return_type="pendulum.DateTime",
        calc_fn="calc_fn_end_time",
    ),
    CalculatedFieldDescription(
        name='zza_time_since_start',
        description="Time since start",
        return_type="pendulum.Period",
        calc_fn="calc_fn_time_since_start",
    ),
    CalculatedFieldDescription(
        name='zza_time_to_end',
        description="Time to end",
        return_type="pendulum.Period",
        calc_fn="calc_fn_time_to_end",
    ),
]


def get_calculated_fields_status():
    return _calculated_status_fields
