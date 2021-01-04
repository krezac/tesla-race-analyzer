from typing import Optional, Callable, Dict

ODOMETER = "odometer"


def _get_distance(initial_status, current_status) -> Optional[float]:
    initial_odo = initial_status[ODOMETER] if ODOMETER in initial_status else None
    current_odo = current_status[ODOMETER] if ODOMETER in current_status else None
    return current_odo - initial_odo if current_odo is not None and initial_odo is not None else None


_calculated_status_fields: Dict[str, Callable] = {
    'distance': _get_distance
}


def get_calculated_fields_status():
    return _calculated_status_fields
