from flask import url_for, flash, Markup, redirect, Response
from flask_admin import expose
from flask_jwt_extended import create_access_token
import pendulum

from src.admin.admin_forms import TestLabelFormatForm, TestCalculatedFieldForm, DriverChangeForm, \
    ConfigRestoreForm, ConfigBackupForm, GenerateJwtTokenForm, CreateNewUserForm
from src.data_processor.data_processor import data_processor
from src.parent_views import MyRoleRequiredCustomView
from src.data_models import ConfigBackupData


class MyTestCalculatedFieldView(MyRoleRequiredCustomView):

    @expose('/', methods=['GET', 'POST'])
    def index(self):

        form = TestCalculatedFieldForm()
        from src import configuration, db
        from src.db_models import FieldScope, CalculatedField
        form.field_scope.choices = [(g.code, g) for g in FieldScope.query.all()]
        if form.validate_on_submit():
            try:
                return_value = data_processor.test_custom_calculated_field('__test_field__', form.field_scope.data, form.fn_code.data, "")  # TODO the return type is not needed for now
                flash(Markup(f"Return value is <b>{return_value['__test_field__']}</b>"), "info")
                if form.add.data:
                    scope = FieldScope.query.filter_by(code=form.field_scope.data).first()
                    cf_ok = CalculatedField.query.filter_by(scope_id=scope.id).order_by(CalculatedField.order_key.desc()).first()
                    order_key = 1
                    if cf_ok:
                        order_key = cf_ok.order_key + 1
                    cf = CalculatedField(
                        name=form.name.data,
                        description=form.description.data,
                        return_type=form.return_type.data,
                        calc_fn=form.fn_code.data,
                        scope_id=scope.id,
                        order_key=order_key
                    )
                    try:
                        db.session.add(cf)
                        db.session.commit()
                        flash(f"Calculated field {form.name.data} stored to database for code {form.field_scope.data}", "info")
                    except Exception as ex:
                        db.session.rollback()
                        flash(f"Can't add {form.name.data}: {ex}", "error")
            except Exception as ex:
                flash(f"{type(ex).__name__}: {ex}", "error")
        laps = data_processor.get_laps_raw()
        lap = laps[-2 if len(laps) > 1 else -1]
        lap = {k: v for k, v in lap.items() if not isinstance(v, dict) and not isinstance(v, list)}
        return self.render('admin/test_calculated_field.html', form=form,
                           current_status=data_processor.get_status_raw(),
                           position=data_processor.get_positions_raw()[-1],
                           lap=lap,
                           charging=data_processor.get_charging_process_list_raw()[-1],
                           total=data_processor.get_total_raw(),
                           forecast=data_processor.get_forecast_raw(),
                           configuration=configuration.dict(),
                           post_url=url_for('test_calculated_field.index'), with_categories=True)


class MyTestLabelFormatTestView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = TestLabelFormatForm()
        from src.db_models import LabelGroup, LabelFormat
        from src import db
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
                if form.add.data:
                    group = LabelGroup.query.filter_by(code=form.label_group.data).first()
                    lf_ok = LabelFormat.query.filter_by(group_id=group.id).order_by(LabelFormat.order_key.desc()).first()
                    order_key = 1
                    if lf_ok:
                        order_key = lf_ok.order_key + 1
                    lf = LabelFormat(
                        label=form.label.data,
                        field=form.field_name.data,
                        format_function=form.format_fn.data,
                        format=form.format.data,
                        unit=form.unit.data,
                        default=form.default.data,
                        group_id=group.id,
                        order_key=order_key
                    )
                    try:
                        db.session.add(lf)
                        db.session.commit()
                        flash(f"Label format {form.field_name.data} stored to database for code {form.label_group.data}", "info")
                    except Exception as ex:
                        db.session.rollback()
                        flash(f"Can't add {form.field_name.data}: {ex}", "error")

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
        return self.render("admin/driver_change.html", form=form)


class ConfigBackupView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = ConfigBackupForm()
        from src import db, configuration
        if form.validate_on_submit():
            now = pendulum.now(tz='utc')

            from src.backup import get_calculated_fields_all, get_label_formats_all, get_drivers, get_driver_changes

            backup = ConfigBackupData(
                configuration=configuration,
                calculated_fields=get_calculated_fields_all(),
                label_formats=get_label_formats_all(),
                drivers=get_drivers(),
                driver_changes=get_driver_changes()
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
        if form.validate_on_submit():
            backup_file = form.backup_file.data
            backup_data = backup_file.read()
            backup = ConfigBackupData.parse_raw(backup_data)
            overwrite_config_file = form.overwrite_config_file.data
            from src import load_config
            if form.restore_config.data:
                load_config(backup.configuration, overwrite_config_file)
                flash("Configuration restored", "info")
                if overwrite_config_file:
                    flash("Configuration file replaced", "info")
            from src.backup import save_calculated_fields_all, save_label_formats_all, save_drivers, save_driver_changes
            if form.restore_calculated_fields.data:
                cnt = save_calculated_fields_all(backup.calculated_fields)
                flash(f" {cnt} calculated fields restored", "info")
            if form.restore_label_formats.data:
                cnt = save_label_formats_all(backup.label_formats)
                flash(f" {cnt} label formats restored", "info")
            if form.restore_drivers.data:
                cnt = save_drivers(backup.drivers)
                flash(f" {cnt} drivers restored", "info")
            if form.restore_driver_changes.data:
                cnt = save_driver_changes(backup.driver_changes)
                flash(f" {cnt} driver changes restored", "info")
        return self.render("admin/config_restore.html", form=form, with_categories=True)


class GenerateJwtTokenView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        api_token = None
        form = GenerateJwtTokenForm()
        if form.validate_on_submit():
            hours = form.hours.data
            from flask_security import current_user
            from datetime import timedelta
            duration = timedelta(hours=hours)
            api_token = create_access_token(identity="api::" + current_user.email, expires_delta=duration)
        else:
            if form.errors:
                for err, err_value in form.errors.items():
                    flash(f"{err}: {err_value}", "error")

        return self.render("admin/generate_jwt_token.html", form=form, with_categories=True, api_token=api_token)


class CreateNewUserView(MyRoleRequiredCustomView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = CreateNewUserForm()
        from src.db_models import Role
        from src import user_datastore, db
        from flask_security import hash_password
        db_roles = Role.query.order_by(Role.name).all()
        roles = [(r.name, r.name) for r in db_roles]
        form.roles.choices = roles

        if form.validate_on_submit():
            try:
                user_datastore.create_user(email=form.email.data, password=hash_password(form.password.data))
                db.session.commit()
                for r in form.roles.data:
                    user_datastore.add_role_to_user(form.email.data, r)
                db.session.commit()

                flash(f"User {form.email.data} created", "info")
            except Exception as ex:
                flash(f"Creating user failed: {ex}", "error")

        return self.render("admin/create_new_user.html", form=form, with_categories=True)
