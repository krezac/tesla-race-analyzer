"""Data models."""
import pendulum

from . import db
from flask_security.models import fsqla_v2 as fsqla


class User(db.Model, fsqla.FsUserMixin):
    pass


# Define the User data-model.
class Role(db.Model, fsqla.FsRoleMixin):
    pass

class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)


# there is intentionally no FK to drivers
class DriverChange(db.Model):
    __tablename__ = 'driver_changes'

    id = db.Column(db.Integer, primary_key=True)
    driver_name = db.Column(db.String, nullable=False)
    copilot_name = db.Column(db.String, nullable=True)
    valid_from = db.Column(db.DateTime, nullable=False, default=pendulum.now(tz='utc'))
    valid_to = db.Column(db.DateTime, nullable=True)