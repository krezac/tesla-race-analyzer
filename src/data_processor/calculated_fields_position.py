from typing import Optional, List, Dict, Any

from src.data_models import CalculatedFieldDescription
from geopy.distance import distance as geopy_distance
from src.data_models import Configuration


def calc_fn_distance_start(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                     lap_list, forecast, configuration: Configuration,
                           current_item_index: Optional[int]) -> Optional[float]:

    return geopy_distance(
        (configuration.start_latitude, configuration.start_longitude),
        (position_list[current_item_index]['latitude'], position_list[current_item_index]['longitude'])
    ).km if position_list[current_item_index]['latitude'] is not None \
            and position_list[current_item_index]['longitude'] is not None else None


_calculated_position_fields: List[CalculatedFieldDescription] = [
    CalculatedFieldDescription(
        name='distance_start',
        description="Distance from start [km]",
        return_type="float",
        calc_fn="calc_fn_distance_start",
    ),
]


def get_calculated_fields_position():
    return _calculated_position_fields
