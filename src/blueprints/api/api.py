from flask import Blueprint, render_template, Response, abort, request
from flask import jsonify as jsonify_native
import pendulum
import json
from typing import Optional, List
from pydantic import BaseModel

from src import configuration, db
from src.db_models import LabelGroup, LabelFormat, FieldScope, CalculatedField
from src.jwt_roles import jwt_ex_role_required, ensure_jwt_has_user_role

from src.data_processor.data_processor import data_processor
from src.enums import LabelFormatGroupEnum, CalculatedFieldScopeEnum

api_bp = Blueprint('api_bp', __name__,
                   template_folder='templates',
                   static_folder='static',
                   static_url_path='/assets')


def _jsonify(data):
    """
    In case there are field not natively serialiable, workaround it by passing as string
    :param data: data to jsonify
    :return: HTTP Response
    """
    try:
        return jsonify_native(data)
    except TypeError:
        out = json.dumps(data, default=str)
        return Response(out, mimetype='application/json')

########################################
# activate update for background tasks #
########################################
@api_bp.route('/_internal/update_status')
# @jwt_ex_role_required('megasuperadmin')  # @jwt_required
def update_status():
    data_processor.update_status()
    return "Success"

@api_bp.route('/_internal/update_laps')
# @jwt_ex_role_required('megasuperadmin')  # @jwt_required
def update_laps():
    data_processor.update_positions_laps_forecast()
    return "Success"


################################################
# functions to get data for UI (no protection) #
################################################

@api_bp.route('/car/status')
def get_status():
    resp = data_processor.get_status_formatted()
    return Response(resp.json(), mimetype='application/json')


@api_bp.route('/car/laps')
def get_laps():
    resp = data_processor.get_laps_formatted()
    return Response(resp.json(), mimetype='application/json')


@api_bp.route('/car/chargings')
def get_chargings():
    resp = data_processor.get_charging_process_list_formatted()
    return Response(resp.json(), mimetype='application/json')


@api_bp.route('/car/total')
def get_total():
    resp = data_processor.get_total_formatted()
    return Response(resp.json(), mimetype='application/json')


@api_bp.route('/car/forecast')
def get_forecast():
    resp = data_processor.get_forecast_formatted()
    return Response(resp.json(), mimetype='application/json')


# not needed any more
# @api_bp.route('/car/status/fields')
# def get_status_fields():
#     resp = describe_status_fields()
#     return Response(resp.json(), mimetype='application/json')
#


@api_bp.route('/version')
def version():
    return Response(render_template("version.txt"), mimetype='application/json')


################################
# service endpoints to debug   #
################################

@api_bp.route('/car/status/raw')
@jwt_ex_role_required('admin')  # @jwt_required
def get_status_raw():
    resp = data_processor.get_status_raw()
    return _jsonify(resp)


@api_bp.route('/car/positions/raw')
@jwt_ex_role_required('admin')  # @jwt_required
def get_positions_raw():
    resp = data_processor.get_positions_raw()
    return _jsonify(resp)


@api_bp.route('/car/laps/raw')
@jwt_ex_role_required('admin')  # @jwt_required
def get_laps_raw():
    resp = data_processor.get_laps_raw()
    return _jsonify(resp)


@api_bp.route('/car/total/raw')
@jwt_ex_role_required('admin')  # @jwt_required
def get_total_raw():
    resp = data_processor.get_total_raw()
    return _jsonify(resp)


@api_bp.route('/car/forecast/raw')
@jwt_ex_role_required('admin')  # @jwt_required
def get_forecast_raw():
    resp = data_processor.get_forecast_raw()
    return _jsonify(resp)


@api_bp.route('/label_group/fields')
def get_list_of_fields():
    """ This is just to show available fields in test window """
    label_group = request.args.get('label_group')
    if label_group == LabelFormatGroupEnum.STATUS.value or label_group == LabelFormatGroupEnum.MAP.value:
        return get_status_raw()
    elif label_group == LabelFormatGroupEnum.RECENT_LAP.value:
        laps = data_processor.get_laps_raw()
        if laps:
            lap = laps[-1].copy()
            if 'lap_data' in lap:
                lap['lap_data'] = {}  # we just don't want to dump
            if 'pit_data' in lap:
                lap['pit_data'] = {}  # we just don't want to dump
            return _jsonify(lap)
    elif label_group == LabelFormatGroupEnum.PREVIOUS_LAPS.value:
        laps = data_processor.get_laps_raw()
        if laps:
            lap = laps[-2 if len(laps) > 0 else -1].copy()
            if 'lap_data' in lap:
                lap['lap_data'] = {}  # we just don't want to dump
            if 'pit_data' in lap:
                lap['pit_data'] = {}  # we just don't want to dump
            return _jsonify(lap)
    elif label_group == LabelFormatGroupEnum.TOTAL.value:
        total = data_processor.get_total_raw()
        return _jsonify(total)
    elif label_group == LabelFormatGroupEnum.FORECAST.value:
        return get_forecast_raw()
    elif label_group == LabelFormatGroupEnum.CHARGING.value:
        chp_list = data_processor.get_charging_process_list_raw()
        if chp_list:
            lap = chp_list[-1].copy()
            return _jsonify(lap)

    return _jsonify({})


@api_bp.route('/graph_data/lap')
def get_graph_data_lap():
    lap_id = request.args.get('lap')
    field = request.args.get('field')

    laps = data_processor.get_laps_raw()
    lap = laps[int(lap_id) if lap_id else -1]
    lap_data = lap['lap_data']
    graph_periods = [pendulum.Period(lap_data[0]['date'], item['date']) for item in lap_data]
    graph_labels = [f"{raw_value.hours:02d}:{raw_value.minutes:02d}:{raw_value.remaining_seconds:02d}" for raw_value in graph_periods]
    graph_data = [float(item[field]) if item[field] is not None else None for item in lap_data]
    return _jsonify({"labels": graph_labels, "values": graph_data})


@api_bp.route('/graph_data/lap/chargings')
def get_graph_charging_lap_data():
    lap_id = request.args.get('lap')
    field = request.args.get('field')

    laps = data_processor.get_laps_raw()
    lap = laps[int(lap_id) if lap_id else -1]
    lap_data = lap['lap_data']
    lap_chargings = data_processor.get_car_chargings(int(lap_id))
    charges = lap_chargings[0]['charges']

    graph_periods = [pendulum.Period(charges[0]['date'], charge['date']) for charge in charges]
    graph_labels = [f"{raw_value.hours:02d}:{raw_value.minutes:02d}:{raw_value.remaining_seconds:02d}" for raw_value in graph_periods]
    graph_data = [float(charge[field]) if charge[field] is not None else None for charge in charges]
    return _jsonify({"labels": graph_labels, "values": graph_data, 'raw': lap_chargings})


######################################
# functions to change configurations #
######################################


@api_bp.route('/config/label_groups')
@jwt_ex_role_required('admin')
def get_label_groups():
    from src.data_models import LabelGroupApi, LabelGroupApiList

    groups = LabelGroup.query.all()
    wrapper = LabelGroupApiList(__root__=[])
    for g in groups:
        wrapper.__root__.append(LabelGroupApi.from_orm(g))

    return Response(wrapper.json(exclude={'__root__': {'__all__': {'id', 'order_key'}}}), mimetype='application/json')


@api_bp.route('/config/field_scopes')
@jwt_ex_role_required('admin')
def get_field_scopes():
    from src.data_models import FieldScopeApi, FieldScopeApiList
    field_scopes = FieldScope.query.all()
    wrapper = FieldScopeApiList(__root__=[])
    for fs in field_scopes:
        wrapper.__root__.append(FieldScopeApi.from_orm(fs))

    return Response(wrapper.json(exclude={'__root__': {'__all__': {'order_key'}}}), mimetype='application/json')


@api_bp.route('/config/calculated_fields/<field_scope_code>', methods=['GET', 'POST'])
@jwt_ex_role_required('admin')
def configure_calculated_fields(field_scope_code):
    from src.data_models import CalculatedFieldApiList
    from src.backup import get_calculated_fields, save_calculated_fields

    if request.method == 'POST':
        save_calculated_fields(field_scope_code, CalculatedFieldApiList.parse_obj(request.get_json()))

    # get the current status
    wrapper = get_calculated_fields(field_scope_code)
    return Response(wrapper.json(), mimetype='application/json')


@api_bp.route('/config/calculated_fields', methods=['GET', 'POST'])
@jwt_ex_role_required('admin')
def configure_calculated_fields_all():
    from src.data_models import CalculatedFieldApiDict
    from src.backup import get_calculated_fields_all, save_calculated_fields_all

    if request.method == 'POST':
        save_calculated_fields_all(CalculatedFieldApiDict.parse_obj(request.get_json()).__root__)

    # get the current status
    wrapper = CalculatedFieldApiDict(__root__=get_calculated_fields_all())
    return Response(wrapper.json(), mimetype='application/json')


@api_bp.route('/config/label_formats/<label_group_code>', methods=['GET', 'POST'])
@jwt_ex_role_required('admin')
def configure_labels(label_group_code):
    from src.data_models import LabelFormatApiList
    from src.backup import get_label_formats, save_label_formats

    if request.method == 'POST':
        save_label_formats(label_group_code, LabelFormatApiList.parse_obj(request.get_json()))

    # get the current status
    wrapper = get_label_formats(label_group_code)
    return Response(wrapper.json(), mimetype='application/json')


@api_bp.route('/config/label_formats', methods=['GET', 'POST'])
@jwt_ex_role_required('admin')
def configure_labels_all():
    from src.data_models import LabelFormatApiDict
    from src.backup import get_label_formats_all, save_label_formats_all

    if request.method == 'POST':
        save_label_formats_all(LabelFormatApiDict.parse_obj(request.get_json()).__root__)

    # get the current status
    wrapper = LabelFormatApiDict(__root__=get_label_formats_all())
    return Response(wrapper.json(), mimetype='application/json')


@api_bp.route('/config/drivers', methods=['GET', 'POST'])
@jwt_ex_role_required('admin')
def configure_drivers():
    from src.data_models import DriverApiList
    from src.backup import get_drivers, save_drivers

    if request.method == 'POST':
        save_drivers(DriverApiList.parse_obj(request.get_json()))

    # get the current status
    wrapper = get_drivers()
    return Response(wrapper.json(), mimetype='application/json')


@api_bp.route('/config/driver_changes', methods=['GET', 'POST'])
@jwt_ex_role_required('admin')
def configure_driver_changes():
    from src.data_models import DriverChangeApiList
    from src.backup import get_driver_changes, save_driver_changes

    if request.method == 'POST':
        save_driver_changes(DriverChangeApiList.parse_obj(request.get_json()))

    # get the current status
    wrapper = get_driver_changes()
    return Response(wrapper.json(), mimetype='application/json')


@api_bp.route('/config/configuration', methods=['GET', 'POST'])
@jwt_ex_role_required('admin')
def configure_configuration():
    from src import configuration, load_config
    from src.data_models import Configuration

    if request.method == 'POST':
        overwrite_config_file = request.args.get('overwrite_config_file', False)
        config = Configuration.parse_obj(request.get_json())
        load_config(config, overwrite_config_file)

    # get the current status
    return Response(configuration.json(), mimetype='application/json')
