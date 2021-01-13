from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired


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
