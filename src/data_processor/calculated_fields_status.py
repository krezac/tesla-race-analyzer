from typing import Optional, Callable, Dict, NamedTuple, List
from src.data_models import CalculatedFieldDescription


def calc_fn_distance(initial_status: NamedTuple, current_status: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    initial_odo = initial_status.odometer if 'odometer' in initial_status._fields else None
    current_odo = current_status.odometer if 'odometer' in current_status._fields else None
    return current_odo - initial_odo if current_odo is not None and initial_odo is not None else None


def calc_fn_distance_double(initial_status: NamedTuple, current_status: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    dist = current_status.zza_distance if 'zza_distance' in current_status._fields else None
    return 2 * dist if dist is not None else None


def calc_fn_distance_quad(initial_status: NamedTuple, current_status: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    ddist = current_status.zza_distance_double if 'zza_distance_double' in current_status._fields else None
    return 2 * ddist if ddist is not None else None


_calculated_status_fields: List[CalculatedFieldDescription] = [
    CalculatedFieldDescription(
        name='zza_distance',
        description="Distance from start points [km]",
        return_type="float",
        calc_fn="calc_fn_distance",
    ),
    CalculatedFieldDescription(
        name='zza_distance_double',
        description="Double Distance from start points [km]",
        return_type="float",
        calc_fn="calc_fn_distance_double",
    ),
    CalculatedFieldDescription(
        name='zza_distance_quad',
        description="Quad Distance from start points [km]",
        return_type="float",
        calc_fn="calc_fn_distance_quad",
    ),
]


def get_calculated_fields_status():
    return _calculated_status_fields
