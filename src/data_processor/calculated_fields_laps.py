from typing import Optional, Dict, List, Any
from src.data_models import CalculatedFieldDescription
from src.data_models import Configuration


def calc_fn_lap_start_time(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                           lap_list, forecast, configuration: Configuration,
                           current_item_index: Optional[int]) -> Optional[float]:
    return current_item['lap_data'][0]['date'] if 'lap_data' in current_item and current_item['lap_data'] else None


def calc_fn_lap_end_time(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                         lap_list, forecast, configuration: Configuration,
                         current_item_index: Optional[int]) -> Optional[float]:
    return current_item['lap_data'][-1]['date'] if 'lap_data' in current_item and current_item['lap_data'] else None


def calc_fn_pit_start_time(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                           lap_list, forecast, configuration: Configuration,
                           current_item_index: Optional[int]) -> Optional[float]:
    return current_item['pit_data'][0]['date'] if 'pit_data' in current_item and current_item['pit_data'] else None


def calc_fn_pit_end_time(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                         lap_list, forecast, configuration: Configuration,
                         current_item_index: Optional[int]) -> Optional[float]:
    return current_item['pit_data'][-1]['date'] if 'pit_data' in current_item and current_item['pit_data'] else None


def calc_fn_distance(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                     lap_list, forecast, configuration: Configuration,
                     current_item_index: Optional[int]) -> Optional[float]:
    return current_item['lap_data'][-1]['odometer'] - current_item['lap_data'][0]['odometer']  \
        if 'lap_data' in current_item and current_item['lap_data'] else None


_calculated_laps_fields: List[CalculatedFieldDescription] = [
    CalculatedFieldDescription(
        name='lap_start_time',
        description="Lap Start Time",
        return_type="pendulum.DateTime",
        calc_fn="calc_fn_lap_start_time",
    ),
    CalculatedFieldDescription(
        name='lap_end_time',
        description="Lap End Time",
        return_type="pendulum.DateTime",
        calc_fn="calc_fn_lap_end_time",
    ),
    CalculatedFieldDescription(
        name='pit_start_time',
        description="Pit Start Time",
        return_type="pendulum.DateTime",
        calc_fn="calc_fn_pit_start_time",
    ),
    CalculatedFieldDescription(
        name='pit_end_time',
        description="Pit End Time",
        return_type="pendulum.DateTime",
        calc_fn="calc_fn_pit_end_time",
    ),
    CalculatedFieldDescription(
        name='distance',
        description="Lap Distance [km]",
        return_type="float",
        calc_fn="calc_fn_distance",
    ),
]


def get_calculated_fields_laps():
    return _calculated_laps_fields
