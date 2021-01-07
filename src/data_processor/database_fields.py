from typing import Optional, Callable, Dict
from src.data_models import DatabaseFieldDescription

_database_status_fields: Dict[str, DatabaseFieldDescription] = {
    'id': DatabaseFieldDescription(
        name='id',
        description="Record ID",
        return_type="int",
    )
}


def get_database_fields_status():
    return _database_status_fields
