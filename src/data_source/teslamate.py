import pendulum
from typing import Dict, Any
from sqlalchemy import text

from src import db


def _cursor_one_to_dict(resultproxy):
    d, a = {}, []
    for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return d


def get_car_status(car_id: int, dt: pendulum.DateTime) -> Dict[str, Any]:
    sql = text("select car.name as car_name, pos.* from positions pos JOIN cars car on pos.car_id = car.id WHERE car_id = :car_id AND usable_battery_level IS NOT NULL AND date < :dt order by date desc limit 1")

    resultproxy = db.get_engine(bind='teslamate').execute(sql, {'car_id': car_id, 'dt': dt})

    resp = _cursor_one_to_dict(resultproxy)
    return resp


