import datetime
from myproject import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)


class User(db.Model, UserMixin):
	__tablename__ = 'User'
	
	idUser = db.Column(db.Integer, primary_key=True, autoincrement=True)
	username = db.Column(db.String(45))
	password = db.Column(db.String(128))
	fname = db.Column(db.String(45))
	lname = db.Column(db.String(45))
	email_address = db.Column(db.String(45))
	street1 = db.Column(db.String(45))
	street2 = db.Column(db.String(45))
	city = db.Column(db.String(45))
	state = db.Column(db.String(45))
	zip = db.Column(db.String(45))
	phone = db.Column(db.String(45))
	create_dt = db.Column(db.DateTime(), default=datetime.datetime)
	isLive = db.Column(db.SmallInteger())
	role_id = db.Column(db.Integer())

	def __init__(self, idUser, username, password, fname, lname, email_address, street1, street2, city, state, zip, phone, create_dt, isLive, role_id):
		
		self.idUser = idUser
		self.username = username
		self.password = generate_password_hash(password)
		self.fname = fname
		self.lname = lname
		self.email_address = email_address
		self.street1 = street1
		self.street2 = street2
		self.city = city
		self.state = state
		self.zip = zip
		self.phone = phone
		self.create_dt = create_dt
		self.isLive = isLive
		self.role_id = role_id

	def check_password(self, password):
		return check_password_hash(self.password, password)
	
	def get_id(self):
		return (self.idUser)

class Lot(db.Model, UserMixin):

	__tablename__ = 'Lot'

	idLot = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	lot_number = db.Column(db.String(45), nullable=False)
	potency = db.Column(db.BigInteger, nullable=False)
	HCP = db.Column(db.Float(), nullable=True)
	Chloro = db.Column(db.Float(), nullable=True)
	Triton = db.Column(db.Float(), nullable=True)
	endo = db.Column(db.Float(), nullable=False)
	analysis_date = db.Column(db.Date(), nullable=True)
	report_date = db.Column(db.Date(), nullable=True)
	create_dt = db.Column(db.DateTime(), nullable=True)		#require changes
	pH = db.Column(db.Float(precision=2), nullable=True)
	name = db.Column(db.String(45), nullable=False)
	review_dt = db.Column(db.DateTime(), nullable=True)
	created_by = db.Column(db.Integer(), nullable=False)
	reviewed_by = db.Column(db.Integer(), nullable=False)
	isLive = db.Column(db.Integer(), nullable=False)

class Patient(db.Model, UserMixin):

	__tablename__ = 'Patient'

	idPatient = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	patient_id = db.Column(db.String(45), nullable=False)
	create_dt = db.Column(db.DateTime(), nullable=False)
	patient_wt = db.Column(db.Float(), nullable=True)
	ulcer_area = db.Column(db.Float(), nullable=True)
	dosing_target = db.Column(db.String(45), nullable=True)
	patient_attributes = db.Column(db.String(255), nullable=True)
	isLive = db.Column(db.Integer(), nullable=True)


class PatientLot(db.Model, UserMixin):

	__tablename__ = 'Patient_Lot'

	idPatient_Lot = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	patient_id = db.Column(db.Integer, nullable=False)
	lot_id = db.Column(db.Integer, nullable=False)
	create_dt = db.Column(db.DateTime(), nullable=False)
	reviewed_by = db.Column(db.Integer, nullable=True)
	reviewed_date = db.Column(db.DateTime(), nullable=True)
	isLive = db.Column(db.Integer, nullable=True)


class Trial(db.Model, UserMixin):

	__tablename__ = 'Trials'

	idTrials = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	name = db.Column(db.String(45), nullable=False)
	descr = db.Column(db.String(45), nullable=False)
	create_dt = db.Column(db.DateTime(), nullable=False)
	isLive = db.Column(db.Integer, nullable=True)


class UserTrial(db.Model, UserMixin):

	__tablename__ = 'User_Trials'

	idUser_Trials = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	trial_id = db.Column(db.Integer, nullable=False)
	user_id = db.Column(db.Integer, nullable=False)
	isLive = db.Column(db.Integer, nullable=True)

class PatientTrial(db.Model, UserMixin):

	__tablename__ = 'Trial_Patient'

	idTrial_Patient = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	trial_id = db.Column(db.Integer, nullable=False)
	patient_id = db.Column(db.Integer, nullable=False)
	isLive = db.Column(db.Integer, nullable=True)
	create_dt = db.Column(db.DateTime(), nullable=False)
	reviewed_by = db.Column(db.Integer, nullable=True)
	reviewed_date = db.Column(db.DateTime(), nullable=True)
	
class LogInfo(db.Model, UserMixin):

	__tablename__ = 'Log_Info'

	idLog = db.Column(db.Integer, primary_key=True, autoincrement=True)
	username = db.Column(db.String(40))
	end_point = db.Column(db.String(100))
	parameters = db.Column(db.String(150))
	mysql_query = db.Column(db.String(256))
	executed_from = db.Column(db.String(3))
	execution_time = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

	def __init__(self, idLog, username, end_point, parameters, mysql_query, executed_from, execution_time):

		self.idLog = idLog
		self.username = username
		self.end_point = end_point
		self.parameters = parameters
		self.mysql_query = mysql_query
		self.executed_from = executed_from
		self.execution_time = execution_time

	def save_to_db(self):
		if self.username != 'fred':
			db.session.add(self)
			db.session.commit()


class Sites(db.Model, UserMixin):

	__tablename__ = 'Sites'

	idSites = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	Descr = db.Column(db.String(45), nullable=False)
	create_dt = db.Column(db.DateTime(), nullable=False)
	site_id = db.Column(db.String(45), nullable=False)
	isLive = db.Column(db.Integer, nullable=True)

class UserSites(db.Model, UserMixin):

	__tablename__ = 'User_Sites'

	idUser_Sites = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	user_id = db.Column(db.String(45), nullable=False)
	site_id = db.Column(db.String(45), nullable=False)
	isLive = db.Column(db.Integer, nullable=True)
	create_dt = db.Column(db.DateTime(), nullable=False)


class TrialSites(db.Model, UserMixin):

	__tablename__ = 'Trial_Sites'

	idTrial_Sites = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	location_id = db.Column(db.String(45), nullable=False)
	trial_id = db.Column(db.String(45), nullable=False)
	isLive = db.Column(db.Integer, nullable=True)

class PatientSites(db.Model, UserMixin):

	__tablename__ = 'Patient_Sites'

	idPatient_Site = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	site_id = db.Column(db.String(45), nullable=False)
	patient_id = db.Column(db.String(45), nullable=False)
	isLive = db.Column(db.Integer, nullable=True)
	create_dt = db.Column(db.DateTime(), nullable=False)
	reviewed_by = db.Column(db.Integer, nullable=True)
	reviewed_date = db.Column(db.DateTime(), nullable=True)
 
class InstructionVerificationLog(db.Model, UserMixin):

	__tablename__ = 'Instruction_Verification_Log'

	idInstruction_Verification_Log = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
	patient_id = db.Column(db.String(45), nullable=False)
	verified_by = db.Column(db.Integer, nullable=True)
	verifyied_dt = db.Column(db.DateTime(), nullable=True)