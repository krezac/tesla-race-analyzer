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


class FieldScopeApi(BaseModel):
    code: str
    title: Optional[str]

    class Config:
        orm_mode = True


class FieldScopeApiList(BaseModel):
    __root__: List[FieldScopeApi]


class CalculatedFieldApi(BaseModel):
    name: str
    description: Optional[str]
    return_type: str
    calc_fn: str
    order_key: Optional[int]

    class Config:
        orm_mode = True


class CalculatedFieldApiList(BaseModel):
    title: Optional[str]
    items: List[CalculatedFieldApi]


class LabelGroupApi(BaseModel):
    code: str
    title: Optional[str]

    class Config:
        orm_mode = True


class LabelGroupApiList(BaseModel):
    __root__: List[LabelGroupApi]


class LabelFormatApi(BaseModel):
    field: str
    label: Optional[str]
    format_function: Optional[str]
    format: Optional[str]
    unit: Optional[str]
    default: Optional[str]
    order_key: Optional[int]

    class Config:
        orm_mode = True


class LabelFormatApiList(BaseModel):
    title: Optional[str]
    items: List[LabelFormatApi]


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
    # TODO explicit if for total ?
    if label_group == LabelFormatGroupEnum.STATUS.value or label_group == LabelFormatGroupEnum.MAP.value:
        return get_status_raw()
    elif label_group == LabelFormatGroupEnum.FORECAST:
        return get_forecast_raw()
    else:
        laps = data_processor.get_laps_raw()
        if laps:
            lap = laps[-1].copy()
            if 'lap_data' in lap:
                lap['lap_data'] = {}  # we just don't want to dump
            if 'pit_data' in lap:
                lap['pit_data'] = {}  # we just don't want to dump
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
# @jwt_ex_role_required('admin')  # @jwt_required
def get_label_groups():
    groups = LabelGroup.query.all()
    wrapper = LabelGroupApiList(__root__=[])
    for g in groups:
        wrapper.__root__.append(LabelGroupApi.from_orm(g))

    return Response(wrapper.json(exclude={'__root__': {'__all__': {'id', 'order_key'}}}), mimetype='application/json')


@api_bp.route('/config/field_scopes')
# @jwt_ex_role_required('admin')  # @jwt_required
def get_field_scopes():
    field_scopes = FieldScope.query.all()
    wrapper = FieldScopeApiList(__root__=[])
    for fs in field_scopes:
        wrapper.__root__.append(FieldScopeApi.from_orm(fs))

    return Response(wrapper.json(exclude={'__root__': {'__all__': {'order_key'}}}), mimetype='application/json')



@api_bp.route('/config/fields/<field_scope_code>', methods=['GET', 'POST'])
def configure_calculated_fields(field_scope_code):
    field_scope: Optional[FieldScope] = FieldScope.query.filter_by(code=field_scope_code).first()
    if not field_scope:
        abort(400, 'invalid scope code')

    if request.method == 'POST':
        ensure_jwt_has_user_role('admin')
        json_request = request.get_json()
        new_scope_title = json_request.get('title')
        j_list = json_request['items']
        obj_list = []
        order_key = 1
        # transform to objects, add order key
        for j in j_list:
            obj = CalculatedField(**j, order_key=order_key, scope_id=field_scope.id)
            order_key += 1
            obj_list.append(obj)

        # cleanup old records
        calculated_fields = CalculatedField.query.filter_by(scope_id=field_scope.id).all()
        for cf in calculated_fields:
            db.session.delete(cf)
        for obj in obj_list:
            db.session.add(obj)
        if field_scope.title != new_scope_title:
            field_scope.title = new_scope_title
            db.session.add(field_scope)
        db.session.commit()

    # get the current status
    fields = CalculatedField.query.filter_by(scope_id=field_scope.id).order_by(CalculatedField.order_key).all()
    wrapper = CalculatedFieldApiList(title=field_scope.title, items=[])
    for field in fields:
        wrapper.items.append(CalculatedFieldApi.from_orm(field))

    return Response(wrapper.json(exclude={'items': {'__all__': {'order_key'}}}), mimetype='application/json')


@api_bp.route('/config/labels/<label_group_code>', methods=['GET', 'POST'])
def configure_labels(label_group_code):
    label_group: Optional[LabelGroup] = LabelGroup.query.filter_by(code=label_group_code).first()
    if not label_group:
        abort(400, 'invalid group code')

    if request.method == 'POST':
        ensure_jwt_has_user_role('admin')
        json_request = request.get_json()
        new_group_title = json_request.get('title')
        j_list = json_request['items']
        obj_list = []
        order_key = 1
        # transform to objects, add order key
        for j in j_list:
            obj = LabelFormat(**j, order_key=order_key, group_id=label_group.id)
            order_key += 1
            obj_list.append(obj)

        # cleanup old records
        label_formats = LabelFormat.query.filter_by(group_id=label_group.id).all()
        for lf in label_formats:
            db.session.delete(lf)
        for obj in obj_list:
            db.session.add(obj)
        if label_group.title != new_group_title:
            label_group.title = new_group_title
            db.session.add(label_group)
        db.session.commit()

    # get the current status
    labels = LabelFormat.query.filter_by(group_id=label_group.id).order_by(LabelFormat.order_key).all()
    wrapper = LabelFormatApiList(title=label_group.title, items=[])
    for label in labels:
        wrapper.items.append(LabelFormatApi.from_orm(label))

    return Response(wrapper.json(exclude={'items': {'__all__': {'id', 'order_key'}}}), mimetype='application/json')
