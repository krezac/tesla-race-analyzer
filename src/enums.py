from enum import Enum


class LabelFormatGroupEnum(Enum):
    STATUS = 'status'
    MAP = 'map'
    TOTAL = 'total'
    RECENT_LAP = 'recent_lap'
    PREVIOUS_LAPS = 'previous_laps'
    FORECAST = 'forecast'
    CHARGING = 'charging'


class CalculatedFieldScopeEnum(Enum):
    STATUS = 'status'
    POSITION = 'position'
    TOTAL = 'total'
    LAP = 'lap'
    FORECAST = 'forecast'
    CHARGING = 'charging'
