from flask import url_for, flash, Markup, redirect, Response
from flask_admin import expose
from flask_jwt_extended import create_access_token
import pendulum

from src.admin.admin_forms import TestLabelFormatForm, TestCalculatedFieldForm, DriverChangeForm, \
    ConfigRestoreForm, ConfigBackupForm
from src.data_processor.data_processor import data_processor
from src.parent_views import MyRoleRequiredCustomView
from src.data_models import ConfigBackupData


class MyTestCalculatedFieldView(MyRoleRequiredCustomView):

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = TestCalculatedFieldForm()
        from src.db_models import FieldScope
        form.field_scope.choices = [(g.code, g) for g in FieldScope.query.all()]
        if form.validate_on_submit():
            try:
                return_value = data_processor.test_custom_calculated_field('__test_field__', form.field_scope.data, form.fn_code.data, "")  # TODO the return type is not needed for now
                flash(Markup(f"Return value is <b>{return_value['__test_field__']}</b>"), "info")
            except Exception as ex:
                flash(f"{type(ex).__name__}: {ex}", "error")
        return self.render('admin/test_calculated_field.html', form=form, post_url=url_for('test_calculated_field.index'), with_categories=True)


class MyTestLabelFormatTestView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = TestLabelFormatForm()
        from src.db_models import LabelGroup
        form.label_group.choices = [(g.code, g) for g in LabelGroup.query.all()]
        from src.data_processor.labels import get_calc_functions
        form.format_fn.choices = get_calc_functions()
        if form.validate_on_submit():
            try:
                return_value = data_processor.test_custom_label_format(form.label_group.data, form.field_name.data,
                                                        '__test_label__', form.format_fn.data,
                                                        form.format.data, form.unit.data, form.default.data
                                                        )
                flash(Markup(f"Return value for label formatting is <b>{return_value[0].value}</b>"), "info")
            except Exception as ex:
                flash(f"{type(ex).__name__}: {ex}", "error")
                raise ex
        api_token = create_access_token(identity='api')
        return self.render('admin/test_label_format.html', form=form, post_url=url_for('test_label_format.index'), with_categories=True, field_list_url=url_for('api_bp.get_list_of_fields'), api_token=api_token)



class DriverChangeView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = DriverChangeForm()
        from src.db_models import Driver, DriverChange
        from src import db
        drivers = [("", "---")] + [(g.name, g.name) for g in Driver.query.all()]
        form.driver.choices = drivers
        form.copilot.choices = drivers
        if form.validate_on_submit():
            now = pendulum.now(tz='utc')
            active_records = DriverChange.query.filter_by(valid_to=None).all()
            for rec in active_records:
                rec.valid_to = now
            db.session.add(DriverChange(driver=form.driver.data, copilot=form.copilot.data, valid_from=now))
            db.session.commit()
        return redirect(url_for("admin.index"))


class ConfigBackupView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = ConfigBackupForm()
        from src.db_models import Driver, DriverChange
        from src import db, configuration
        if form.validate_on_submit():
            now = pendulum.now(tz='utc')
            backup = ConfigBackupData(
                configuration=configuration
            )
            return Response(backup.json(indent=2),
                            mimetype='application/json',
                            headers={'Content-Disposition':
                                     f"attachment;filename=tran_backup-{now.format('YYYY-MM-DD-HH-mm-ss')}.json"})
        return self.render("admin/config_backup.html", form=form)


class ConfigRestoreView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = ConfigRestoreForm()
        from src.db_models import Driver, DriverChange
        from src import db
        if form.validate_on_submit():
            backup_file = form.backup_file.data
            backup_data = backup_file.read()
            backup = ConfigBackupData.parse_raw(backup_data)
            overwrite_config_file = form.overwrite_config_file
            from src import load_config
            load_config(backup.configuration, overwrite_config_file.data)
            flash(f"System state restored from backup {backup}", "info")
        return self.render("admin/config_restore.html", form=form, with_categories=True)
