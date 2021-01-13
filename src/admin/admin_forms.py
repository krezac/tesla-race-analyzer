from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class TestCalculatedFieldForm(FlaskForm):
    field_scope = StringField('Scope', validators=[DataRequired()])
    field_name = StringField('Name', validators=[DataRequired()])
    fn_code = StringField('Code', validators=[DataRequired()])
    return_type = StringField('Return type', validators=[DataRequired()])


class TestLabelFormatForm(FlaskForm):
    label_group = StringField('Label Group', validators=[DataRequired()])
    field_name = StringField('Name', validators=[DataRequired()])
    label = StringField('Label', validators=[DataRequired()])
    format_fn = StringField('Function', validators=[DataRequired()])
    format = StringField('Format', validators=[DataRequired()])
    unit = StringField('Unit', validators=[DataRequired()])
    default = StringField('Default', validators=[DataRequired()])
