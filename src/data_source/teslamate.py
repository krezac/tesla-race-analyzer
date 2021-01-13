import pendulum
from typing import Dict, Any, List
from sqlalchemy import text
from src.utils import function_timer


def _cursor_one_to_dict(resultproxy):
    d, a = {}, []
    for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return d


def _cursor_one_to_dict_list(resultproxy):
    d, a = {}, []
    for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return a


@function_timer()
def get_car_status(car_id: int, dt: pendulum.DateTime, update_fast_data: bool = True) -> Dict[str, Any]:
    # get the full record
    from src import db
    sql = text("""select car.name as car_name, pos.* from positions pos 
                  JOIN cars car on pos.car_id = car.id 
                  WHERE car_id = :car_id AND date < :dt  AND usable_battery_level IS NOT NULL 
                  order by date desc limit 1""")
    resultproxy = db.get_engine(bind='teslamate').execute(sql, {'car_id': car_id, 'dt': dt})
    resp = _cursor_one_to_dict(resultproxy)

    if update_fast_data:
        sql = text("""select date, latitude, longitude, speed, power, odometer, elevation from positions 
                      WHERE car_id = :car_id AND date < :dt AND elevation IS NOT NULL 
                      order by date desc limit 1""")
        resultproxy = db.get_engine(bind='teslamate').execute(sql, {'car_id': car_id, 'dt': dt})
        resp2 = _cursor_one_to_dict(resultproxy)
        if resp is not None and resp2:
            resp.update(resp2)
    return resp


@function_timer()
def get_car_positions(car_id: int, dt: pendulum.DateTime, hours: int, update_fast_data: bool = True) -> List[Dict[str, Any]]:
    from src import db
    # get the full records  #####   AND usable_battery_level IS NOT NULL
    sql = text("""SELECT * FROM positions 
                  WHERE car_id = :car_id AND date >= :dt AND date <= (:dt + interval ':hours hours')
                  AND usable_battery_level IS NOT NULL 
                  ORDER BY date""")
    resultproxy = db.get_engine(bind='teslamate').execute(sql, {'car_id': car_id, 'dt': dt, 'hours': hours})
    return _cursor_one_to_dict_list(resultproxy)


