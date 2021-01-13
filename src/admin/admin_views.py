from flask import redirect, url_for, flash, Markup
from flask_admin import BaseView, expose
from flask_admin.contrib import sqla
from flask_security import current_user

from src.admin.admin_forms import TestLabelFormatForm, TestCalculatedFieldForm
from src.data_processor.data_processor import test_custom_calculated_field, test_custom_label_format


# Create customized model view class for admin users
class MyAdminView(sqla.ModelView):

    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated and current_user.has_role('admin')

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


# Parent view for custom admin pages (not db model based)
class MyAdminCustomView(BaseView):

    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated
               #and current_user.has_role('admin')

    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))



class MySecurityRedirectView(BaseView):
    def __init__(self, url_key, *args, **kwargs):
        super(MySecurityRedirectView, self).__init__(*args, **kwargs)
        self.url_key = url_key
    @expose('/')
    def index(self):
        return redirect(url_for(self.url_key))


class MyTestCalculatedFieldView(MyAdminCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = TestCalculatedFieldForm()
        if form.validate_on_submit():
            try:
                return_value = test_custom_calculated_field(form.field_name.data, form.field_scope.data, form.fn_code.data, form.return_type.data)
                flash(Markup(f"Return value for field <b>{form.field_name.data}</b> is <b>{return_value[form.field_name.data]}</b>"), "info")
            except Exception as ex:
                flash(ex, "error")
        return self.render('admin/test_calculated_field.html', form=form, post_url=url_for('test_calculated_field.index'), with_categories=True)


class MyTestLabelFormatTestView(MyAdminCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = TestLabelFormatForm()
        if form.validate_on_submit():
            try:
                return_value = test_custom_label_format(form.label_group.data, form.field_name.data,
                                                        form.label.data, form.format_fn.data,
                                                        form.format.data, form.unit.data, form.default.data
                                                        )
                flash(Markup(f"Return value for label <b>{return_value[0].label}</b> is <b>{return_value[0].value}</b>"), "info")
            except Exception as ex:
                print(ex)
                flash(ex, "error")
        return self.render('admin/test_label_format.html', form=form, post_url=url_for('test_label_format.index'), with_categories=True)


class LabelFormatView(MyAdminView):
    pass
    # column_searchable_list = ['field', ""]


class CalculatedFieldView(MyAdminView):
    pass
    #form_columns = ['scope', 'name', 'description', 'return_type', 'calc_fn', 'order_key']
    # column_searchable_list = ['field', ""]