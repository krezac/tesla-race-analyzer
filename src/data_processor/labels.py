from typing import List, Dict, NamedTuple
import pendulum
import logging

from src.data_models import LabelConfigItem, LabelItem

logger = logging.getLogger('app.car_data')


def format_float_fn(raw_value: float, format_str: str) -> str:
    return format_str % raw_value if format_str else str(raw_value)


def format_period_fn(raw_value: pendulum.Period, _format_str: str) -> str:
    if raw_value.days:
        return f"{raw_value.days} days, {raw_value.hours:02d}:{raw_value.minutes:02d}:{raw_value.remaining_seconds:02d}"
    else:
        return f"{raw_value.hours:02d}:{raw_value.minutes:02d}:{raw_value.remaining_seconds:02d}"


def format_period_words_fn(raw_value: pendulum.Period, _format_str: str) -> str:
    return raw_value.in_words()


def format_datetime_fn(raw_value: pendulum.DateTime, format_str: str) -> str:
    raw_value_tz = raw_value.in_tz('Europe/Paris')
    return raw_value_tz.format(format_str) if format_str else str(raw_value_tz)


def _format_value(raw_value, config_item: LabelConfigItem):
    if raw_value is None:
        return config_item.default
    if config_item.format_function:
        format_fn = globals()[config_item.format_function]
        if format_fn:
            return format_fn(raw_value, config_item.format) + (config_item.unit if config_item.unit else '')

    return f"{raw_value}{config_item.unit if config_item.unit else ''}"


def _generate_label(config_item: LabelConfigItem, data: NamedTuple) -> LabelItem:
    raw_value = getattr(data, config_item.field)
    if raw_value is None:
        logger.error(f"field {config_item.field} does not exist in data_dict ({data}). Misconfiguration, please fix")
        return LabelItem(label=config_item.label, value=config_item.default)  # misconfiguration
    value = _format_value(raw_value, config_item)
    return LabelItem(label=config_item.label, value=value)


def generate_labels(config_items: List[LabelConfigItem], data: NamedTuple) -> List[LabelItem]:
    out = []
    for config_item in config_items:
        item = _generate_label(config_item, data)
        out.append(item)
    return out

