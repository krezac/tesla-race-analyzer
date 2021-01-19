from flask import url_for
from flask_admin import expose

from src.blueprints.web.web_forms import StaticDashboardForm

from src.parent_views import MyRoleRequiredCustomView


class MyTestCalculatedFieldView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        pass
