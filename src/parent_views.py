from typing import Optional

from flask import redirect, url_for, flash, Markup
from flask_admin import BaseView, expose
from flask_admin.contrib import sqla
from flask_security import current_user
from flask_jwt_extended import create_access_token

from src.admin.admin_forms import TestLabelFormatForm, TestCalculatedFieldForm
from src.data_processor.data_processor import data_processor


class MyRedirectView(BaseView):
    """
    View to redirect to arbitrary page (i.e. security)
    """
    def __init__(self, target_endpoint, *args, **kwargs):
        super(MyRedirectView, self).__init__(*args, **kwargs)
        self.target_endpoint = target_endpoint

    @expose('/')
    def index(self):
        return redirect(url_for(self.target_endpoint))


class MyRoleRequiredDataView(sqla.ModelView):
    """
    View for data editing page (flask-admin built in) requiring role
    """

    def __init__(self, role_required: str, model, session, **kwargs):
        super(MyRoleRequiredDataView, self).__init__(model, session, **kwargs)
        self.role_required = role_required

    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated and \
               (not self.role_required or current_user.has_role(self.role_required))

    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))


class MyRoleRequiredCustomView(BaseView):
    """
    View for no-data based pages requiring role
    """

    def __init__(self, role_required: str, **kwargs):
        super(MyRoleRequiredCustomView, self).__init__(**kwargs)
        self.role_required = role_required

    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated and \
               (not self.role_required or current_user.has_role(self.role_required))

    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))
