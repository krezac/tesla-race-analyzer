from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SelectField, TextAreaField, IntegerField, SubmitField, BooleanField, \
    SelectMultipleField
from wtforms.fields import IntegerField
from wtforms.validators import DataRequired, NumberRange


class TestCalculatedFieldForm(FlaskForm):
    field_scope = SelectField("Scope", validators=[DataRequired()])
    fn_code = TextAreaField('Code', validators=[DataRequired()])
    item_index = IntegerField('Item Index', validators=[DataRequired()], default=-1)


class TestLabelFormatForm(FlaskForm):
    label_group = SelectField('Label Group', validators=[DataRequired()])
    field_name = StringField('Name', validators=[DataRequired()])
    format_fn = SelectField('Function', validators=[DataRequired()])
    format = StringField('Format', validators=[DataRequired()])
    unit = StringField('Unit', validators=[])
    default = StringField('Default', validators=[], default='---')
    item_index = IntegerField('Item Index', validators=[DataRequired()], default=-1)


class DriverChangeForm(FlaskForm):
    driver = SelectField('Driver', validators=[DataRequired()])
    copilot = SelectField('Copilot', validators=[])
    save = SubmitField(label='Save')


class ConfigBackupForm(FlaskForm):
    save = SubmitField(label='Save backup')


class ConfigRestoreForm(FlaskForm):
    backup_file = FileField(label='Select file', validators=[FileRequired()])
    restore_config = BooleanField(label='Restore config', default=True)
    overwrite_config_file = BooleanField(label='Overwrite config file', default=False)
    restore_calculated_fields = BooleanField(label='Restore calculated_fields', default=True)
    restore_label_formats = BooleanField(label='Restore label formats', default=True)
    restore_drivers = BooleanField(label='Restore drivers', default=True)
    restore_driver_changes = BooleanField(label='Restore driver changes', default=True)
    load = SubmitField(label='Load backup')


class GenerateJwtTokenForm(FlaskForm):
    hours = IntegerField(label='Token validity[hours]', validators=[DataRequired(), NumberRange(1, 72)], default=1)
    generate = SubmitField(label='Generate')


class CreateNewUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    roles = SelectMultipleField('Roles', validators=[DataRequired()])
    create = SubmitField(label='Create')
