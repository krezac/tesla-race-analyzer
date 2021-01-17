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

    current_item['duration'] = current_item['end_date'] - current_item['start_date'] \
        if 'start_date' in current_item and 'end_date' in current_item \
           and current_item['start_date'] and current_item['end_date'] else None

    current_item['efficiency'] = 100.0 * current_item['charge_energy_added'] / current_item['charge_energy_used'] \
        if 'charge_energy_added' in current_item and 'charge_energy_added' in current_item \
           and current_item['charge_energy_used'] and current_item['charge_energy_used'] else None
