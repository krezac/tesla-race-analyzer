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
    POSITION = 'position'
    LAP = 'lap'
    FORECAST = 'forecast'

