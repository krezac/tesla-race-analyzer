from typing import Optional, Dict, Any
import pendulum
from geopy.distance import distance as geopy_distance

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
    Note the prototype is the same for all calcul;ated functions even if all inputs are not used

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
    initial_odo = initial_status['odometer'] if 'odometer' in initial_status else None
    current_odo = current_item['odometer'] if 'odometer' in current_item else None
    start_time = configuration.start_time
    end_time = configuration.start_time.add(hours=configuration.hours)

    current_item['distance'] = current_odo - initial_odo if current_odo is not None and initial_odo is not None else None

    current_item['air_distance'] = geopy_distance(
        (configuration.start_latitude, configuration.start_longitude),
        (current_item['latitude'], current_item['longitude'])
        ).km if 'latitude' in current_item and current_item['latitude'] is not None \
                and 'longitude' in current_item and current_item['longitude'] is not None else None

    current_item['start_time'] = start_time
    current_item['end_time'] = end_time

    current_item['time_since_start'] = pendulum.period(start_time, now_dt, True) \
        if now_dt >= start_time else pendulum.period(now_dt, now_dt, True)
    current_item['time_to_end'] = pendulum.period(now_dt, end_time, True) \
        if now_dt <= end_time else pendulum.period(now_dt, now_dt, True)

    current_item['slow_data_age'] = pendulum.period(current_item['slow_data_date'], now_dt) \
        if current_item and 'slow_data_date' in current_item and current_item['slow_data_date'] else None
    current_item['fast_data_age'] = pendulum.period(current_item['fast_data_date'], now_dt) \
        if current_item and 'fast_data_date' in current_item and current_item['fast_data_date'] else None

    current_item['lap_number'] = lap_list[-1]['lap_id'] if lap_list else None
