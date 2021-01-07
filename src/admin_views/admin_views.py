from flask import redirect, url_for, request
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib import sqla
from flask_admin import AdminIndexView
from flask_security import current_user


# Create customized model view class for admin users
class MyAdminView(sqla.ModelView):

    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated
               #and current_user.has_role('admin')

    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))

# Create customized model view class for authenticated users
class MyAuthView(sqla.ModelView):

    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated

    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))


class MyLogoutView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('security.logout'))


class LabelFormatView(MyAdminView):
    pass
    # column_searchable_list = ['field', ""]


class CalculatedFieldView(MyAdminView):
    pass
    #form_columns = ['scope', 'name', 'description', 'return_type', 'calc_fn', 'order_key']
    # column_searchable_list = ['field', ""]