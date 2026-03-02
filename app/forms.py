from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

from app.validators import normalize_and_validate_email, normalize_and_validate_phone


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=72)])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    username = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField("Phone", validators=[DataRequired(), Length(max=20)])
    role = SelectField(
        "Role",
        choices=[("staff", "Staff"), ("admin", "Admin")],
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=72)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        field.data = normalize_and_validate_email(field.data)

    def validate_phone(self, field):
        field.data = normalize_and_validate_phone(field.data)


class PatientPortalRegisterForm(FlaskForm):
    patient_code = StringField("Patient ID", validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField("Registered Email", validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=72)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Activate Patient Account")

    def validate_email(self, field):
        field.data = normalize_and_validate_email(field.data)


class PatientForm(FlaskForm):
    patient_code = StringField("Patient ID", validators=[DataRequired(), Length(min=3, max=30)])
    full_name = StringField("Patient Name", validators=[DataRequired(), Length(min=2, max=150)])
    age = IntegerField("Age", validators=[DataRequired(), NumberRange(min=0, max=120)])
    gender = SelectField(
        "Gender",
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        validators=[DataRequired()],
    )
    phone = StringField("Phone", validators=[DataRequired(), Length(max=20)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    submit = SubmitField("Save Patient")

    def validate_email(self, field):
        field.data = normalize_and_validate_email(field.data)

    def validate_phone(self, field):
        field.data = normalize_and_validate_phone(field.data)


class ReportForm(FlaskForm):
    test_name = StringField("Test Name", validators=[DataRequired(), Length(max=150)])
    test_category = SelectField(
        "Category",
        choices=[
            ("Hematology", "Hematology"),
            ("Biochemistry", "Biochemistry"),
            ("Microbiology", "Microbiology"),
            ("Radiology", "Radiology"),
            ("Pathology", "Pathology"),
        ],
        validators=[DataRequired()],
    )
    sample_type = StringField("Sample Type", validators=[DataRequired(), Length(max=100)])
    result_value = StringField("Result", validators=[DataRequired(), Length(max=120)])
    reference_range = StringField("Reference Range", validators=[Optional(), Length(max=120)])
    interpretation = SelectField(
        "Interpretation",
        choices=[
            ("Normal", "Normal"),
            ("Abnormal", "Abnormal"),
            ("Critical", "Critical"),
            ("Inconclusive", "Inconclusive"),
        ],
        validators=[DataRequired()],
    )
    verified_by = StringField("Verified By", validators=[Optional(), Length(max=150)])
    notes = TextAreaField("Clinical Notes", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Publish Report")


class SecurityQuestionVerifyForm(FlaskForm):
    answer = StringField("Security Answer", validators=[DataRequired(), Length(min=2, max=255)])
    submit = SubmitField("Verify")


class SecurityQuestionSetupForm(FlaskForm):
    question = StringField("Security Question", validators=[DataRequired(), Length(min=8, max=255)])
    answer = StringField("Security Answer", validators=[DataRequired(), Length(min=2, max=255)])
    submit = SubmitField("Save and Continue")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    submit = SubmitField("Continue")

    def validate_email(self, field):
        field.data = normalize_and_validate_email(field.data)


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=8, max=72)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Reset Password")
