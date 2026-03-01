from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from app import db
from app.forms import LoginForm, PatientForm, PatientPortalRegisterForm, RegisterForm, ReportForm
from app.models import DiagnosticReport, Patient, User

main = Blueprint("main", __name__)


def _flash_form_errors(form):
    for field_name, errors in form.errors.items():
        if field_name == "csrf_token":
            flash("Session expired. Refresh the page and try again.", "danger")
            continue

        field = getattr(form, field_name, None)
        label = field.label.text if field is not None else field_name.replace("_", " ").title()
        for error in errors:
            flash(f"{label}: {error}", "danger")


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("main.auth"))
        if current_user.role != "admin":
            flash("Admin access is required for this action.", "danger")
            return redirect(url_for("main.dashboard"))
        return view_func(*args, **kwargs)

    return wrapped


def staff_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("main.auth"))
        if current_user.role == "patient":
            flash("Staff or admin access is required for this action.", "danger")
            return redirect(url_for("main.my_reports"))
        return view_func(*args, **kwargs)

    return wrapped


@main.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "patient":
            return redirect(url_for("main.my_reports"))
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.auth", section="user"))


@main.route("/auth", methods=["GET", "POST"])
def auth():
    if current_user.is_authenticated:
        if current_user.role == "patient":
            return redirect(url_for("main.my_reports"))
        return redirect(url_for("main.dashboard"))

    active_section = request.args.get("section", "user")
    admin_login_form = LoginForm(prefix="admin")
    user_login_form = LoginForm(prefix="user")
    patient_form = PatientPortalRegisterForm(prefix="patient")

    if admin_login_form.submit.data:
        if admin_login_form.validate_on_submit():
            user = User.query.filter_by(email=admin_login_form.email.data.lower().strip()).first()
            if user and user.check_password(admin_login_form.password.data):
                if user.role != "admin":
                    flash("This form is only for admin accounts.", "danger")
                    active_section = "admin"
                    return render_template(
                        "auth.html",
                        admin_login_form=admin_login_form,
                        user_login_form=user_login_form,
                        patient_form=patient_form,
                        active_section=active_section,
                    )

                login_user(user)
                flash("Admin logged in successfully.", "success")
                return redirect(url_for("main.dashboard"))
            if User.query.count() == 0:
                flash("No accounts exist yet. Configure default admin credentials and restart.", "warning")
            flash("Invalid admin email or password.", "danger")
            active_section = "admin"
        else:
            _flash_form_errors(admin_login_form)
            active_section = "admin"

    if user_login_form.submit.data:
        if user_login_form.validate_on_submit():
            user = User.query.filter_by(email=user_login_form.email.data.lower().strip()).first()
            if user and user.check_password(user_login_form.password.data):
                if user.role == "admin":
                    flash("Admin accounts must use the Admin Login section.", "warning")
                    return redirect(url_for("main.auth", section="admin"))

                login_user(user)
                flash("You are now logged in.", "success")
                if user.role == "patient":
                    return redirect(url_for("main.my_reports"))
                return redirect(url_for("main.dashboard"))
            if User.query.count() == 0:
                flash("No accounts exist yet. Configure default admin credentials and restart.", "warning")
            flash("Invalid user email or password.", "danger")
            active_section = "user"
        else:
            _flash_form_errors(user_login_form)
            active_section = "user"

    if patient_form.submit.data:
        if patient_form.validate_on_submit():
            patient_code = patient_form.patient_code.data.strip().upper()
            patient_email = patient_form.email.data.lower().strip()
            patient = Patient.query.filter_by(patient_code=patient_code).first()

            if not patient:
                flash("Patient ID was not found. Please contact diagnostics support.", "danger")
                active_section = "register"
                return render_template(
                    "auth.html",
                    admin_login_form=admin_login_form,
                    user_login_form=user_login_form,
                    patient_form=patient_form,
                    active_section=active_section,
                )

            if not patient.email or patient.email.lower().strip() != patient_email:
                flash("Email does not match the patient profile.", "danger")
                active_section = "register"
                return render_template(
                    "auth.html",
                    admin_login_form=admin_login_form,
                    user_login_form=user_login_form,
                    patient_form=patient_form,
                    active_section=active_section,
                )

            if patient.portal_user:
                flash("A portal account already exists for this patient. Please log in.", "warning")
                return redirect(url_for("main.auth", section="user"))

            existing_user = User.query.filter_by(email=patient_email).first()
            if existing_user:
                flash("This email is already used by another account.", "danger")
                active_section = "register"
                return render_template(
                    "auth.html",
                    admin_login_form=admin_login_form,
                    user_login_form=user_login_form,
                    patient_form=patient_form,
                    active_section=active_section,
                )

            user = User(
                username=patient.full_name,
                email=patient_email,
                phone=patient.phone,
                role="patient",
                patient_id=patient.id,
            )
            user.set_password(patient_form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Patient account activated. Please log in.", "success")
            return redirect(url_for("main.auth", section="user"))
        else:
            _flash_form_errors(patient_form)
            active_section = "register"

    return render_template(
        "auth.html",
        admin_login_form=admin_login_form,
        user_login_form=user_login_form,
        patient_form=patient_form,
        active_section=active_section,
    )


@main.route("/login", methods=["GET", "POST"])
def login():
    return redirect(url_for("main.auth", section="user"))


@main.route("/register", methods=["GET", "POST"])
def register():
    return redirect(url_for("main.auth", section="register"))


@main.route("/patient/register", methods=["GET", "POST"])
def patient_register():
    return redirect(url_for("main.auth", section="register"))


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("main.auth"))


@main.route("/dashboard")
@login_required
@staff_required
def dashboard():
    stats = {
        "patients": Patient.query.count(),
        "reports": DiagnosticReport.query.count(),
        "critical_reports": DiagnosticReport.query.filter_by(interpretation="Critical").count(),
    }
    recent_reports = (
        DiagnosticReport.query.order_by(DiagnosticReport.reported_at.desc()).limit(8).all()
    )
    return render_template("home.html", stats=stats, recent_reports=recent_reports)


@main.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users.html", users=all_users)


@main.route("/users/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash("An account with this email already exists.", "danger")
            return render_template("create_user.html", form=form)

        user = User(
            username=form.username.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("User created successfully.", "success")
        return redirect(url_for("main.users"))

    return render_template("create_user.html", form=form)


@main.route("/patients")
@login_required
@staff_required
def list_patients():
    search = request.args.get("q", "").strip()
    query = Patient.query
    if search:
        like_term = f"%{search}%"
        query = query.filter(
            or_(
                Patient.patient_code.ilike(like_term),
                Patient.full_name.ilike(like_term),
                Patient.phone.ilike(like_term),
            )
        )
    patients = query.order_by(Patient.created_at.desc()).all()
    return render_template("patients.html", patients=patients, search=search)


@main.route("/patients/new", methods=["GET", "POST"])
@login_required
@staff_required
def add_patient():
    form = PatientForm()
    if form.validate_on_submit():
        exists = Patient.query.filter_by(patient_code=form.patient_code.data.strip()).first()
        if exists:
            flash("Patient ID already exists.", "danger")
            return render_template("add_patient.html", form=form)

        patient = Patient(
            patient_code=form.patient_code.data.strip().upper(),
            full_name=form.full_name.data.strip(),
            age=form.age.data,
            gender=form.gender.data,
            phone=form.phone.data.strip() if form.phone.data else None,
            email=form.email.data.lower().strip() if form.email.data else None,
        )
        db.session.add(patient)
        db.session.commit()
        flash("Patient profile created.", "success")
        return redirect(url_for("main.view_patient", patient_id=patient.id))
    return render_template("add_patient.html", form=form)


@main.route("/patients/<int:patient_id>")
@login_required
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if current_user.role == "patient" and current_user.patient_id != patient.id:
        flash("You do not have access to this patient record.", "danger")
        return redirect(url_for("main.my_reports"))

    reports = (
        DiagnosticReport.query.filter_by(patient_id=patient.id)
        .order_by(DiagnosticReport.reported_at.desc())
        .all()
    )
    return render_template("view_patient.html", patient=patient, reports=reports)


@main.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
@staff_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        if form.patient_code.data.strip().upper() != patient.patient_code:
            duplicate = Patient.query.filter_by(
                patient_code=form.patient_code.data.strip().upper()
            ).first()
            if duplicate:
                flash("Patient ID already exists.", "danger")
                return render_template("edit_patient.html", form=form, patient=patient)

        patient.patient_code = form.patient_code.data.strip().upper()
        patient.full_name = form.full_name.data.strip()
        patient.age = form.age.data
        patient.gender = form.gender.data
        patient.phone = form.phone.data.strip() if form.phone.data else None
        patient.email = form.email.data.lower().strip() if form.email.data else None
        db.session.commit()
        flash("Patient profile updated.", "success")
        return redirect(url_for("main.view_patient", patient_id=patient.id))
    return render_template("edit_patient.html", form=form, patient=patient)


@main.route("/patients/<int:patient_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash("Patient and related reports deleted.", "info")
    return redirect(url_for("main.list_patients"))


@main.route("/patients/<int:patient_id>/reports/new", methods=["GET", "POST"])
@login_required
@staff_required
def add_report(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = ReportForm()
    if form.validate_on_submit():
        report = DiagnosticReport(
            patient_id=patient.id,
            test_name=form.test_name.data.strip(),
            test_category=form.test_category.data,
            sample_type=form.sample_type.data.strip(),
            result_value=form.result_value.data.strip(),
            reference_range=form.reference_range.data.strip() if form.reference_range.data else None,
            interpretation=form.interpretation.data,
            notes=form.notes.data.strip() if form.notes.data else None,
            verified_by=form.verified_by.data.strip() if form.verified_by.data else None,
            created_by_id=current_user.id,
        )
        db.session.add(report)
        db.session.commit()
        flash("Diagnostic report published.", "success")
        return redirect(url_for("main.view_patient", patient_id=patient.id))
    return render_template("add_report.html", form=form, patient=patient)


@main.route("/reports/<int:report_id>")
@login_required
def view_report(report_id):
    report = DiagnosticReport.query.get_or_404(report_id)
    if current_user.role == "patient" and current_user.patient_id != report.patient_id:
        flash("You do not have access to this report.", "danger")
        return redirect(url_for("main.my_reports"))
    return render_template("view_report.html", report=report)


@main.route("/my-reports")
@login_required
def my_reports():
    if current_user.role != "patient" or not current_user.patient_id:
        return redirect(url_for("main.dashboard"))

    patient = Patient.query.get_or_404(current_user.patient_id)
    reports = (
        DiagnosticReport.query.filter_by(patient_id=patient.id)
        .order_by(DiagnosticReport.reported_at.desc())
        .all()
    )
    return render_template("my_reports.html", patient=patient, reports=reports)
