from typing import Optional, Dict, Any
import pendulum
from src.data_models import Configuration

import logging
logger = logging.getLogger(__name__)


def add_calculated_fields(*,
                          current_item: Dict[str, Any],
                          initial_status,
                          current_status,
                          position_list,
                          lap_list,
                          total,
                          charging_process_list,
                          forecast,
                          configuration: Configuration,
                          current_item_index: Optional[int],
                          now_dt: pendulum.DateTime):
    """
    Add hardcoded calculated fields into current_item
    Note the prototype is the same for all calculated functions even if all inputs are not used

    :param current_item:
    :param initial_status:
    :param current_status:
    :param position_list:
    :param lap_list:
    :param total:
    :param charging_process_list:
    :param forecast:
    :param configuration:
    :param current_item_index:
    :param now_dt: time to calculate data for.
    :return:
    """
    if not lap_list:
        return

    logger.info(f"{len(lap_list)} laps on forecast input")

    unfinished_lap = lap_list[-1] if lap_list and not lap_list[-1]['finished'] else None
    logger.debug(f"unfinished lap: {unfinished_lap is not None}")

    car_laps = lap_list[:-1]
    if not car_laps:
        return None
    logger.info(f"{len(car_laps)} laps to analyze")

    start_time = configuration.start_time
    end_time = configuration.start_time.add(hours=configuration.hours)
    time_since_start = now_dt - start_time if now_dt > start_time else pendulum.period(now_dt, now_dt)
    time_to_end = end_time - now_dt if now_dt < end_time else pendulum.period(now_dt, now_dt)
    distance_since_start = \
        current_status['distance'] if current_status and 'distance' in current_status and current_status['distance'] is not None else 0.0

    # print(f"from start: {time_since_start.in_hours()}, to end: {time_to_end.in_hours()}, dist: {distance_since_start}")

    avg_lap_time = pendulum.Period(now_dt, now_dt)
    avg_pit_time = pendulum.Period(now_dt, now_dt)
    avg_lap_distance = 0
    for lap in car_laps:
        avg_lap_time += lap['lap_duration']
        avg_pit_time += lap['pit_duration']
        avg_lap_distance += lap['distance']
    logger.info(f"sum lap time {avg_lap_time}, sum lap distance {avg_lap_distance}")
    avg_lap_time /= len(car_laps)
    avg_pit_time /= len(car_laps)
    avg_lap_distance /= len(car_laps)
    # print(f"avg lap time {avgLapTime}, avg pit time: {avgPitTime}, avg lap distance {avgLapDistance}")
    # print(f"avg lap time {avgLapTime}, avg lap distance {avgLapDistance}")

    unfinished_lap_remaining_time = pendulum.Period(now_dt, now_dt)
    unfinished_lap_remaining_distance = 0
    # calculate time and dist for the unfinished lap
    # print(f"unfinished lap duration {unfinished_lap.duration} vs avg {avgLapTime}")
    if unfinished_lap and unfinished_lap['lap_duration'] < avg_lap_time:
        unfinished_lap_remaining_time = avg_lap_time - unfinished_lap['lap_duration']
    # print(f"unfinished lap time remaining time: {unfinished_lap_remaining_time}")
    if unfinished_lap and unfinished_lap['distance'] < avg_lap_distance:
        unfinished_lap_remaining_distance = avg_lap_distance - unfinished_lap['distance']
    # print(f"unfinished lap time remaining distance: {unfinished_lap_remaining_time}")

    time_to_forecast = time_to_end
    if unfinished_lap_remaining_time:
        time_to_forecast -= unfinished_lap_remaining_time
    # print(f"time to forecast: {timeToForecast.in_hours()}")
    full_laps_remaining = int(time_to_forecast / (avg_lap_time + avg_pit_time))
    # print(f"laps to go: {fullLapsRemaining}")
    remaining_last_lap_time = time_to_forecast - full_laps_remaining * (avg_lap_time + avg_pit_time)  # time left after max possible full laps
    # print(f"last lap time: {remaining_last_lap_time}")
    coef = remaining_last_lap_time / (avg_lap_time + avg_pit_time)
    # print(f"coef: {coef}")
    last_lap_duration = avg_lap_time * coef
    # print(f"last lap duration: {last_lap_duration}")
    last_pit_duration = avg_pit_time * coef
    # print(f"last pit duration : {last_pit_duration}")
    last_lap_distance = avg_lap_distance * coef
    # print(f"last lap distance: {last_lap_distance}")

    total_estimated_distance = distance_since_start + unfinished_lap_remaining_distance + full_laps_remaining * avg_lap_distance + last_lap_distance
    # print(f"total estimated distance: {total_estimated_distance}")

    current_item['avg_lap_duration'] = avg_lap_time
    current_item['avg_pit_duration'] = avg_pit_time
    current_item['avg_full_duration'] = avg_lap_time + avg_pit_time
    current_item['avg_lap_distance'] = avg_lap_distance
    current_item['unfinished_lap_remaining_time'] = unfinished_lap_remaining_time
    current_item['unfinished_lap_remaining_distance'] = unfinished_lap_remaining_distance
    current_item['full_laps_remaining'] = full_laps_remaining
    current_item['last_lap_duration'] = last_lap_duration
    current_item['last_pit_duration'] = last_pit_duration
    current_item['last_full_duration'] = last_lap_duration + last_pit_duration
    current_item['last_lap_distance'] = last_lap_distance
    current_item['total_estimated_distance'] = total_estimated_distance

    # add best lap metric (best full avg speed
    best_lap_id = None
    best_avg_speed = 0
    best_full_duration = time_since_start
    best_lap_distance = 0
    for lap in car_laps:
        if 'full_avg_speed' in lap and lap['full_avg_speed'] > best_avg_speed:
            best_avg_speed = lap['full_avg_speed']
            best_lap_id = lap['lap_id']
            best_full_duration = lap['full_duration']
            best_lap_distance = lap['distance']
    current_item['best_lap'] = best_lap_id

    best_full_laps_remaining = int(time_to_forecast / best_full_duration)
    # print(f"laps to go: {fullLapsRemaining}")
    best_remaining_last_lap_time = time_to_forecast - best_full_laps_remaining * best_full_duration  # time left after max possible full laps
    # print(f"last lap time: {remaining_last_lap_time}")
    best_coef = best_remaining_last_lap_time / best_full_duration
    # print(f"coef: {coef}")
    best_last_lap_distance = best_lap_distance * best_coef
    # print(f"last lap distance: {last_lap_distance}")

    best_estimated_distance = distance_since_start + unfinished_lap_remaining_distance + best_full_laps_remaining * best_lap_distance + best_last_lap_distance
    current_item['best_estimated_distance'] = best_estimated_distance
