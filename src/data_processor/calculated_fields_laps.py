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
                          forecast,
                          total,
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
    :param forecast:
    :param total:
    :param configuration:
    :param current_item_index:
    :param now_dt: time to calculate data for.
    :return:
    """

    current_item['lap_start_time'] = current_item['lap_data'][0]['date'] \
        if 'lap_data' in current_item and current_item['lap_data'] else None
    current_item['lap_end_time'] = current_item['lap_data'][-1]['date'] \
        if 'lap_data' in current_item and current_item['lap_data'] else None

    current_item['pit_start_time'] = current_item['pit_data'][0]['date'] \
        if 'pit_data' in current_item and current_item['pit_data'] else None
    current_item['pit_end_time'] = current_item['pit_data'][-1]['date'] \
        if 'pit_data' in current_item and current_item['pit_data'] else None

    current_item['distance'] = current_item['lap_data'][-1]['odometer'] - current_item['lap_data'][0]['odometer']  \
        if 'lap_data' in current_item and current_item['lap_data'] else None
