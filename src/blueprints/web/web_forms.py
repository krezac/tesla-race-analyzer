import pendulum
from flask_wtf import FlaskForm
from wtforms import DateTimeField, SubmitField
from wtforms.validators import DataRequired


class StaticDashboardForm(FlaskForm):
    dt = DateTimeField("Time (UTC)", validators=[DataRequired()])
    go_to_time = SubmitField(label='Go to')
    go_to_start = SubmitField(label='Start')
    go_to_minus_10_hours = SubmitField(label='-10h')
    go_to_minus_1_hour = SubmitField(label='-1h')
    go_to_minus_10_minutes = SubmitField(label='-10m')
    go_to_minus_1_minute = SubmitField(label='-1m')
    go_to_minus_10_seconds = SubmitField(label='-10s')
    go_to_minus_1_second = SubmitField(label='-1s')
    go_to_plus_1_second = SubmitField(label='+1s')
    go_to_plus_10_seconds = SubmitField(label='+10s')
    go_to_plus_1_minute = SubmitField(label='+1m')
    go_to_plus_10_minutes = SubmitField(label='+10m')
    go_to_plus_1_hour = SubmitField(label='+1h')
    go_to_plus_10_hours = SubmitField(label='+10h')
    go_to_end = SubmitField(label='End')
