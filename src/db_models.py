"""Data models."""
import pendulum

from . import db
from flask_security.models import fsqla_v2 as fsqla
from sqlalchemy import UniqueConstraint
from typing import Optional
from src.enums import CalculatedFieldScopeEnum, LabelFormatGroupEnum


class User(db.Model, fsqla.FsUserMixin):
    def __repr__(self):
        return self.email


# Define the User data-model.
class Role(db.Model, fsqla.FsRoleMixin):

    def __repr__(self):
        return self.name


class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    def __repr__(self):
        return self.name


class DriverChange(db.Model):
    __tablename__ = 'driver_changes'

    id = db.Column(db.Integer, primary_key=True)
    driver = db.Column(db.String, nullable=False)  # note these are no foreign keys
    copilot = db.Column(db.String, nullable=True)  # note these are no foreign keys
    valid_from = db.Column(db.DateTime, nullable=False, default=pendulum.now(tz='utc'))
    valid_to = db.Column(db.DateTime, nullable=True)


class LabelGroup(db.Model):
    __tablename__ = 'label_groups'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, nullable=False, unique=True)
    title = db.Column(db.String, nullable=True)
    #formats = db.relationship('LabelFormat', backref='label_group', lazy=True)

    def __repr__(self):
        return f"{self.code} ({self.title})"

    @classmethod
    def add_if_not_exists(cls, code: LabelFormatGroupEnum, title: str):
        if not LabelGroup.query.filter_by(code=code.value).first():
            db.session.add(LabelGroup(code=code.value, title=title))


class LabelFormat(db.Model):
    __tablename__ = 'label_formats'

    # __table_args__ = (
    #     db.UniqueConstraint('group_id', 'field', name='uix_label_format_group_field'),
    #     db.UniqueConstraint('group_id', 'order_key', name='uix_label_format_group_order'),
    # )

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('label_groups.id'), nullable=False)
    field = db.Column(db.String, nullable=False)
    label = db.Column(db.String, nullable=True)
    format_function = db.Column(db.String, nullable=True)
    format = db.Column(db.String, nullable=True)
    unit = db.Column(db.String, nullable=True)
    default = db.Column(db.String, nullable=True)
    order_key = db.Column(db.Integer, nullable=False)
    group = db.relationship("LabelGroup", foreign_keys='LabelFormat.group_id')
    db.UniqueConstraint(group_id, order_key)

    # explicit/composite unique constraint.  'name' is optional.
    #UniqueConstraint('group_id', 'field', name='uix_label_format_group_field')
    #UniqueConstraint('group_id', 'order_key', name='uix_label_format_group_order')

    def __repr__(self):
        return self.field

    @classmethod
    def get_all_by_group(cls, label_group_code):
        label_group: Optional[LabelGroup] = LabelGroup.query.filter_by(code=label_group_code).first()
        if not label_group:
            raise Exception("invalid group code")
        return LabelFormat.query.filter_by(group_id=label_group.id).all()


class FieldScope(db.Model):
    __tablename__ = 'field_scopes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, nullable=False, unique=True)
    title = db.Column(db.String, nullable=False)
    #fields = db.relationship('CalculatedField', backref='field_scope', lazy=True)

    def __repr__(self):
        return f"{self.code} ({self.title})"

    @classmethod
    def add_if_not_exists(cls, code: CalculatedFieldScopeEnum, title: str):
        if not FieldScope.query.filter_by(code=code.value).first():
            db.session.add(FieldScope(code=code.value, title=title))


class CalculatedField(db.Model):
    __tablename__ = 'calculated_fields'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    return_type = db.Column(db.String, nullable=False)
    calc_fn = db.Column(db.String, nullable=False)
    order_key = db.Column(db.Integer, nullable=False)
    scope_id = db.Column(db.Integer, db.ForeignKey('field_scopes.id'), nullable=False)
    scope = db.relationship("FieldScope", foreign_keys='CalculatedField.scope_id')

    db.UniqueConstraint(scope_id, name)
    db.UniqueConstraint(scope_id, order_key)

    # explicit/composite unique constraint.  'name' is optional.
    #UniqueConstraint('scope_id', 'name', name='uix_field_scope_name')
    #UniqueConstraint('scope_id', 'order_key', name='uix_field_scope_order')

    @classmethod
    def get_all_by_scope(cls, field_scope_code):
        field_scope: Optional[FieldScope] = FieldScope.query.filter_by(code=field_scope_code).first()
        if not field_scope:
            raise Exception("invalid field scope")
        return CalculatedField.query.filter_by(scope_id=field_scope.id).all()

    def __repr__(self):
        return self.name


class CustomPage(db.Model):
    __tablename__ = 'custom_pages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    template = db.Column(db.String, nullable=False)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return self.name
