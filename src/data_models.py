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


class Config(BaseModel):
    car_id: int
    index_page: str
    start_latitude: float
    start_longitude: float
    start_time: pendulum.DateTime
    hours: int

    status_formatted_fields_file: Optional[str]
    status_formatted_fields: Optional[LabelConfigDefinition]

    def post_process(self):
        if isinstance(self.start_time, datetime.datetime):
            self.start_time = pendulum.from_timestamp(self.start_time.timestamp(), tz='utc')

    def load_sub_files(self, config_dir: str):
        if self.status_formatted_fields_file:
            p = os.path.join(config_dir, self.status_formatted_fields_file)
            self.status_formatted_fields = LabelConfigDefinition.parse_file(p)
