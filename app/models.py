from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), unique=True, nullable=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    email_verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    reports = db.relationship(
        "DiagnosticReport",
        back_populates="created_by",
        lazy=True,
    )
    patient_profile = db.relationship("Patient", back_populates="portal_user", uselist=False)
    security_profile = db.relationship(
        "UserSecurityProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False, index=True)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    reports = db.relationship(
        "DiagnosticReport",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy=True,
    )
    portal_user = db.relationship("User", back_populates="patient_profile", uselist=False)


class DiagnosticReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    test_name = db.Column(db.String(150), nullable=False)
    test_category = db.Column(db.String(100), nullable=False)
    sample_type = db.Column(db.String(100), nullable=False)
    result_value = db.Column(db.String(120), nullable=False)
    reference_range = db.Column(db.String(120), nullable=True)
    interpretation = db.Column(db.String(40), nullable=False, default="Normal")
    notes = db.Column(db.Text, nullable=True)
    verified_by = db.Column(db.String(150), nullable=True)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    patient = db.relationship("Patient", back_populates="reports")
    created_by = db.relationship("User", back_populates="reports")


class UserSecurityProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False, index=True)
    question = db.Column(db.String(255), nullable=False)
    answer_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = db.relationship("User", back_populates="security_profile")

    def set_answer(self, answer):
        self.answer_hash = generate_password_hash(answer.strip().lower())

    def check_answer(self, answer):
        return check_password_hash(self.answer_hash, answer.strip().lower())
