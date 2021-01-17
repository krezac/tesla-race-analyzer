from pydantic import BaseModel
from typing import Optional, List, Callable, Type, Dict, Any
import pendulum
import datetime
import os


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
    vertical_previous_laps: bool
    reverse_previous_laps: bool

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

class JsonLapListWrapper(BaseModel):
    __root__: List[JsonLabelGroup]


class JsonLapsResponse(BaseModel):
    # TODO migrate total to separate structure total: JsonLabelGroup
    previous: JsonLapListWrapper
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

    forecast_raw: Optional[Dict[str, Any]]
    forecast_formatted: Optional[JsonLabelGroup]
