import pendulum
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel
import src.data_source.teslamate
from src.data_processor.labels import generate_labels
from src.data_models import Configuration, JsonLabelItem, JsonLabelGroup, JsonStatusResponse, JsonLapsResponse, JsonStaticSnapshot, JsonResponseListWrapper
from src.utils import function_timer

from src.enums import LabelFormatGroupEnum, CalculatedFieldScopeEnum
import src.data_processor.calculated_fields_positions
import src.data_processor.calculated_fields_laps
import src.data_processor.calculated_fields_forecast
from src.data_processor import lap_analyzer

import logging
logger = logging.getLogger(__name__)


class DataProcessor(BaseModel):
    """ just wrapper around cached data"""
    initial_status_raw: Optional[Dict[str, Any]]

    current_status_raw: Optional[Dict[str, Any]]
    current_status_formatted: Optional[JsonStatusResponse]

    car_positions_raw: Optional[List[Dict[str, Any]]]

    lap_list_raw: Optional[List[Dict[str, Any]]]
    lap_list_formatted: Optional[JsonLapsResponse]

    total_raw: Optional[Dict[str, Any]]
    total_formatted: Optional[JsonLabelGroup]

    charging_process_list_raw: Optional[List[Dict[str, Any]]]
    charging_process_list_formatted: Optional[JsonResponseListWrapper]

    forecast_raw: Optional[Dict[str, Any]]
    forecast_formatted: Optional[JsonLabelGroup]
    
    ################
    # data loaders #
    ################

    @function_timer()
    def _update_initial_status(self, car_id: int, start_time: pendulum.DateTime):
        """
        Load initial status
        Not meant to be called from outside
        :param car_id:  car id to load status for.
        :param start_time:  time to retrieve the status for.
        :return: retrieved data
        """
        return src.data_source.teslamate.get_car_status(car_id, start_time)

    def _set_driver_change(self, record, dt: pendulum.DateTime):
        from src.db_models import DriverChange
        driver_change = DriverChange.query.filter(
            (DriverChange.valid_from <= dt) & ((DriverChange.valid_to >= dt) | (DriverChange.valid_to == None))
        ).order_by(DriverChange.valid_from.desc()).first()
        record['driver_name'] = driver_change.driver if driver_change else None
        record['copilot_name'] = driver_change.copilot if driver_change else None

    @function_timer()
    def _load_status_raw(self, car_id: int, dt: pendulum.DateTime, *,
                         initial_status, _current_status=None, position_list, lap_list,
                         total, charging_process_list, forecast,
                         configuration: Configuration):

        status = src.data_source.teslamate.get_car_status(car_id, dt)
        # add driver change
        self._set_driver_change(status, dt)
        # update status by calculated fields
        return self._enhance_status(status, dt,
                                    initial_status=initial_status,
                                    _current_status=status,
                                    position_list=position_list,
                                    lap_list=lap_list,
                                    total=total,
                                    charging_process_list=charging_process_list,
                                    forecast=forecast,
                                    configuration=configuration,
                                    )

    @function_timer()
    def _load_positions(self, car_id: int, dt_start: pendulum.DateTime, dt_end: pendulum.DateTime, *,
                        initial_status, current_status, _position_list=None, lap_list, 
                        total, charging_process_list, forecast,
                        configuration: Configuration) \
            -> List[Dict[str, Any]]:
        positions = src.data_source.teslamate.get_car_positions(car_id, dt_start, dt_end)
        return self._enhance_positions(positions, dt_end,
                                       initial_status=initial_status,
                                       current_status=current_status,
                                       _position_list=positions,
                                       lap_list=lap_list,
                                       total=total,
                                       charging_process_list=charging_process_list,
                                       forecast=forecast,
                                       configuration=configuration,
                                    )

    @function_timer()
    def _load_laps(self, positions, dt: pendulum.DateTime, *,
                   initial_status, current_status, position_list, _lap_list=None, 
                   total, charging_process_list, forecast,
                   configuration: Configuration):
        # TODO convert to finder
        laps = lap_analyzer.find_laps(configuration, positions, configuration.start_radius, 0, 0)
        for lap in laps:
            if 'lap_data' in lap and lap['lap_data']:
                self._set_driver_change(lap, lap['lap_data'][0]['date'])
        laps = self._enhance_laps(laps, dt,
                                  initial_status=initial_status,
                                  current_status=current_status,
                                  position_list=position_list,
                                  _lap_list=laps,
                                  total=total,
                                  charging_process_list=charging_process_list,
                                  forecast=forecast,
                                  configuration=configuration,
                                  )
        return laps

    @function_timer()
    def _load_total(self, dt: pendulum.DateTime, *,
                   initial_status, current_status, position_list, lap_list, 
                    _total=None, charging_process_list, forecast,
                   configuration: Configuration):
        # TODO convert to finder
        total = {}
        total = self._enhance_total(total, dt,
                                    initial_status=initial_status,
                                    current_status=current_status,
                                    position_list=position_list,
                                    lap_list=lap_list,
                                    _total=total,
                                    charging_process_list=charging_process_list,
                                    forecast=forecast,
                                    configuration=configuration,
                                    )
        return total

    @function_timer()
    def _load_charging_processes(self, car_id: int, dt_start: pendulum.DateTime, dt_end: pendulum.DateTime, *,
                                 initial_status, current_status, position_list, lap_list, 
                                 total, _charging_process_list=None, forecast, 
                                 configuration: Configuration) \
            -> List[Dict[str, Any]]:
        charging_processes = src.data_source.teslamate.get_car_charging_processes(car_id, dt_start, dt_end)
        return self._enhance_charging_processes(charging_processes, dt_end,
                                                initial_status=initial_status,
                                                current_status=current_status,
                                                position_list=position_list,
                                                lap_list=lap_list,
                                                total=total,
                                                _charging_process_list=charging_processes,
                                                forecast=forecast,
                                                configuration=configuration,
                                               )

    @function_timer()
    def _load_forecast(self, dt: pendulum.DateTime, *,
                       initial_status, current_status, position_list, lap_list,
                       total, charging_process_list, _forecast=None,
                       configuration: Configuration):
        # TODO convert to finder
        forecast = {}

        # note that forecast doesn't care about all laps. So let's restrict it
        exclude_first_laps = configuration.forecast_exclude_first_laps
        use_last_laps = configuration.forecast_use_last_laps

        lap_list_for_forecast = []
        car_laps = [lap for lap in lap_list if lap['finished']]  # care only about finished lap
        logger.debug(f"{len(car_laps)} finished laps to analyze")

        if not lap_list or len(car_laps) < (use_last_laps + exclude_first_laps):
            logger.info(
                f"not enough laps ({len(car_laps)}/{len(lap_list)}) from {use_last_laps} + {exclude_first_laps} needed)")
        else:
            lap_list_for_forecast = lap_list[-use_last_laps:]
            if not lap_list[-1]['finished']:  # include the unfinished lap as it affects calculations
                lap_list_for_forecast.append(lap_list[-1])

        forecast = self._enhance_forecast(total, dt,
                                          initial_status=initial_status,
                                          current_status=current_status,
                                          position_list=position_list,
                                          lap_list=lap_list_for_forecast,  # note the limited list here
                                          total=total,
                                          charging_process_list=charging_process_list,
                                          _forecast=forecast,
                                          configuration=configuration,
                                          )
        return forecast

    #####################################
    # enhancers - add calculated fields #
    #####################################

    @classmethod
    def _add_user_defined_calculated_field(cls, field_description, current_item: Dict[str, Any], *,
                                           initial_status, current_status, position_list, lap_list, 
                                           total, charging_process_list, forecast,
                                           configuration: Configuration,
                                           current_item_index: Optional[int], now_dt: pendulum.DateTime):
        """
        Add database defined calculated fields to current_item  (helper, not to be called directly)
        :param field_description: this is of type CalculatedField. I don't want to import because of DB dependency
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
        :param now_dt:
        :return:
        """
        name = field_description.name
        code = field_description.calc_fn
        value = eval(code, {}, {
            'current_item': current_item,
            'initial_status': initial_status,
            'current_status': current_status,
            'position_list': position_list,
            'lap_list': lap_list,
            'total': total,
            'charging_process_list': charging_process_list,
            'forecast': forecast,
            'configuration': configuration,
            'current_item_index': current_item_index,
            'now_dt': now_dt
        })  # calculate new value
        current_item[name] = value

    @function_timer()
    def _enhance_status(self, status: Dict[str, Any], dt: pendulum.DateTime, *,
                        initial_status, _current_status=None, position_list, lap_list, 
                        total, charging_process_list, forecast, 
                        configuration: Configuration) -> Dict[str, Any]:
        """
        Add calculated fields to the status
        :param status:  data to enhance
        :return: the enhanced version (note it does in place enhancements, changes the parameter)
        """
        # add hardcoded calculated fields
        from src.data_processor.calculated_fields_status import add_calculated_fields
        add_calculated_fields(current_item=status,
                              initial_status=initial_status,
                              current_status=status,
                              position_list=position_list,
                              lap_list=lap_list,
                              total=total,
                              charging_process_list=charging_process_list,
                              forecast=forecast,
                              configuration=configuration,
                              current_item_index=None,
                              now_dt=dt
                              )

        # add user-defined (db) calculated fields
        from src.db_models import CalculatedField
        db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.STATUS.value)
        for db_calculated_field in db_calculated_fields:
            self._add_user_defined_calculated_field(db_calculated_field, status,
                                                    initial_status=initial_status,
                                                    current_status=status,
                                                    position_list=position_list,
                                                    lap_list=lap_list,
                                                    total=total,
                                                    charging_process_list=charging_process_list,
                                                    forecast=forecast,
                                                    configuration=configuration,
                                                    current_item_index=None,
                                                    now_dt=dt
                                                    )
            return status

    @function_timer()
    def _enhance_positions(self, positions: List[Dict[str, Any]], dt: pendulum.DateTime, *,
                           initial_status, current_status, _position_list=None, lap_list, 
                           total, charging_process_list, forecast,
                           configuration: Configuration) -> List[Dict[str, Any]]:
        # add calculated fields
        # !! note this operation is expensive as it runs on lot of records

        from src.data_processor.calculated_fields_positions import add_calculated_fields
        from src.db_models import CalculatedField
        db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.POSITION.value)
        for i in range(len(positions)):
            add_calculated_fields(current_item=positions[i],
                                  initial_status=initial_status,
                                  current_status=current_status,
                                  position_list=positions,
                                  lap_list=lap_list,
                                  total=total,
                                  charging_process_list=charging_process_list,
                                  forecast=forecast,
                                  configuration=configuration,
                                  current_item_index=i,
                                  now_dt=dt
                                  )
            for field_description in db_calculated_fields:
                self._add_user_defined_calculated_field(field_description, positions[i],
                                                        initial_status=initial_status,
                                                        current_status=current_status,
                                                        position_list=positions,
                                                        lap_list=lap_list,
                                                        total=total,
                                                        charging_process_list=charging_process_list,
                                                        forecast=forecast,
                                                        configuration=configuration,
                                                        current_item_index=i,
                                                        now_dt=dt,
                                                        )
        return positions

    @function_timer()
    def _enhance_laps(self, laps: List[Dict[str, Any]], dt: pendulum.DateTime, *,
                      initial_status, current_status, position_list, _lap_list=None, 
                      total, charging_process_list, forecast,
                      configuration: Configuration) -> List[Dict[str, Any]]:

        from src.data_processor.calculated_fields_laps import add_calculated_fields
        from src.db_models import CalculatedField
        db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.POSITION.value)
        for i in range(len(laps)):
            add_calculated_fields(current_item=laps[i],
                                  initial_status=initial_status,
                                  current_status=current_status,
                                  position_list=position_list,
                                  lap_list=laps,
                                  total=total,
                                  charging_process_list=charging_process_list,
                                  forecast=forecast,
                                  configuration=configuration,
                                  current_item_index=i,
                                  now_dt=dt
                                  )
            for field_description in db_calculated_fields:
                self._add_user_defined_calculated_field(field_description, laps[i],
                                                        initial_status=initial_status,
                                                        current_status=current_status,
                                                        position_list=position_list,
                                                        lap_list=laps,
                                                        total=total,
                                                        charging_process_list=charging_process_list,
                                                        forecast=forecast,
                                                        configuration=configuration,
                                                        current_item_index=i,
                                                        now_dt=dt,
                                                        )
        return laps

    @function_timer()
    def _enhance_total(self, total: Dict[str, Any], dt: pendulum.DateTime, *,
                       initial_status, current_status, position_list, lap_list,
                       _total=None, charging_process_list, forecast,
                       configuration: Configuration) -> Dict[str, Any]:
        """
        Add calculated fields for total
        :param total: data to enhance
        :return: the enhanced version (note it does in place enhancements, changes the parameter)
        """
        # add hardcoded calculated fields
        from src.data_processor.calculated_fields_total import add_calculated_fields
        add_calculated_fields(current_item=total,
                              initial_status=initial_status,
                              current_status=current_status,
                              position_list=position_list,
                              lap_list=lap_list,
                              total=total,
                              charging_process_list=charging_process_list,
                              forecast=forecast,
                              configuration=configuration,
                              current_item_index=None,
                              now_dt=dt
                              )

        # add user-defined (db) calculated fields
        from src.db_models import CalculatedField
        db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.TOTAL.value)
        for db_calculated_field in db_calculated_fields:
            self._add_user_defined_calculated_field(db_calculated_field, total,
                                                    initial_status=initial_status,
                                                    current_status=current_status,
                                                    position_list=position_list,
                                                    lap_list=lap_list,
                                                    total=total,
                                                    charging_process_list=charging_process_list,
                                                    forecast=forecast,
                                                    configuration=configuration,
                                                    current_item_index=None,
                                                    now_dt=dt
                                                    )
        return total

    @function_timer()
    def _enhance_charging_processes(self, charging_processes: List[Dict[str, Any]], dt: pendulum.DateTime, *,
                                    initial_status, current_status, position_list, lap_list, 
                                    total, forecast, _charging_process_list,
                                    configuration: Configuration) -> List[Dict[str, Any]]:
        """
        Add calculated fields for charigng processes
        :param forecast:
        :return: the enhanced version (note it does in place enhancements, changes the parameter)
        """
        from src.data_processor.calculated_fields_charges import add_calculated_fields
        from src.db_models import CalculatedField
        db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.POSITION.value)
        for i in range(len(charging_processes)):
            add_calculated_fields(current_item=charging_processes[i],
                                  initial_status=initial_status,
                                  current_status=current_status,
                                  position_list=position_list,
                                  lap_list=lap_list,
                                  total=total,
                                  charging_process_list=charging_processes,
                                  forecast=forecast,
                                  configuration=configuration,
                                  current_item_index=i,
                                  now_dt=dt
                                  )
            for field_description in db_calculated_fields:
                self._add_user_defined_calculated_field(field_description, charging_processes[i],
                                                        initial_status=initial_status,
                                                        current_status=current_status,
                                                        position_list=position_list,
                                                        lap_list=lap_list,
                                                        total=total,
                                                        charging_process_list=charging_processes,
                                                        forecast=forecast,
                                                        configuration=configuration,
                                                        current_item_index=i,
                                                        now_dt=dt,
                                                        )
        return charging_processes

    @function_timer()
    def _enhance_forecast(self, forecast: Dict[str, Any], dt: pendulum.DateTime, *,
                          initial_status, current_status, position_list, lap_list,
                          total, charging_process_list, _forecast=None,
                          configuration: Configuration) -> Dict[str, Any]:
        """
        Add calculated fields for forecast
        :param forecast:
        :return: the enhanced version (note it does in place enhancements, changes the parameter)
        """
        # add hardcoded calculated fields
        from src.data_processor.calculated_fields_forecast import add_calculated_fields
        add_calculated_fields(current_item=forecast,
                              initial_status=initial_status,
                              current_status=current_status,
                              position_list=position_list,
                              lap_list=lap_list,
                              total=total,
                              charging_process_list=charging_process_list,
                              forecast=forecast,
                              configuration=configuration,
                              current_item_index=None,
                              now_dt=dt
                              )

        # add user-defined (db) calculated fields
        from src.db_models import CalculatedField
        db_calculated_fields = CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.FORECAST.value)
        for db_calculated_field in db_calculated_fields:
            self._add_user_defined_calculated_field(db_calculated_field, forecast,
                                                    initial_status=initial_status,
                                                    current_status=current_status,
                                                    position_list=position_list,
                                                    lap_list=lap_list,
                                                    total=total,
                                                    charging_process_list=charging_process_list,
                                                    forecast=forecast,
                                                    configuration=configuration,
                                                    current_item_index=None,
                                                    now_dt=dt
                                                    )
        return forecast

    ##############
    # formatters #
    ##############

    @classmethod
    def _format_dict(cls, d: Dict[str, Any], label_group: LabelFormatGroupEnum,
                     dt: Optional[pendulum.DateTime], *, record_id: Optional[str] = None) -> JsonLabelGroup:
        """
        Generic function to format dict into group of labels
        :param d: data to be formatted
        :param label_group: group of labels/title
        :param dt:
        :param record_id: if provided, it's passed to the ui. i.e. for purpose of table headers
        :return: formatted structure
        """
        from src.db_models import LabelGroup, LabelFormat
        from src.data_processor.labels import generate_labels

        db_label_group: LabelGroup = src.db_models.LabelGroup.query.filter_by(code=label_group.value).first()
        formatted_items: List[JsonLabelItem] = generate_labels(LabelFormat.get_all_by_group(label_group.value),
                                                               d, dt)
        return JsonLabelGroup(title=db_label_group.title, items=formatted_items, record_id=record_id)

    def _load_status_formatted(self, status: Dict[str, Any], total: Dict[str, Any], forecast: Dict[str, Any],
                               dt: Optional[pendulum.DateTime]) -> JsonStatusResponse:
        return JsonStatusResponse(
            lat=status['latitude'],
            lon=status['longitude'],
            mapLabels=self._format_dict(status, LabelFormatGroupEnum.MAP, dt),
            statusLabels=self._format_dict(status, LabelFormatGroupEnum.STATUS, dt),
            totalLabels=self._format_dict(total, LabelFormatGroupEnum.TOTAL, dt),  # TODO partial hack
            forecastLabels=self._format_dict(forecast, LabelFormatGroupEnum.FORECAST, dt),
        )

    def _load_laps_formatted(self, laps: List[Dict[str, Any]], dt: Optional[pendulum.DateTime]) -> JsonLapsResponse:
        from src import configuration
        recent_lap = laps[-1] if laps else None
        prev_lap_list = laps[-configuration.show_previous_laps - 1:-1] if len(laps) > 0 else []

        formatted_prev_laps = [self._format_dict(lap, LabelFormatGroupEnum.PREVIOUS_LAPS, dt,
                                                 record_id=str(lap['lap_id'])) for lap in prev_lap_list]
        if configuration.previous_laps_table_reversed:
            formatted_prev_laps.reverse()
        formatted_recent_lap = self._format_dict(recent_lap, LabelFormatGroupEnum.RECENT_LAP, dt,
                                                 record_id=str(recent_lap['lap_id'])) if recent_lap else None

        return JsonLapsResponse(
            previous=JsonResponseListWrapper(__root__=formatted_prev_laps),
            recent=formatted_recent_lap
        )

    def _load_charging_process_list_formatted(self, charging_process_list: List[Dict[str, Any]],
                                              dt: Optional[pendulum.DateTime]) -> JsonResponseListWrapper:
        from src import configuration
        formatted_list = [self._format_dict(chp, LabelFormatGroupEnum.CHARGING, dt, record_id=str(rec_id))
                          for rec_id, chp in enumerate(charging_process_list, start=1)]  # simulate id using index

        if configuration.charging_table_reversed:
            formatted_list.reverse()

        return JsonResponseListWrapper(
            __root__=formatted_list
        )

    #################################################
    # update calls (to be used from background jobs #
    #################################################

    @function_timer()
    def update_status(self):
        """
        update current status. May be called from background job
        """
        from src import configuration
        car_id = configuration.car_id
        now = pendulum.now(tz='utc')

        if not self.initial_status_raw:
            self.initial_status_raw = self._update_initial_status(car_id, configuration.start_time)  # make sure there is initial status loaded

        status = self._load_status_raw(car_id, now,
                                       initial_status=self.initial_status_raw,
                                       _current_status=self.current_status_raw,
                                       position_list=self.car_positions_raw,
                                       lap_list=self.lap_list_raw,
                                       total=self.total_raw,
                                       charging_process_list=self.charging_process_list_raw,
                                       forecast=self.forecast_raw,
                                       configuration=configuration, )
        self.current_status_raw = status

        # just to make sure all data exist before rendering if no bg jobs are allowed
        if not configuration or not self.total_raw or not self.forecast_raw:
            self.update_positions_laps_forecast()

        self.current_status_formatted = self._load_status_formatted(self.current_status_raw, self.total_raw,
                                                                    self.forecast_raw, now)

    @function_timer()
    def update_positions_laps_forecast(self):
        """
        update rest of the data (besides status. May be called from background job
        """
        from src import configuration

        now = pendulum.now(tz='utc')
        dt_end = configuration.start_time.add(hours=configuration.hours)
        positions = self._load_positions(
            configuration.car_id, configuration.start_time, dt_end,
            initial_status=self.initial_status_raw,
            current_status=self.current_status_raw,
            _position_list=self.car_positions_raw,
            lap_list=self.lap_list_raw,
            total=self.total_raw,
            charging_process_list=self.charging_process_list_raw,
            forecast=self.forecast_raw,
            configuration=configuration, )
        self.car_positions_raw = positions
        # no formatting for positions

        # find and update laps
        self.lap_list_raw = self._load_laps(
            positions, now,
            initial_status=self.initial_status_raw,
            current_status=self.current_status_raw,
            position_list=self.car_positions_raw,
            _lap_list=self.lap_list_raw,
            total=self.total_raw,
            charging_process_list=self.charging_process_list_raw,
            forecast=self.forecast_raw,
            configuration=configuration,
            )

        # load charging
        self.charging_process_list_raw = self._load_charging_processes(
            configuration.car_id, configuration.start_time, dt_end,
            initial_status=self.initial_status_raw,
            current_status=self.current_status_raw,
            position_list=self.car_positions_raw,
            lap_list=self.lap_list_raw,
            total=self.total_raw,
            _charging_process_list=self.charging_process_list_raw,
            forecast=self.forecast_raw,
            configuration=configuration,
            )

        # load total
        self.total_raw = self._load_total(
            now,
            initial_status=self.initial_status_raw,
            current_status=self.current_status_raw,
            position_list=self.car_positions_raw,
            lap_list=self.lap_list_raw,
            _total=self.total_raw,
            charging_process_list=self.charging_process_list_raw,
            forecast=self.forecast_raw,
            configuration=configuration,
            )

        # load forecast
        self.forecast_raw = self._load_forecast(
            now,
            initial_status=self.initial_status_raw,
            current_status=self.current_status_raw,
            position_list=self.car_positions_raw,
            lap_list=self.lap_list_raw,
            total=self.total_raw,
            charging_process_list=self.charging_process_list_raw,
            _forecast=self.forecast_raw,
            configuration=configuration,
            )

        # just to make sure all data exist before rendering if no bg jobs are allowed
        if not configuration or not self.current_status_raw:
            self.update_status

        # generate the formatted form after, when all are updated
        self.lap_list_formatted = self._load_laps_formatted(self.lap_list_raw, now)
        self.charging_process_list_formatted = \
            self._load_charging_process_list_formatted(self.charging_process_list_raw, now)
        self.total_formatted = self._format_dict(self.total_raw, LabelFormatGroupEnum.TOTAL, now)
        self.forecast_formatted = self._format_dict(self.forecast_raw, LabelFormatGroupEnum.FORECAST, now)

    ###########
    # getters #
    ###########

    def get_status_raw(self) -> Dict[str, Any]:
        """
        get current status raw
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.current_status_raw:
            self.update_status()
        return self.current_status_raw

    def get_status_formatted(self) -> JsonStatusResponse:
        """
        get current status raw
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.current_status_formatted:
            self.update_status()
        out = self.current_status_formatted
        out.totalLabels = self.total_formatted  # TODO this is not nice hack
        return out

    def get_positions_raw(self) -> List[Dict[str, Any]]:
        """
        get current positions raw
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.car_positions_raw:
            self.update_positions_laps_forecast()
        return self.car_positions_raw

    def get_laps_raw(self) -> List[Dict[str, Any]]:
        """
        get laps raw form
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.lap_list_raw:
            self.update_positions_laps_forecast()
        return self.lap_list_raw

    def get_laps_formatted(self) -> JsonLapsResponse:
        """
        get laps formatted for UI
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.lap_list_formatted:
            self.update_positions_laps_forecast()
        return self.lap_list_formatted

    def get_total_raw(self) -> Dict[str, Any]:
        """
        get total raw
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.total_raw:
            self.update_positions_laps_forecast()
        return self.total_raw

    def get_total_formatted(self) -> JsonLabelGroup:
        """
        get total formatted
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.total_formatted:
            self.update_positions_laps_forecast()
        return self.total_formatted

    def get_charging_process_list_raw(self) -> List[Dict[str, Any]]:
        """
        get charging processes raw
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.charging_process_list_raw:
            self.update_positions_laps_forecast()
        return self.charging_process_list_raw

    def get_charging_process_list_formatted(self) -> JsonResponseListWrapper:
        """
        get charging processes formatted
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.charging_process_list_formatted:
            self.update_positions_laps_forecast()
        return self.charging_process_list_formatted

    def get_forecast_raw(self) -> Dict[str, Any]:
        """
        get forecast raw
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.forecast_raw:
            self.update_positions_laps_forecast()
        return self.forecast_raw

    def get_forecast_formatted(self) -> JsonLabelGroup:
        """
        get forecast formatted
        :return: retrieved data
        """
        from src import configuration
        if not configuration.update_run_background or not self.forecast_formatted:
            self.update_positions_laps_forecast()
        return self.forecast_formatted

    # TODO add charging in better way
    def get_car_chargings(self, lap_id: int):

        from src import configuration
        if not configuration.update_run_background or not self.lap_list_raw:
            self.update_positions_laps_forecast()

        lap = self.lap_list_raw[lap_id]
        pit_start = lap['pit_start_time']
        pit_end = lap['pit_end_time']
        from src import configuration  # imports global configuration
        return src.data_source.teslamate.get_car_chargings(configuration.car_id, pit_start, pit_end)

    ################################
    # static snapshot for datetime #
    ################################

    @function_timer()
    def get_static_snapshot(self, dt_end: pendulum.DateTime) -> JsonStaticSnapshot:
        """
        Get system snapshot for specific date and time
        :param dt_end:
        :return:
        """
        from src import configuration
        snapshot = JsonStaticSnapshot()
        snapshot.initial_status_raw = self._update_initial_status(configuration.car_id, configuration.start_time)
        for i in range(2):  # repeat twice in case there are dependent fields
            snapshot.current_status_raw = self._load_status_raw(
                configuration.car_id, dt_end,
                initial_status=snapshot.initial_status_raw,
                _current_status=snapshot.current_status_raw,
                position_list=snapshot.car_positions_raw,
                lap_list=snapshot.lap_list_raw,
                total=snapshot.total_raw,
                charging_process_list=snapshot.charging_process_list_raw,
                forecast=snapshot.forecast_raw,
                configuration=configuration,
                )
            snapshot.car_positions_raw = self._load_positions(
                configuration.car_id, configuration.start_time, dt_end,
                initial_status=snapshot.initial_status_raw,
                current_status=snapshot.current_status_raw,
                _position_list=snapshot.car_positions_raw,
                lap_list=snapshot.lap_list_raw,
                total=snapshot.total_raw,
                charging_process_list=snapshot.charging_process_list_raw,
                forecast=snapshot.forecast_raw,
                configuration=configuration,
                )

            snapshot.lap_list_raw = self._load_laps(
                snapshot.car_positions_raw, dt_end,
                initial_status=snapshot.initial_status_raw,
                current_status=snapshot.current_status_raw,
                position_list=snapshot.car_positions_raw,
                _lap_list=snapshot.lap_list_raw,
                total=snapshot.total_raw,
                charging_process_list=snapshot.charging_process_list_raw,
                forecast=snapshot.forecast_raw,
                configuration=configuration,
                )

            snapshot.charging_process_list_raw = self._load_charging_processes(
                configuration.car_id, configuration.start_time, dt_end,
                initial_status=snapshot.initial_status_raw,
                current_status=snapshot.current_status_raw,
                position_list=snapshot.car_positions_raw,
                lap_list=snapshot.lap_list_raw,
                total=snapshot.total_raw,
                _charging_process_list=snapshot.charging_process_list_raw,
                forecast=snapshot.forecast_raw,
                configuration=configuration,
                )

            snapshot.total_raw = self._load_total(
                dt_end,
                initial_status=snapshot.initial_status_raw,
                current_status=snapshot.current_status_raw,
                position_list=snapshot.car_positions_raw,
                lap_list=snapshot.lap_list_raw,
                _total=snapshot.total_raw,
                charging_process_list=snapshot.charging_process_list_raw,
                forecast=snapshot.forecast_raw,
                configuration=configuration,
                )

            snapshot.forecast_raw = self._load_forecast(
                dt_end,
                initial_status=snapshot.initial_status_raw,
                current_status=snapshot.current_status_raw,
                position_list=snapshot.car_positions_raw,
                lap_list=snapshot.lap_list_raw,
                total=snapshot.total_raw,
                charging_process_list=snapshot.charging_process_list_raw,
                _forecast=snapshot.forecast_raw,
                configuration=configuration,
                )

        snapshot.current_status_formatted = self._load_status_formatted(snapshot.current_status_raw,
                                                                        snapshot.total_raw,
                                                                        snapshot.forecast_raw, dt_end)
        snapshot.lap_list_formatted = self._load_laps_formatted(snapshot.lap_list_raw, dt_end)
        snapshot.charging_process_list_formatted = self._load_charging_process_list_formatted(
            snapshot.charging_process_list_raw, dt_end)
        snapshot.total_formatted = self._format_dict(snapshot.total_raw, LabelFormatGroupEnum.TOTAL, dt_end)
        snapshot.current_status_formatted.totalLabels = snapshot.total_formatted  # to pass it to appropriate spot
        snapshot.forecast_formatted = self._format_dict(snapshot.forecast_raw, LabelFormatGroupEnum.FORECAST, dt_end)

        return snapshot

    ####################
    # other UI helpers #
    ####################
    # Not needed any more
    # def describe_status_fields(self) -> List[DatabaseFieldDescription]:
    #     from src.db_models import LabelFormat, CalculatedField
    #
    #     # TODO for the development time, update on every try if not _current_status_raw:
    #     self.update_status()
    #
    #     out = FieldDescriptionList(items=[])
    #
    #     database_raw_fields = get_database_fields_status()
    #     hardcoded_calculated_fields = {cf.name: cf for cf in
    #                                    src.data_processor.calculated_fields_status.get_calculated_fields_status()}
    #     database_calculated_fields = {cf.name: cf for cf in
    #                                   CalculatedField.get_all_by_scope(CalculatedFieldScopeEnum.STATUS.value)}
    #
    #     # remember the order (custom, hardcoded, db) as the names may be overridden
    #     for key in self._current_status_raw:
    #         if key in hardcoded_calculated_fields:
    #             cf = hardcoded_calculated_fields[key]
    #             out.items.append(DatabaseFieldDescription(
    #                 name=cf.name, description=cf.description, return_type=cf.return_type))
    #         elif key in database_raw_fields:
    #             out.items.append(database_raw_fields[key])
    #         elif key in database_calculated_fields:
    #             cf = database_calculated_fields[key]
    #             out.items.append(DatabaseFieldDescription(
    #                 name=cf.name, description=cf.description, return_type=cf.return_type))
    #         else:
    #             # fallback
    #             out.items.append(DatabaseFieldDescription(name=key, description="__fallback__"))
    #
    #     return out

    def test_custom_calculated_field(self, field_name: str, scope_code: str, function_code: str, return_type: str) \
            -> Optional[Any]:
        from src.db_models import CalculatedField
        from src import configuration  # imports global configuration

        from src import configuration
        if not configuration.update_run_background or not self.current_status_raw:
            self.update_status()

        field = CalculatedField(
            id=-1, name=field_name, description="", return_type=return_type, calc_fn=function_code, scope_id=1   # TODO
        )
        current_item = {}

        # TODO generate current item and index based on the scope

        self._add_user_defined_calculated_field(field, current_item,
                                                initial_status=self.initial_status_raw,
                                                current_status=self.current_status_raw,
                                                position_list=self.car_positions_raw,
                                                lap_list=self.lap_list_raw,
                                                forecast=self.forecast_raw,
                                                current_item_index=None,
                                                configuration=configuration,
                                                now_dt=pendulum.now(tz='utc')
                                                )
        return current_item

    def test_custom_label_format(self, group_code: str, field: str, label: str, format_fn: str, format_str: str,
                                 unit: str, default: str) -> List[JsonLabelItem]:
        from src.db_models import LabelFormat
        from src import configuration  # imports global configuration

        from src import configuration
        if not configuration.update_run_background or not self.current_status_raw:
            self.update_status()

        label_format = LabelFormat(field=field, label=label, format_function=format_fn, format=format_str, unit=unit,
                                   default=default, group_id=1)  # TODO

        # TODO generate current item and index based on the scope

        formatted_items = generate_labels([label_format],
                                          self.current_status_raw, pendulum.now(tz='utc'))
        return formatted_items


# let's have just one singleton to be used
data_processor = DataProcessor()
