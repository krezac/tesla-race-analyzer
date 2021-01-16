from typing import List, Dict, Any
import pendulum
import logging

from src.data_models import JsonLabelItem

logger = logging.getLogger('app.car_data')



def format_fn_float(raw_value: float, format_str: str, now_dt: pendulum.DateTime) -> str:
    return format_str % raw_value if format_str else str(raw_value)


def format_fn_period(raw_value: pendulum.Period, _format_str: str, now_dt: pendulum.DateTime) -> str:
    if raw_value.days:
        return f"{raw_value.days} days, {raw_value.hours:02d}:{raw_value.minutes:02d}:{raw_value.remaining_seconds:02d}"
    else:
        return f"{raw_value.hours:02d}:{raw_value.minutes:02d}:{raw_value.remaining_seconds:02d}"


def format_fn_period_words(raw_value: pendulum.Period, _format_str: str, now_dt: pendulum.DateTime) -> str:
    return raw_value.in_words()


def format_fn_datetime(raw_value: pendulum.DateTime, format_str: str, now_dt: pendulum.DateTime) -> str:
    raw_value_tz = raw_value.in_tz('Europe/Paris')
    return raw_value_tz.format(format_str) if format_str else str(raw_value_tz)


def format_fn_eval(raw_value: pendulum.Period, format_str: str, now_dt: pendulum.DateTime) -> str:
    from src import configuration
    return str(eval(format_str, {}, {'configuration': configuration, 'raw_value': raw_value}))


def _format_value(raw_value, label_format, now_dt: pendulum.DateTime):
    if raw_value is None:
        return label_format.default
    if label_format.format_function:
        format_fn = globals()[label_format.format_function]
        if format_fn:
            return format_fn(raw_value, label_format.format, now_dt) + (label_format.unit if label_format.unit else '')

    return f"{raw_value}{label_format.unit if label_format.unit else ''}"


def _generate_label(label_format, data: Dict[str, Any], now_dt: pendulum.DateTime) -> JsonLabelItem:
    if not data or label_format.field not in data or data[label_format.field] is None:
        logger.error(f"field {label_format.field} does not exist in data_dict ({data}). Misconfiguration, please fix")
        return JsonLabelItem(label=label_format.label, value=label_format.default)  # misconfiguration
    value = _format_value(data[label_format.field], label_format, now_dt)
    return JsonLabelItem(label=label_format.label, value=value)


def generate_labels(label_format_list: List, data: Dict[str, Any], now_dt: pendulum.DateTime) \
        -> List[JsonLabelItem]:
    out = []
    for config_item in label_format_list:
        item = _generate_label(config_item, data, now_dt)
        if item:
            out.append(item)
    return out


def get_calc_functions() -> List[str]:
    import sys
    return [o for o in dir(sys.modules[__name__]) if o.startswith("format_fn_")]
