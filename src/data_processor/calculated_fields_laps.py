from typing import Optional, Callable, Dict, NamedTuple, List
from src.data_models import CalculatedFieldDescription


def calc_fn_distance(initial_status: NamedTuple, current_status: NamedTuple, lap: NamedTuple, lap_list: List[NamedTuple]) -> Optional[float]:
    #initial_odo = initial_status.odometer if 'odometer' in initial_status._fields else None
    #current_odo = current_status.odometer if 'odometer' in current_status._fields else None
    #return current_odo - initial_odo if current_odo is not None and initial_odo is not None else None
    return 123


_calculated_laps_fields: List[CalculatedFieldDescription] = [
    CalculatedFieldDescription(
        name='zza_distance',
        description="Lap Distance [km]",
        return_type="float",
        calc_fn="calc_fn_distance",
    ),
]


def get_calculated_fields_status():
    return _calculated_laps_fields
