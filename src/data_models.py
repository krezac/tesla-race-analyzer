from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pendulum
import datetime


class DatabaseFieldDescription(BaseModel):
    name: str
    description: Optional[str]
    return_type: Optional[str]


class CalculatedFieldDescription(DatabaseFieldDescription):
    calc_fn: Optional[str]


class FieldDescriptionList(BaseModel):
    items: List[DatabaseFieldDescription]


class Configuration(BaseModel):
    anonymous_index_page: str
    admin_index_page: str
    car_id: int
    start_latitude: float
    start_longitude: float
    start_time: pendulum.DateTime
    hours: int
    start_radius: float
    merge_from_lap: float
    laps_merged: float
    show_previous_laps: int
    previous_laps_table_vertical: bool
    previous_laps_table_reversed: bool

    charging_table_vertical: bool
    charging_table_reversed: bool

    forecast_exclude_first_laps: int
    forecast_use_last_laps: int

    update_run_background: bool
    update_status_seconds: int
    update_laps_seconds: int

    def post_process(self):
        if isinstance(self.start_time, datetime.datetime):
            self.start_time = pendulum.from_timestamp(self.start_time.timestamp(), tz='utc')


#####################################
# structures for AJAX API endpoints #
#####################################

class JsonLabelItem(BaseModel):
    """formatted label"""
    label: str
    value: Optional[str]


class JsonLabelGroup(BaseModel):
    """group of labels with title"""
    title: Optional[str]
    record_id: Optional[str]
    items: List[JsonLabelItem]


class JsonStatusResponse(BaseModel):
    lat: float
    lon: float
    mapLabels: JsonLabelGroup
    statusLabels: JsonLabelGroup
    totalLabels: JsonLabelGroup
    forecastLabels: JsonLabelGroup


class JsonResponseListWrapper(BaseModel):
    __root__: List[JsonLabelGroup]


class JsonLapsResponse(BaseModel):
    # TODO migrate total to separate structure total: JsonLabelGroup
    previous: JsonResponseListWrapper
    recent: Optional[JsonLabelGroup]


class JsonStaticSnapshot(BaseModel):
    initial_status_raw: Optional[Dict[str, Any]]

    current_status_raw: Optional[Dict[str, Any]]
    current_status_formatted: Optional[JsonStatusResponse]

    car_positions_raw: Optional[List[Dict[str, Any]]]

    lap_list_raw: Optional[List[Dict[str, Any]]]
    lap_list_formatted: Optional[JsonLapsResponse]

    total_raw: Optional[Dict[str, Any]]
    total_formatted: Optional[JsonLabelGroup]

    charging_process_list_raw: Optional[List[Dict[str, Any]]]
    charging_process_list_formatted: Optional[JsonResponseListWrapper]

    forecast_raw: Optional[Dict[str, Any]]
    forecast_formatted: Optional[JsonLabelGroup]

########################
# to serialize/deserialize config


class FieldScopeApi(BaseModel):
    code: str
    title: Optional[str]

    class Config:
        orm_mode = True


class FieldScopeApiList(BaseModel):
    __root__: List[FieldScopeApi]


class CalculatedFieldApi(BaseModel):
    name: str
    description: Optional[str]
    return_type: str
    calc_fn: str

    class Config:
        orm_mode = True


class CalculatedFieldApiList(BaseModel):
    title: Optional[str]
    items: List[CalculatedFieldApi]


class CalculatedFieldApiDict(BaseModel):
    __root__: Dict[str, CalculatedFieldApiList]


class LabelGroupApi(BaseModel):
    code: str
    title: Optional[str]

    class Config:
        orm_mode = True


class LabelGroupApiList(BaseModel):
    __root__: List[LabelGroupApi]


class LabelFormatApi(BaseModel):
    field: str
    label: Optional[str]
    format_function: Optional[str]
    format: Optional[str]
    unit: Optional[str]
    default: Optional[str]

    class Config:
        orm_mode = True


class LabelFormatApiList(BaseModel):
    title: Optional[str]
    items: List[LabelFormatApi]


class LabelFormatApiDict(BaseModel):
    __root__: Dict[str, LabelFormatApiList]


class DriverApi(BaseModel):
    name: str

    class Config:
        orm_mode = True


class DriverApiList(BaseModel):
    __root__: Optional[List[DriverApi]]


class DriverChangeApi(BaseModel):
    driver: str
    copilot: Optional[str]
    valid_from: pendulum.DateTime
    valid_to: Optional[pendulum.DateTime]

    class Config:
        orm_mode = True


class DriverChangeApiList(BaseModel):
    __root__: Optional[List[DriverChangeApi]]


class ConfigBackupData(BaseModel):
    configuration: Optional[Configuration]
    calculated_fields: Optional[Dict[str, CalculatedFieldApiList]]
    label_formats: Optional[Dict[str, LabelFormatApiList]]
    drivers: Optional[DriverApiList]
    driver_changes: Optional[DriverChangeApiList]
