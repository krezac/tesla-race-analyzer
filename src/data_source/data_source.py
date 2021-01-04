from abc import abstractmethod
import pendulum
from typing import Dict, Any


class AbstractDataSource:
    def __init__(self):
        pass

    @abstractmethod
    def get_car_status(self, dt: pendulum.DateTime) -> Dict[str, Any]:
        pass
