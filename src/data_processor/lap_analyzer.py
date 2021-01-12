#!/usr/bin/env python

import pendulum

from geopy.distance import distance as geopy_distance
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import statistics
from src.data_models import Config
from src.utils import function_timer

class LapSplit(BaseModel):
    lapId: str
    pitEntryIdx: Optional[int]
    pitLeaveIdx: Optional[int]
    lapEntryIdx: Optional[int]
    lapLeaveIdx: Optional[int]

class LapStatus(BaseModel):
    """
    raw fields only
    """
    id: str  # string because of aggregating
    startTime: Optional[pendulum.DateTime]
    endTime: Optional[pendulum.DateTime]
    startTimePit: Optional[pendulum.DateTime]
    endTimePit: Optional[pendulum.DateTime]
    startOdo: Optional[float]
    endOdo: Optional[float]
    insideTemp: Optional[float]
    outsideTemp: Optional[float]


@function_timer()
def find_laps(configuration: Config, segment, region=10, min_time=5, start_idx=0) -> List[LapSplit]:
    """Return laps given latitude & longitude data.

    We assume that the first point defines the start and
    that the last point defines the end and that these are
    approximately at the same place.

    Parameters
    ----------
    segment : dict
        The data for the full track.
    region : float
        The region around the starting point which is used to
        define if we are passing through the starting point and
        begin a new lap.
    min_time : float
        This is the minimum time (in seconds) we should spend in the
        region before exiting. This will depend on the setting for region
        and the velocity for the activity.
    start_idx : integer
        The starting point for the first lap.

    """
    if not segment:  # race not started yet
        return []

    points = [(pt['latitude'], pt['longitude']) for pt in segment]
    start = (configuration.start_latitude, configuration.start_longitude) \
        if configuration.start_latitude is not None and configuration.start_longitude \
        else points[start_idx]
    time = [pt['date'] for pt in segment]
    # For locating the tracks, we look for point which are such that
    # we enter the starting region and pass through it.
    # For each point, find the distance to the starting region:
    distance = [geopy_distance(point, start) for point in points]
    #np.set_printoptions(suppress=True)
    # print(distance)

    # Now look for points where we enter the region:
    # We want to avoid cases where we jump back and forth across the
    # boundary, so we set a minimum time we should spend inside the
    # region.

    # let's assume we are in pit or at the lap already at start time

    lapId = 1
    splits = []
    pit_entry_idx = None
    lap_entry_idx = None
    current_split = None

    for i, dist in enumerate(distance):
        if i == start_idx:  # in fact that just skips the first one
            if distance[0] > region:  # already at lap, so create new one
                current_split = LapSplit(
                    lapId=lapId,
                    pitEntryIdx=start_idx,
                    pitLeaveIdx=start_idx,
                    lapEntryIdx=start_idx
                )
            else:  # in pit
                current_split = LapSplit(
                    lapId=lapId,
                    pitEntryIdx=start_idx,
                )
            splits.append(current_split)  # HACK
            lapId += 1
            continue
        if dist <= region:  # we are inside the pit
            if distance[i - 1] <= region:  # was in pit before
                if pit_entry_idx:  # not recorded yet
                    delta_t = time[i] - time[pit_entry_idx]
                    if min_time < delta_t.total_seconds() or (i == (len(distance) - 1)):  # check time in pit (if last point and in pit, create anyway
                        if current_split:  # long enough, dump the previous one to output list
                            current_split.lapLeaveIdx = pit_entry_idx
                            # HACK splits.append(current_split)
                        current_split = LapSplit(lapId=str(lapId), pitEntryIdx=pit_entry_idx)  # and create new one
                        splits.append(current_split)  # HACK
                        lapId += 1
                        pit_entry_idx = None
            else:  # entered the pit (left lap)
                pit_entry_idx = i  # remember entry, start measuring time
        else:  # outside of pit (on lap)
            if distance[i - 1] > region:  # was on lap before
                if lap_entry_idx:  # not recorded yet
                    delta_t = time[i] - time[lap_entry_idx]
                    if min_time < delta_t.total_seconds():  # check time in pit
                        if current_split:  # long enough, record switch to lap
                            current_split.pitLeaveIdx = lap_entry_idx
                            current_split.lapEntryIdx = lap_entry_idx
                        pit_entry_idx = None
            else:  # entered the lap (left pit)
                lap_entry_idx = i  # remember exit, start measuring time

    # HACK if current_split and current_split.lapEntryIdx:  # do not include the one having just pit time
    # HACK    splits.append(current_split)

    agg_splits = aggregate_splits(configuration, splits)

    # new
    statuses = extract_lap_statuses(configuration, agg_splits, segment)
    # TODO
    # if not agg_splits[-1].lapLeaveIdx or distance[agg_splits[-1].lapLeaveIdx] > region:
    #     statuses[-1]['finished'] = False  # outside of region
    return statuses


def aggregate_splits(configuration: Config, splits: List[LapSplit]) -> List[LapSplit]:
    agg_start = configuration.merge_from_lap
    agg_count = configuration.laps_merged

    if agg_count <= 1 or len(splits) <= agg_start:
        return splits

    agg_splits = []

    # copy the ones before start (1, 2, 3, ... agg_start - 1)
    for i in range(agg_start - 1):
        agg_splits.append(splits[i])

    group_count = (len(splits) - agg_start + 1) // agg_count
    for i in range(group_count):
        first = splits[agg_start - 1 + i * agg_count]
        last = splits[agg_start - 1 + (i + 1) * agg_count - 1]
        split = LapSplit(
            lapId=first.lapId + "-" + last.lapId,
            pitEntryIdx=first.pitEntryIdx,
            pitLeaveIdx=first.pitLeaveIdx,
            lapEntryIdx=first.lapEntryIdx,
            lapLeaveIdx=last.lapLeaveIdx
        )
        agg_splits.append(split)

    for i in range(agg_start + agg_count * group_count - 1, len(splits)):
        agg_splits.append(splits[i])
    return agg_splits


def extract_lap_statuses(configuration: Config, splits: List[LapSplit], segment: List) -> List[LapStatus]:
    out = []
    for split in splits:
        out.append(extract_lap_status(configuration, split, segment))
    return out


def extract_lap_status(configuration: Config, split: LapSplit, segment) -> LapStatus:
    """ Lap data from database:
    xx id |
    xx date           |
    xx latitude  |
    xx longitude |
    -- speed |
    -- power |
    xx odometer   |
    xx ideal_battery_range_km |
    xx battery_level |
    xx outside_temp |
    -- elevation |
    -- fan_status |
    -- driver_temp_setting |
    -- passenger_temp_set ting |
    -- is_climate_on |
    -- is_rear_defroster_on |
    -- is_front_defroster_on |
    -- car_id |
    -- drive_id |
    xx inside_temp |
    -- battery_heater |
    -- battery_heater_on |
    -- battery_heater_no_power |
    xx est_battery_range_km |
    xx rated_battery_range_km
    """

    lap_start = split.lapEntryIdx
    lap_stop = split.lapLeaveIdx + 1 if split.lapLeaveIdx else len(segment) - 1
    lap_data = segment[lap_start:lap_stop]

    pit_start = split.pitEntryIdx
    pit_stop = split.pitLeaveIdx + 1 if split.pitLeaveIdx else len(segment) - 1
    pit_data = segment[pit_start:pit_stop]

    # try to calculate real energy
    # real_energy = 0.0
    # for i in range(1, len(lap_data)):
    #     real_energy += (lap_data[i].power * pendulum.Period(lap_data[i-1].date, lap_data[i].date).total_seconds())/3600
    # # it's in kWs
    # real_energy_hour = real_energy / pendulum.Period(lap_data[0].date, lap_data[-1].date).seconds * 3600
    #
    # real_energy_km = real_energy / (lap_data[-1].odometer - lap_data[0].odometer) * 1000


    ls =  LapStatus(
        id=split.lapId,
        startTime=pendulum.instance(lap_data[0]['date'], 'utc') if split.lapEntryIdx is not None else None,
        endTime=pendulum.instance(lap_data[-1]['date'], 'utc') if split.lapEntryIdx is not None else None,

        startTimePit=pendulum.instance(pit_data[0]['date'], 'utc') if split.pitEntryIdx is not None else None,
        endTimePit=pendulum.instance(pit_data[-1]['date'], 'utc') if split.lapEntryIdx is not None else None,

        startOdo=lap_data[0]['odometer'] if split.lapEntryIdx is not None else None,
        endOdo=lap_data[-1]['odometer'] if split.lapEntryIdx is not None else None,  # to be able to show current lap

        insideTemp=statistics.mean([l['inside_temp'] for l in lap_data if l['inside_temp']]),
        outsideTemp=statistics.mean([l['outside_temp'] for l in lap_data if l['outside_temp']]),

        # startSOC=lap_data[0].usable_battery_level if split.lapEntryIdx is not None else None,
        # endSOC=lap_data[-1].usable_battery_level if split.lapEntryIdx is not None else None,
        #
        # startRangeIdeal=lap_data[0].ideal_battery_range_km if split.lapEntryIdx is not None else None,
        # endRangeIdeal=lap_data[-1].ideal_battery_range_km if split.lapEntryIdx is not None else None,
        #
        # startRangeEst=lap_data[0].est_battery_range_km if split.lapEntryIdx is not None else None,
        # endRangeEst=lap_data[-1].est_battery_range_km if split.lapEntryIdx is not None else None,
        #
        # startRangeRated=lap_data[0].rated_battery_range_km if split.lapEntryIdx is not None else None,
        # endRangeRated=lap_data[-1].rated_battery_range_km if split.lapEntryIdx is not None else None,
        #
        # consumptionRated=configuration.consumptionRated,
        # finished=True,  # will be cleared later if needed
        #
        # real_energy=real_energy,
        # real_energy_km=real_energy_km,
        # real_energy_hour=real_energy_hour,
    )
    return ls
