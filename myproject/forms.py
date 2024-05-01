from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, IntegerField, SelectField
from wtforms.fields.html5 import DateField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired
from wtforms import ValidationError
from datetime import datetime
from myproject.models import User, Trial

def get_trial_choices():
	all_trial_inf = Trial.query.all()
	trial_detail = []
	for trial in all_trial_inf:
		trial_inf = (trial.idTrials, trial.name)
		trial_detail.append(trial_inf)

	return trial_detail


class UserToTrialForm(FlaskForm):
	user_id = SelectField('User', coerce=int, validators=[InputRequired(message="User is required!")])
	#username_confirm = StringField('Confirm The Selected UserName', validators=[InputRequired(message="User Name Confirmation is required!")])
	trial_id = SelectField('Trial', coerce=int, validators=[InputRequired(message="Trial is required!")])
	action = SelectField('Action', coerce=int, choices=[(1, 'Connect'), (0, 'Disconnect')], validators=[InputRequired(message="Action is required!")])
	#trialname_confirm = StringField('Confirm The Selected TrialName', validators=[InputRequired(message="Trial Name Confirmation is required!")])
	submit = SubmitField('Submit')


class PatientLotForm(FlaskForm):
	patient_id = SelectField('Patient ID', coerce=int, validators=[InputRequired(message="Patient Id is required!")])
	lot_id = SelectField('Lot ID', coerce=int, validators=[InputRequired(message="Lot Id is required!")])
	action = SelectField('Action', coerce=int, choices=[(1, 'Connect'), (0, 'Disconnect')], validators=[InputRequired(message="Action is required!")])
	submit = SubmitField('Submit')


class PatientTrialForm(FlaskForm):
	patient_id = SelectField('Patient ID', coerce=int, validators=[InputRequired(message="Patient Id is required!")])
	trial_id = SelectField('Trial Name', coerce=int, validators=[InputRequired(message="Trial Name is required!")])
	action = SelectField('Action', coerce=int, choices=[(1, 'Connect'), (0, 'Disconnect')], validators=[InputRequired(message="Action is required!")])
	submit = SubmitField('Submit')

class PatientForm(FlaskForm):
	patient_id = StringField('Patient Id', validators=[InputRequired(message="Patient Id is required!")])
	patient_wt = DecimalField('Pateint Weight (kg)', validators=[InputRequired(message="Pateint Weight is Required!")])
	submit = SubmitField('Add Patient')

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[InputRequired(message="Username is required!")])
	password = PasswordField('Password', validators=[InputRequired(message="Password is Required!")])
	submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
	
	username = StringField('Username', validators=[InputRequired(message="Username is required!")])
	password = PasswordField('Password', validators=[InputRequired(), EqualTo('confirm_password', message="Passwords must match!")])
	confirm_password = PasswordField('Confirm Password', validators=[InputRequired()])
	fname = StringField('First name', validators=[InputRequired(message="First Name is required!")])
	lname = StringField('Last name', validators=[InputRequired(message="Last Name is required!")])
	email_address = StringField('Email', validators=[InputRequired(message="Email is required!"), Email(message="Invalid Email!")])
	street1 = StringField('Address Line 1', validators=[InputRequired(message="Address Line 1 is required!")])
	street2 = StringField('Address Line 2')
	city =    StringField('City', validators=[InputRequired(message="City is required!")])
	state =  StringField('State', validators=[InputRequired(message="State is required!")])
	zip =    StringField('Zip Code', validators=[InputRequired(message="Zip Code is required!")])
	phone =  StringField('Phone', validators=[InputRequired(message="Phone Number is required!")])
	isLive = StringField('Live Status', validators=[InputRequired(message="Live Status is required!")])
	role_id = StringField('Role Id', validators=[InputRequired(message="Role Id is required!")])
	submit = SubmitField('Register')


class AddNewUserForm(FlaskForm):
	
	all_trial_inf = Trial.query.filter(Trial.isLive!=0).order_by(Trial.name).all()
	trial_detail = []
	for trial in all_trial_inf:
		trial_inf = (trial.idTrials, trial.name)
		trial_detail.append(trial_inf)
	
	fname = StringField('First name', validators=[InputRequired(message="First Name is required!")])
	lname = StringField('Last name', validators=[InputRequired(message="Last Name is required!")])
	email_address = StringField('Email', validators=[InputRequired(message="Email is required!"), Email(message="Invalid Email!")])
	street1 = StringField('Address Line 1', validators=[InputRequired(message="Address Line 1 is required!")])
	street2 = StringField('Address Line 2')
	city =    StringField('City', validators=[InputRequired(message="City is required!")])
	state =  StringField('State', validators=[InputRequired(message="State is required!")])
	zip =    StringField('Zip Code', validators=[InputRequired(message="Zip Code is required!")])
	phone =  StringField('Phone', validators=[InputRequired(message="Phone Number is required!")])
	isLive = StringField('Live Status', validators=[InputRequired(message="Live Status is required!")])
	role_id = StringField('Role Id', validators=[InputRequired(message="Role Id is required!")])
	trial = SelectField(label='Trial', coerce=int, choices=trial_detail, validators=[InputRequired(message="Trial Name is required!")])
	trial_confirm = StringField('Confirm Trial Name', validators=[InputRequired(message="Provide Trial Confirmation!")])
	submit = SubmitField('Add User')


	def check_email(self, field):
		if User.query.filter_by(email_address = field.data).first():
			raise ValidationError("This email is already registered!")
	
	def check_username(self, field):
		if User.query.filter_by(username = field.data).first():
			raise ValidationError("This Username is already taken!")


class LotForm(FlaskForm):
	
	idLot = StringField('Lot ID', validators=[InputRequired(message="Lot Id is required!")])
	lot_number = StringField('Lot Number', validators=[InputRequired(message="Lot Number is required!")])
	potency = IntegerField('Potency', validators=[InputRequired(message="Potency is required!")])
	HCP = DecimalField('HCP', validators=[InputRequired(message="HCP is required!")])
	chloro = DecimalField('Chloro', validators=[InputRequired(message="Chloro is required!")])
	triton = DecimalField('Triton', validators=[InputRequired(message="Triton is required!")])
	endo = DecimalField('Endo', validators=[InputRequired(message="Endo is required!")])
	analysis_date = DateField('Analysis Date', format='%Y-%m-%d', default=datetime.now(), validators=[InputRequired(message="Analysis Date is required!")])
	report_date = DateField('Report Date', format='%Y-%m-%d', default=datetime.now(), validators=[InputRequired(message="Report Date is required!")])
	create_dt = DateTimeField('Create Date', validators=[InputRequired(message="Report Date is required!")], format='%Y-%m-%d %H:%M:%S')
	pH = DecimalField('PH', validators=[InputRequired(message="PH is required!")])
	name = StringField('Lot Name', validators=[InputRequired(message="Lot Name is required!")])
	review_dt = DateField('Review Date')
	created_by = StringField('Created By', validators=[InputRequired(message="Provide the User Id who created this Lot")])
	reviewed_by = IntegerField('Reviewed By (User Id)', validators=[InputRequired(message="Provide the User Id who Reviewed this Lot")])
	submit = SubmitField('Add Lot')
	submit_verify = SubmitField('Verify Lot')

class NewLotForm(FlaskForm):
	lot_number = StringField('Lot Number', validators=[InputRequired(message="Lot Number is required!")])
	potency = IntegerField('Potency', validators=[InputRequired(message="Potency is required!")])
	HCP = DecimalField('HCP', validators=[InputRequired(message="HCP is required!")])
	chloro = DecimalField('Chloro', validators=[InputRequired(message="Chloro is required!")])
	triton = DecimalField('Triton', validators=[InputRequired(message="Triton is required!")])
	endo = DecimalField('Endo', validators=[InputRequired(message="Endo is required!")])
	analysis_date = DateField('Analysis Date', format='%Y-%m-%d', default=datetime.now(), validators=[InputRequired(message="Analysis Date is required!")])
	report_date = DateField('Report Date', format='%Y-%m-%d', default=datetime.now(), validators=[InputRequired(message="Report Date is required!")])
	pH = DecimalField('PH', validators=[InputRequired(message="PH is required!")])
	name = StringField('Lot Name', validators=[InputRequired(message="Lot Name is required!")])
	review_dt = DateField('Review Date')
	created_by = IntegerField('Created By (User Id)', validators=[InputRequired(message="Provide the User Id who created this Lot")])
	submit = SubmitField('Add Lot')


class LotPotencyUpdateForm(FlaskForm):
	idLot = StringField('Lot ID', validators=[InputRequired(message="Lot Id is required!")])
	lot_number = StringField('Lot Number', validators=[InputRequired(message="Lot Number is required!")])
	potency = DecimalField('Provide New Potency (Ex. 350000 or 3.5E10)', validators=[InputRequired(message="Potency is required!")])
	name = StringField('Lot Name', validators=[InputRequired(message="Lot Name is required!")])
	#created_by = IntegerField('Created By (User Id)', validators=[DataRequired(message="Provide the User Id who created this Lot")])
	submit_verify = SubmitField('Update Potency')

class FlagUserForm(FlaskForm):	
	user_id = SelectField('User ID', coerce=int, validators=[InputRequired(message="User Id is required!")])
	action = SelectField('Action', coerce=int, choices=[(1, 'Enable'), (0, 'Disable')], validators=[InputRequired(message="Action is required!")])
	submit = SubmitField('Flag User')

class AddNewSiteForm(FlaskForm):
	all_trial_inf = Trial.query.filter(Trial.isLive!=0).order_by(Trial.name).all()
	trial_detail = []
	for trial in all_trial_inf:
		trial_inf = (trial.idTrials, trial.name)
		trial_detail.append(trial_inf)	
	Descr = StringField('Site Description', validators=[InputRequired(message="Site Description is required!")])
	site_id = StringField('Site ID', validators=[InputRequired(message="Site ID is required!")])
	conftrial = StringField(label='Confirm Trial', validators=[InputRequired(message="Provide Trial Confirmation!")])
	trial = SelectField(label='Trial', coerce=int, choices=trial_detail, validators=[InputRequired(message="Trial Name is required!")])
	submit = SubmitField('Add New Site')

class PatientToSiteForm(FlaskForm):
	patient_id = SelectField('Patient ID', coerce=int, validators=[InputRequired(message="Patient Id is required!")])
	site_id = SelectField('Site ID', coerce=int, validators=[InputRequired(message="Site Id is required!")])
	action = SelectField('Action', coerce=int, choices=[(1, 'Connect'), (0, 'Disconnect')], validators=[InputRequired(message="Action is required!")])
	submit = SubmitField('Submit')
'''
class PatientToSiteForm(FlaskForm):
	patient_id = SelectField('Patient ID', coerce=int, validators=[InputRequired(message="Patient Id is required!")])
	site_id = SelectField('Site ID', coerce=int, validators=[InputRequired(message="Site Id is required!")])
	submit = SubmitField('Submit')
'''

class BoxToFreezerLocForm(FlaskForm):
    boxName = StringField('Box Label', validators=[InputRequired(message="Box Label is required")])
    submit = SubmitField('Submit')

class UserToSiteForm(FlaskForm):
	user_id = SelectField('User ID', coerce=int, validators=[InputRequired(message="User Id is required!")])
	site_id = SelectField('Site ID', coerce=int, validators=[InputRequired(message="Site Id is required!")])
	action = SelectField('Action', coerce=int, choices=[(1, 'Connect'), (0, 'Disconnect')], validators=[InputRequired(message="Action is required!")])
	submit = SubmitField('Submit')

class ChangePasswordForm(FlaskForm):
	user_id = SelectField('User ID', coerce=int, validators=[InputRequired(message="User Id is required!")])
	submit = SubmitField('Submit')

class dosinginstructionForm(FlaskForm):
	patient_id = SelectField('Select Patient ID', coerce=int, validators=[InputRequired(message="Patient Id is required!")])
	submit = SubmitField('Submit')