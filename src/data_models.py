from pydantic import BaseModel
from typing import Optional, List, Callable, Type
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


class LabelConfigItem(BaseModel):
    """ label definition (source, format...)"""
    field: str
    label: str
    format: Optional[str]
    format_function: Optional[str]
    unit: Optional[str]
    default: Optional[str]


class LabelConfigDefinition(BaseModel):
    title: Optional[str]
    items: List[LabelConfigItem]


class LabelItem(BaseModel):
    """formatted label"""
    label: str
    value: Optional[str]


class LabelGroup(BaseModel):
    """group of labels with totle"""
    title: Optional[str]
    items: List[LabelItem]


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

    def post_process(self):
        if isinstance(self.start_time, datetime.datetime):
            self.start_time = pendulum.from_timestamp(self.start_time.timestamp(), tz='utc')


class JsonStatusResponse(BaseModel):
    lat: float
    lon: float
    mapLabels: LabelGroup
    textLabels: LabelGroup
    forecastLabels: LabelGroup