from typing import Optional, Dict, List, Any
import pendulum

from src.data_models import CalculatedFieldDescription
from src.data_models import Configuration


def add_calculated_fields(*,
                          current_item: Dict[str, Any],
                          initial_status,
                          current_status,
                          position_list,
                          lap_list,
                          total,
                          charging_process_list,
                          forecast,
                          configuration: Configuration,
                          current_item_index: Optional[int],
                          now_dt: pendulum.DateTime):
    """
    Add hardcoded calculated fields into current_item
    Note the prototype is the same for all calculated functions even if all inputs are not used

    :param current_item:
    :param initial_status:
    :param current_status:
    :param position_list:
    :param lap_list:
    :param total:
    :param charging_process_list:
    :param forecast:
    :param configuration:
    :param current_item_index:
    :param now_dt: time to calculate data for.
    :return:
    """

    lap_start_time: pendulum.DateTime = current_item['lap_data'][0]['date'] \
        if 'lap_data' in current_item and current_item['lap_data'] else None

    lap_end_time: pendulum.DateTime = current_item['lap_data'][-1]['date'] \
        if 'lap_data' in current_item and current_item['lap_data'] else None

    pit_start_time: pendulum.DateTime = current_item['pit_data'][0]['date'] \
        if 'pit_data' in current_item and current_item['pit_data'] else None

    pit_end_time: pendulum.DateTime = current_item['pit_data'][-1]['date'] \
        if 'pit_data' in current_item and current_item['pit_data'] else None

    distance: float = current_item['lap_data'][-1]['odometer'] - current_item['lap_data'][0]['odometer']  \
        if 'lap_data' in current_item and current_item['lap_data'] else None

    lap_duration: pendulum.Period = lap_end_time - lap_start_time if lap_end_time and lap_start_time else None
    pit_duration: pendulum.Period = pit_end_time - pit_start_time if pit_end_time and pit_start_time else None

    full_duration: pendulum.Period = None
    if lap_duration and pit_duration:
        full_duration = lap_duration + pit_duration
    elif lap_duration:
        full_duration = lap_duration
    else:
        full_duration = pit_duration

    lap_avg_speed: float = distance / lap_duration.total_seconds() * 3600 if distance is not None and lap_duration else None
    full_avg_speed: float = distance / full_duration.total_seconds() * 3600 if distance is not None and full_duration else None

    current_item['lap_start_time'] = lap_start_time
    current_item['lap_end_time'] = lap_end_time

    current_item['pit_start_time'] = pit_start_time
    current_item['pit_end_time'] = pit_end_time

    current_item['distance'] = distance

    current_item['lap_duration'] = lap_duration
    current_item['pit_duration'] = pit_duration
    current_item['full_duration'] = full_duration

    current_item['lap_avg_speed'] = lap_avg_speed
    current_item['full_avg_speed'] = full_avg_speed
