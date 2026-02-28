from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from app import db
from app.forms import LoginForm, PatientForm, RegisterForm, ReportForm
from app.models import DiagnosticReport, Patient, User

main = Blueprint("main", __name__)


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("main.login"))
        if current_user.role != "admin":
            flash("Admin access is required for this action.", "danger")
            return redirect(url_for("main.dashboard"))
        return view_func(*args, **kwargs)

    return wrapped


@main.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("You are now logged in.", "success")
            return redirect(url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html", form=form)


@main.route("/register", methods=["GET", "POST"])
@login_required
@admin_required
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash("An account with this email already exists.", "danger")
            return render_template("register.html", form=form)

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

    return render_template("register.html", form=form)


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("main.login"))


@main.route("/dashboard")
@login_required
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


@main.route("/patients")
@login_required
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
    reports = (
        DiagnosticReport.query.filter_by(patient_id=patient.id)
        .order_by(DiagnosticReport.reported_at.desc())
        .all()
    )
    return render_template("view_patient.html", patient=patient, reports=reports)


@main.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
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
    return render_template("view_report.html", report=report)
