from typing import Optional, NamedTuple, List

from src.data_models import CalculatedFieldDescription
from src import config
from geopy.distance import distance as geopy_distance


def calc_fn_distance_start(*, initial_status: NamedTuple, current_status: NamedTuple, position_list: List[NamedTuple], lap_list: List[NamedTuple], current_point_index) -> Optional[float]:

    return geopy_distance(
        (config.start_latitude, config.start_longitude),
        (position_list[current_point_index]['latitude'], position_list[current_point_index]['longitude'])
    ).km if position_list[current_point_index]['latitude'] is not None \
            and position_list[current_point_index]['longitude'] is not None else None


_calculated_position_fields: List[CalculatedFieldDescription] = [
    CalculatedFieldDescription(
        name='zza_distance_start',
        description="Distance from start [km]",
        return_type="float",
        calc_fn="calc_fn_distance_start",
    ),
]


def get_calculated_fields_position():
    return _calculated_position_fields
