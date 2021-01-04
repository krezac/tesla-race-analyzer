from pydantic import BaseModel
from typing import Optional, List
import pendulum
import os


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
    start_latitude: float
    start_longitude: float
    start_time: pendulum.DateTime

    status_formatted_fields_file: Optional[str]
    status_formatted_fields: Optional[LabelConfigDefinition]

    def load_sub_files(self, config_dir: str):
        if self.status_formatted_fields_file:
            p = os.path.join(config_dir, self.status_formatted_fields_file)
            self.status_formatted_fields = LabelConfigDefinition.parse_file(p)
