from typing import Optional, List, Dict

from src.db_models import LabelGroup, LabelFormat, FieldScope, CalculatedField, Driver, DriverChange
from src.data_models import LabelFormatApi, LabelFormatApiList
from src.data_models import CalculatedFieldApi, CalculatedFieldApiList
from src.data_models import DriverApi, DriverApiList
from src.data_models import DriverChangeApi, DriverChangeApiList

from src import db


def get_calculated_fields(field_scope_code: str) -> CalculatedFieldApiList:
    field_scope: Optional[FieldScope] = FieldScope.query.filter_by(code=field_scope_code).first()
    if not field_scope:
        raise ValueError(f"invalid scope code: {field_scope_code}")

    fields = CalculatedField.query.filter_by(scope_id=field_scope.id).order_by(CalculatedField.order_key).all()
    wrapper = CalculatedFieldApiList(title=field_scope.title, items=[])
    for field in fields:
        wrapper.items.append(CalculatedFieldApi.from_orm(field))
    return wrapper


def save_calculated_fields(field_scope_code: str, req_data: CalculatedFieldApiList) -> int:
    from src import db

    field_scope: Optional[FieldScope] = FieldScope.query.filter_by(code=field_scope_code).first()

    if not field_scope:
        field_scope = FieldScope(code=field_scope_code, title=req_data.title)
        db.session.add(field_scope)
    else:
        field_scope.title = req_data.title
    db.session.commit()

    order_key = 1
    db_obj_list = []
    # transform to objects, add order key
    for item in req_data.items:
        db_obj = CalculatedField(**item.dict(), order_key=order_key, scope_id=field_scope.id)
        db_obj_list.append(db_obj)
        order_key += 1

    try:
        calculated_fields = CalculatedField.query.filter_by(scope_id=field_scope.id).all()
        # cleanup old records
        for cf in calculated_fields:
            db.session.delete(cf)
        # write new records
        for obj in db_obj_list:
            db.session.add(obj)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex
    return len(db_obj_list)


def get_calculated_fields_all() -> Dict[str, CalculatedFieldApiList]:
    field_scopes: List[FieldScope] = FieldScope.query.order_by(FieldScope.code).all()

    out = {}
    for field_scope in field_scopes:
        fields = get_calculated_fields(field_scope.code)
        out[field_scope.code] = fields
    return out


def save_calculated_fields_all(d: Dict[str, CalculatedFieldApiList]) -> int:
    res = 0
    for code, values in d.items():
        res += save_calculated_fields(code, values)
    return res


def get_label_formats(label_group_code: str) -> LabelFormatApiList:
    label_group: Optional[LabelGroup] = LabelGroup.query.filter_by(code=label_group_code).first()
    if not label_group:
        raise Exception(f"invalid label group: {label_group_code}")

    labels = LabelFormat.query.filter_by(group_id=label_group.id).order_by(LabelFormat.order_key).all()
    wrapper = LabelFormatApiList(title=label_group.title, items=[])
    for label in labels:
        wrapper.items.append(LabelFormatApi.from_orm(label))
    return wrapper


def save_label_formats(label_group_code: str, req_data: LabelFormatApiList) -> int:
    from src import db

    label_group: Optional[LabelGroup] = LabelGroup.query.filter_by(code=label_group_code).first()

    if not label_group:
        label_group = LabelGroup(code=label_group_code, title=req_data.title)
        db.session.add(label_group)
    else:
        label_group.title = req_data.title
    db.session.commit()

    order_key = 1
    db_obj_list = []
    # transform to objects, add order key
    for item in req_data.items:
        db_obj = LabelFormat(**item.dict(), order_key=order_key, group_id=label_group.id)
        db_obj_list.append(db_obj)
        order_key += 1

    try:
        label_formats = LabelFormat.query.filter_by(group_id=label_group.id).all()
        # cleanup old records
        for lf in label_formats:
            db.session.delete(lf)
        # add new records
        for obj in db_obj_list:
            db.session.add(obj)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex
    return len(db_obj_list)


def get_label_formats_all() -> Dict[str, LabelFormatApiList]:
    label_groups: List[LabelGroup] = LabelGroup.query.order_by(LabelGroup.code).all()
    out = {}
    for label_group in label_groups:
        formats = get_label_formats(label_group.code)
        out[label_group.code] = formats
    return out


def save_label_formats_all(d: Dict[str, LabelFormatApiList]):
    res = 0
    for code, values in d.items():
        res += save_label_formats(code, values)
    return res


def get_drivers() -> DriverApiList:
    from src.db_models import Driver
    db_drivers = Driver.query.order_by(Driver.name).all()
    wrapper = DriverApiList(__root__=[])
    for db_driver in db_drivers:
        wrapper.__root__.append(DriverApi.from_orm(db_driver))
    return wrapper


def save_drivers(req_data: DriverApiList) -> int:
    from src import db

    db_obj_list = []
    # transform to objects, add order key
    for item in req_data.__root__:
        db_obj = Driver(**item.dict())
        db_obj_list.append(db_obj)

    try:
        drivers = Driver.query.all()
        # cleanup old records
        for d in drivers:
            db.session.delete(d)
        # add new records
        for obj in db_obj_list:
            db.session.add(obj)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex
    return len(db_obj_list)


def get_driver_changes() -> DriverChangeApiList:
    from src.db_models import DriverChange
    db_driver_changes = DriverChange.query.order_by(DriverChange.valid_from).all()
    wrapper = DriverChangeApiList(__root__=[])
    for db_driver_change in db_driver_changes:
        wrapper.__root__.append(DriverChangeApi.from_orm(db_driver_change))
    return wrapper


def save_driver_changes(req_data: DriverChangeApiList) -> int:
    from src import db

    db_obj_list = []
    # transform to objects, add order key
    for item in req_data.__root__:
        db_obj = DriverChange(**item.dict())
        db_obj_list.append(db_obj)

    try:
        driver_changes = DriverChange.query.all()
        # cleanup old records
        for dch in driver_changes:
            db.session.delete(dch)
        # add new records
        for obj in db_obj_list:
            db.session.add(obj)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex
    return len(db_obj_list)

