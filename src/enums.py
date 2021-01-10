from enum import Enum


class LabelFormatGroupEnum(Enum):
    STATUS = 'status'
    MAP = 'map'
    TOTAL_LAP = 'total_lap'
    CURRENT_LAP = 'current_lap'
    PREVIOUS_LAPS = 'previous_laps'
    FORECAST = 'forecast'


class CalculatedFieldScopeEnum(Enum):
    STATUS = 'status'
    LAP_POINT = 'lap_point'
    LAP = 'lap'
    FORECAST = 'forecast'

