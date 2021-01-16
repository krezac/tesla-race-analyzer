from flask import url_for
from flask_admin import expose

from src.blueprints.web.web_forms import StaticDashboardForm

from src.admin.admin_views import MyAdminCustomView


class MyTestCalculatedFieldView(MyAdminCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        pass
