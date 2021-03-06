import pendulum
from typing import Dict, Any, List
from sqlalchemy import text
from src.utils import function_timer
from decimal import Decimal
from datetime import datetime, timezone


# these are to convert unfriendly data types (Decimal to float, datetime to DateTime)
def _retype_data_field(v):
    if isinstance(v, Decimal):
        return float(v)
    elif isinstance(v, datetime):
        utc_time = v.replace(tzinfo=timezone.utc)
        utc_timestamp = utc_time.timestamp()

        return pendulum.from_timestamp(utc_timestamp, tz='utc')
    return v


def _cursor_one_to_dict_list(resultproxy):
    a = []
    for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        d = {}
        for column, value in rowproxy.items():
            # build up the dictionary
            d[column] = _retype_data_field(value)
        a.append(d)
    return a


def _cursor_one_to_dict(resultproxy):
    l = _cursor_one_to_dict_list(resultproxy)
    return l[0] if l else {}


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
    resp['slow_data_date'] = resp['date'] if 'date' in resp else None

    if update_fast_data:
        sql = text("""select date, latitude, longitude, speed, power, odometer, elevation from positions 
                      WHERE car_id = :car_id AND date < :dt AND elevation IS NOT NULL 
                      order by date desc limit 1""")
        resultproxy = db.get_engine(bind='teslamate').execute(sql, {'car_id': car_id, 'dt': dt})
        resp2 = _cursor_one_to_dict(resultproxy)
        resp2['fast_data_date'] = resp2['date']  if 'date' in resp2 else None
        if resp is not None and resp2:
            resp.update(resp2)
    return resp


@function_timer()
def get_car_positions(car_id: int, dt_start: pendulum.DateTime, dt_end: pendulum.DateTime, update_fast_data: bool = True) -> List[Dict[str, Any]]:
    from src import db
    # get the full records  #####   AND usable_battery_level IS NOT NULL
    sql = text("""SELECT * FROM positions 
                  WHERE car_id = :car_id AND date >= :dt_start AND date <= :dt_end
                  AND usable_battery_level IS NOT NULL 
                  ORDER BY date""")
    resultproxy = db.get_engine(bind='teslamate').execute(sql, {'car_id': car_id, 'dt_start': dt_start, 'dt_end': dt_end})
    return _cursor_one_to_dict_list(resultproxy)


@function_timer()
def get_car_charging_processes(car_id: int, dt_from: pendulum.DateTime, dt_to: pendulum.DateTime) -> List[Dict[str, Any]]:
    from src import db
    # first get the charging processes itself
    sql = text("""SELECT * FROM charging_processes 
                  WHERE car_id = :car_id
                  AND (start_date BETWEEN (:dt_from - interval ':min minutes') AND (:dt_to + interval ':min minutes')) 
                  AND (end_date IS NULL OR end_date BETWEEN (:dt_from - interval ':min minutes') AND (:dt_to + interval ':min minutes'))
                  ORDER BY start_date""")
    resultproxy = db.get_engine(bind='teslamate').execute(sql, {'car_id': car_id, 'dt_from': dt_from, 'dt_to': dt_to, 'min': 5})  # safety margin TODO make configurable
    charging_processes = _cursor_one_to_dict_list(resultproxy)
    chp_id_list = [chp['id'] for chp in charging_processes]
    charging_processes_dict = {chp['id']: chp for chp in charging_processes}

    # and the aggregate charges data
    sql = text("""SELECT charging_process_id, 
    min(charger_power) as min_charger_power, avg(charger_power) as avg_charger_power, max(charger_power) as max_charger_power
    FROM charges 
    WHERE charging_process_id = ANY(:chp_id_list) GROUP BY charging_process_id""")
    resultproxy = db.get_engine(bind='teslamate').execute(sql, {'chp_id_list': chp_id_list})
    charges_list = _cursor_one_to_dict_list(resultproxy)

    # and now merge the data
    for item in charges_list:
        id = item['charging_process_id']
        charging_processes_dict[id].update(item)

    return charging_processes


@function_timer()
def get_car_charging_details(charging_process_id: int) -> List[
        Dict[str, Any]]:
    from src import db
    sql = text("""SELECT 
    date, battery_level, charge_energy_added, charger_actual_current, charger_power, 
    ideal_battery_range_km, outside_temp, rated_battery_range_km, usable_battery_level   
    FROM charges 
    WHERE charging_process_id = :chp_id ORDER BY date""")
    resultproxy = db.get_engine(bind='teslamate').execute(sql, {'chp_id': charging_process_id})
    return  _cursor_one_to_dict_list(resultproxy)


    return charging_processes
