from flask import redirect, url_for, flash, Markup
from flask_admin import BaseView, expose
from flask_admin.contrib import sqla
from flask_security import current_user
from flask_jwt_extended import create_access_token

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
        from src.db_models import FieldScope
        form.field_scope.choices = [(g.code, g) for g in FieldScope.query.all()]
        if form.validate_on_submit():
            try:
                return_value = test_custom_calculated_field('__test_field__', form.field_scope.data, form.fn_code.data, "")  # TODO the return type is not needed for now
                flash(Markup(f"Return value is <b>{return_value['__test_field__']}</b>"), "info")
            except Exception as ex:
                flash(f"{type(ex).__name__}: {ex}", "error")
        return self.render('admin/test_calculated_field.html', form=form, post_url=url_for('test_calculated_field.index'), with_categories=True)


class MyTestLabelFormatTestView(MyAdminCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = TestLabelFormatForm()
        from src.db_models import LabelGroup
        form.label_group.choices = [(g.code, g) for g in LabelGroup.query.all()]
        from src.data_processor.labels import get_calc_functions
        form.format_fn.choices = get_calc_functions()
        if form.validate_on_submit():
            try:
                return_value = test_custom_label_format(form.label_group.data, form.field_name.data,
                                                        '__test_label__', form.format_fn.data,
                                                        form.format.data, form.unit.data, form.default.data
                                                        )
                flash(Markup(f"Return value for label formatting is <b>{return_value[0].value}</b>"), "info")
            except Exception as ex:
                flash(f"{type(ex).__name__}: {ex}", "error")
                raise ex
        api_token = create_access_token(identity='api')
        return self.render('admin/test_label_format.html', form=form, post_url=url_for('test_label_format.index'), with_categories=True, field_list_url=url_for('api_bp.get_list_of_fields'), api_token=api_token)


class LabelFormatView(MyAdminView):
    pass
    # column_searchable_list = ['field', ""]


class CalculatedFieldView(MyAdminView):
    pass
    #form_columns = ['scope', 'name', 'description', 'return_type', 'calc_fn', 'order_key']
    # column_searchable_list = ['field', ""]