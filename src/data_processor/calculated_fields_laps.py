from typing import Optional, Dict, List, Any
from src.data_models import CalculatedFieldDescription
from src.data_models import Configuration


def calc_fn_distance(*, current_item: Dict[str, Any], initial_status, current_status, position_list,
                     lap_list, forecast, configuration: Configuration,
                     current_item_index: Optional[int]) -> Optional[float]:
    #initial_odo = initial_status.odometer if 'odometer' in initial_status._fields else None
    #current_odo = current_status.odometer if 'odometer' in current_status._fields else None
    #return current_odo - initial_odo if current_odo is not None and initial_odo is not None else None
    return 123


_calculated_laps_fields: List[CalculatedFieldDescription] = [
    CalculatedFieldDescription(
        name='distance',
        description="Lap Distance [km]",
        return_type="float",
        calc_fn="calc_fn_distance",
    ),
]


def get_calculated_fields_laps():
    return _calculated_laps_fields
