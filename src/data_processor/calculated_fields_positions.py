from typing import Optional, List, Dict, Any
import pendulum

from src.data_models import CalculatedFieldDescription
from geopy.distance import distance as geopy_distance
from src.data_models import Configuration


def add_calculated_fields(*,
                          current_item: Dict[str, Any],
                          initial_status,
                          current_status,
                          position_list,
                          lap_list,
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
    :param forecast:
    :param configuration:
    :param current_item_index:
    :param now_dt: time to calculate data for.
    :return:
    """
    # because of amount of data don't add anything unless necessary

    # current_item['distance_start'] = geopy_distance(
    #     (configuration.start_latitude, configuration.start_longitude),
    #     (position_list[current_item_index]['latitude'], position_list[current_item_index]['longitude'])
    #     ).km if position_list[current_item_index]['latitude'] is not None \
    #     and position_list[current_item_index]['longitude'] is not None else None

    pass
