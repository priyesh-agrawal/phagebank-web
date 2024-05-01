from sqlalchemy.sql.functions import current_user
from myproject import app, db
from flask import render_template, redirect, request, url_for, flash, abort, session, send_file
from flask_login import login_user, login_required, logout_user
import flask_login
from BoxtoFreezerLoc import convertBoxToFreezerLoc
from werkzeug.security import generate_password_hash
from myproject.models import (
						User, Lot, Patient, 
						PatientLot, LogInfo, Trial, 
						UserTrial, PatientTrial, Sites,
						PatientSites, UserSites, TrialSites,
						InstructionVerificationLog)

from myproject.forms import (
						LoginForm, RegistrationForm, LotForm, 
						PatientTrialForm, NewLotForm, PatientForm, 
						PatientLotForm, LotPotencyUpdateForm, FlagUserForm, 
						AddNewUserForm, UserToTrialForm, AddNewSiteForm, 
						PatientToSiteForm, UserToSiteForm, ChangePasswordForm,
						BoxToFreezerLocForm, dosinginstructionForm)

from sqlalchemy import func
import datetime
import traceback
import json
import subprocess
import secrets
import string
import os
from myproject.PhageBankDBModule import send_email_without_attachment

def get_userdict():
	users_lst = User.query.all()
	userdict = {}
	for user in users_lst:
		userdict[user.idUser] = '{} {}'.format(str(user.fname), str(user.lname))
	return userdict

def get_dt_string():
	now = datetime.datetime.now()
	dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
	current_date = now.strftime("%m/%d/%Y")
	return dt_string



def generate_password():
	import secrets
	import string
	#alphabet = string.ascii_letters + string.digits + string.punctuation
	alphabet = string.ascii_letters + string.digits
	password = ''.join(secrets.choice(alphabet) for i in range(15))

	return password


def report_log_to_db(user_id, end_point, params, sql_query):
	
	###REPORTING LOG
	user_inf = User.query.filter(User.idUser==user_id).first()
	user_log = LogInfo(None, user_inf.username, end_point, params, sql_query, 'WEB', get_dt_string())
	user_log.save_to_db()
	###


def update_patient_lot_table(lot_number_toupdate_patient_lot_table, current_lot_id, user_id):
	#select Lot.idLot from Lot where lot_number='CG20011910' and created_by is not Null and reviewed_by is not Null;
	all_lot_ids_for_given_lotnum_tup = db.session.query(Lot.idLot).select_from(Lot).filter(Lot.lot_number==lot_number_toupdate_patient_lot_table).filter(Lot.reviewed_by!=None).filter(Lot.created_by!=None).all()
	all_lot_ids_for_given_lotnum = [int(lot_id_tup[0]) for lot_id_tup in all_lot_ids_for_given_lotnum_tup]
	all_lot_ids_for_given_lotnum = sorted(all_lot_ids_for_given_lotnum, reverse=True)

	most_recent_id = all_lot_ids_for_given_lotnum.pop(0)
	#print('aaa', all_lot_ids_for_given_lotnum)
	try:
		patient_lot_ids_to_update_tup = db.session.query(PatientLot.idPatient_Lot).filter(PatientLot.lot_id.in_(all_lot_ids_for_given_lotnum)).all()
		patient_lot_ids_to_update = [int(lot_id_tup[0]) for lot_id_tup in patient_lot_ids_to_update_tup]
		update_rows_patient_lot = PatientLot.query.filter(PatientLot.idPatient_Lot.in_(patient_lot_ids_to_update)).update({PatientLot.lot_id: most_recent_id})
		#print('xx',patient_lot_ids_to_update)
		patient_lot_ids_to_update_1 = [str(i) for i in patient_lot_ids_to_update]
		patient_lot_ids_to_update_str = ", ".join(patient_lot_ids_to_update_1)
		db.session.commit()
		report_log_to_db(user_id, 'verify', lot_number_toupdate_patient_lot_table, "update Patient_Lot set Patient_Lot.lot_id={} where Patient_Lot.idPatient_Lot in {}".format(str(most_recent_id), patient_lot_ids_to_update_str))
		return 'PatientLot Table Updated Successfully!'
	except Exception as Error:
		return str(Error)



def format_dosing_inf(dosingdata):
	bullet_point = '•'
	import re
	if "PJI" in dosingdata:
		for dosing in ["IV Cycle 1", "IO Cycle 1", "IV Cycle 2", "IA Cycle 2"]:
			for treatment in ["Phage", "Placebo"]:
				dosingdata["PJI"][dosing][treatment]  = re.sub("\\n$", "", dosingdata["PJI"][dosing][treatment] )
				dosingdata["PJI"][dosing][treatment] = re.sub("\\n", "</li><li>", dosingdata["PJI"][dosing][treatment])
				dosingdata["PJI"][dosing][treatment] = re.sub(bullet_point, "", dosingdata["PJI"][dosing][treatment])
				dosingdata["PJI"][dosing][treatment] = "<li>"+dosingdata["PJI"][dosing][treatment]
	elif "DFI" in dosingdata:
		
		for treatment in ["Phage", "Placebo"]:
			dosingdata["DFI"]["IV"][treatment] = re.sub("\\n$", "", dosingdata["DFI"]["IV"][treatment]  )
			dosingdata["DFI"]["IV"][treatment] = re.sub("\\n", "</li><li>", dosingdata["DFI"]["IV"][treatment] )
			dosingdata["DFI"]["IV"][treatment] = re.sub(bullet_point, "", dosingdata["DFI"]["IV"][treatment] )
			dosingdata["DFI"]["IV"][treatment] = "<li>"+dosingdata["DFI"]["IV"][treatment] 
		
		for uarea in dosingdata["DFI"]["Topical"]:
			for treatment in ["Phage", "Placebo"]:
				dosingdata["DFI"]["Topical"][uarea][treatment] = re.sub("\\n$", "", dosingdata["DFI"]["Topical"][uarea][treatment]  )
				dosingdata["DFI"]["Topical"][uarea][treatment] = re.sub("\\n", "</li><li>", dosingdata["DFI"]["Topical"][uarea][treatment] )
				dosingdata["DFI"]["Topical"][uarea][treatment] = re.sub(bullet_point, "", dosingdata["DFI"]["Topical"][uarea][treatment] )
				dosingdata["DFI"]["Topical"][uarea][treatment] = "<li>"+dosingdata["DFI"]["Topical"][uarea][treatment] 
	return dosingdata


@app.before_request
def before_request():
	session.permanent = True
	app.permanent_session_lifetime = datetime.timedelta(minutes=60)



@app.route('/')	  
def index():
	return render_template('index.html', year=datetime.date.today().year)


@app.route('/accessdenied')
@login_required
def accessdenied():
	
	return render_template('accessdenied.html', year=datetime.date.today().year)


@app.route('/welcome')
@login_required
def welcome():
	
	#flash("Welcome {} {}!".format(user_inf.username, str(user_inf.role_id)), 'success')
	return render_template('welcome.html', year=datetime.date.today().year)

#session["_user_id"]
@app.route('/createpatient', methods=['GET', 'POST'])
@login_required
def createpatient():
	#return "<h1>Creating new patient</h1>"
	form = PatientForm()

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	err_msg = None
	if form.validate_on_submit():
		try:
			newPatient = Patient(idPatient = None, 
							patient_id = form.patient_id.data,
							create_dt = get_dt_string(),
							patient_wt = form.patient_wt.data,
							isLive = 1)
		
			db.session.add(newPatient)
			db.session.commit()
			###Adding Patient to Dosing Instruction
			patient_info = Patient.query.filter_by(patient_id=form.patient_id.data).first()
			newDosingInstruction = InstructionVerificationLog(idInstruction_Verification_Log = None,
								patient_id=patient_info.idPatient,
								verified_by = None,
								verifyied_dt = None)
			db.session.add(newDosingInstruction)
			patient_added_msg = "New Patient '{}' Added to the DB Successfully!".format(form.patient_id.data)
			flash(patient_added_msg, 'success')
			report_log_to_db(session["_user_id"], 'createpatient', '{}, {}'.format(str(form.patient_id.data), str(form.patient_wt.data)), "*Adding new Patient to the DB!")
			return redirect(url_for('index'))
		except Exception as Error:
			err_msg = str(Error)
			flash("Error Occured '{}'!".format(err_msg), 'danger')
			return redirect(url_for('createpatient'))
	if form.errors:
		err_msg = str(form.errors)
	
	return render_template('createpatient.html', form=form, err_msg=err_msg, year=datetime.date.today().year)


@app.route('/flaguser', methods=['GET', 'POST'])
@login_required
def flaguser():
	#return "<h1>Creating new patient</h1>"
	form = FlagUserForm()

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	form.user_id.choices = [(user_i.idUser, "{} {} ({})".format(user_i.fname, user_i.lname, user_i.username)) for user_i in User.query.order_by(User.username).all()]

	err_msg = None
	if form.validate_on_submit():
		try:
			user_inf = User.query.filter_by(idUser=form.user_id.data).first()

			if user_inf.isLive == 0 and form.action.data == 0:
				flash(f"The User '{form.user_id.data}' is already disabled in DB!", 'danger')
				return redirect(url_for('flaguser'))
			if user_inf.isLive == 1 and form.action.data == 1:
				flash(f"The User '{form.user_id.data}' is already enabled in DB!", 'danger')
				return redirect(url_for('flaguser'))
			
			user_inf.isLive = form.action.data
			db.session.commit()
			
			user_disabled_msg = f"User with UserId '{form.user_id.data}' Successfully disabled!"
			flash(user_disabled_msg, 'success')
			report_log_to_db(session["_user_id"], 'flaguser', str(form.user_id.data), "*Flagging the User!")
			return redirect(url_for('flaguser'))
		except Exception as Error:
			err_msg = str(Error)
			flash(f"Error Occured '{err_msg}'!", 'danger')
			return redirect(url_for('flaguser'))
	if form.errors:
		err_msg = str(form.errors)
	
	return render_template('flaguser.html', form=form, err_msg=err_msg, year=datetime.date.today().year)



@app.route('/patienttolot', methods=['GET', 'POST'])
@login_required
def patienttolot():
	dt_string = get_dt_string()
	form = PatientLotForm()

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	form.patient_id.choices = [(patient.idPatient, patient.patient_id) for patient in Patient.query.order_by(Patient.patient_id).filter(Patient.isLive!=0).all()]
	
	all_max_lot_ids = db.session.query(func.max(Lot.idLot)).select_from(Lot).filter(Lot.reviewed_by!=None).filter(Lot.isLive!=0).group_by(Lot.lot_number).order_by(Lot.lot_number).all()
	all_max_id_list = [id_tup[0] for id_tup in all_max_lot_ids]
	#all_newest_lots = Lot.query.filter(Lot.idLot.in_(all_max_id_list)).all()
	
	form.lot_id.choices = [(lot.idLot, str(lot.lot_number)+' ('+str(lot.name)+')') for lot in Lot.query.filter(Lot.idLot.in_(all_max_id_list)).order_by(Lot.lot_number).all()]
	#Lot.query.filter(Lot.reviewed_by!=None).order_by(Lot.lot_number).all()]
	err_msg = None
	if form.validate_on_submit():
		try:
			newPatientLot = PatientLot(idPatient_Lot = None, 
							patient_id = int(form.patient_id.data),
							lot_id = int(form.lot_id.data),
							isLive=form.action.data,
							create_dt = get_dt_string())
			
			report_log_to_db(session["_user_id"], 'patienttolot', '{},{}'.format(str(form.patient_id.data), str(form.lot_id.data)), "*Adding Patient-Lot Combination to the DB")
			patient_lot_connection_inf = PatientLot.query.filter(PatientLot.patient_id==form.patient_id.data).filter(PatientLot.lot_id==form.lot_id.data).first()
			if patient_lot_connection_inf:
				if form.action.data == 0:
					if patient_lot_connection_inf.isLive == 0:
						flash("The Patient-Lot Relation Already Removed from DB!", 'danger')
						return redirect(url_for('patienttolot'))
					else:
						patient_lot_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Disconnected the Patient-Lot Relation!", 'success')
						return redirect(url_for('patienttolot'))
				elif form.action.data == 1:
					if patient_lot_connection_inf.isLive == 1:
						flash("The Patient-Lot Relation Already Exists in The Database!", 'danger')
						return redirect(url_for('patienttolot'))
					elif patient_lot_connection_inf.isLive == 0:
						patient_lot_connection_inf.isLive = form.action.data
						checkif_patientid_present = InstructionVerificationLog.query.filter(InstructionVerificationLog.patient_id==patient_lot_connection_inf.patient_id).filter(InstructionVerificationLog.verified_by==None).first()
						if not checkif_patientid_present:
							newDosingInstruction = InstructionVerificationLog(idInstruction_Verification_Log = None, patient_id=patient_lot_connection_inf.patient_id,
								verified_by = None, verifyied_dt = None)
							db.session.add(newDosingInstruction)
						db.session.commit()
						flash("Successfully Updated the Patient-Lot  Relation!", 'success')
						return redirect(url_for('patienttolot'))
			else:
				db.session.add(newPatientLot)
				db.session.commit()
				flash("New Patient-Lot  Relation Added to the DB Successfully!", 'success')
				return redirect(url_for('patienttolot'))			
		except Exception as Error:
			err_msg = str(Error)
			flash("Error Occured '{}'!".format(err_msg), 'danger')
			return redirect(url_for('patienttolot'))
	
	if form.errors:
		err_msg = str(form.errors)
	
	return render_template('patienttolot.html', form=form, err_msg=err_msg, year=datetime.date.today().year)


@app.route('/patienttotrial', methods=['GET', 'POST'])
@login_required
def patienttotrial():
	dt_string = get_dt_string()
	
	form = PatientTrialForm()

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("Permission denied: user {} does not have admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	form.patient_id.choices = [(patient.idPatient, patient.patient_id) for patient in Patient.query.order_by(Patient.patient_id).filter(Patient.isLive!=0).all()]
	
	form.trial_id.choices = [(trial.idTrials, trial.name) for trial in Trial.query.filter(Trial.isLive==1).order_by(Trial.idTrials).all()]
	
	err_msg = None
	if form.validate_on_submit():
		try:
			newPatientTrial = PatientTrial(idTrial_Patient = None, 
							trial_id = int(form.trial_id.data),
							patient_id = int(form.patient_id.data),
							create_dt = get_dt_string(),
							isLive = form.action.data)
			
			report_log_to_db(session["_user_id"], 'patienttotrial', '{},{}'.format(str(form.patient_id.data), str(form.trial_id.data)), "*Adding new Patient-Trial to the DB")
			patient_trial_connection_inf =PatientTrial.query.filter(PatientTrial.patient_id==form.patient_id.data).filter(PatientTrial.trial_id==form.trial_id.data).first()
			if patient_trial_connection_inf:
				if form.action.data == 0:
					if patient_trial_connection_inf.isLive == 0:
						flash("The Patient-Trial Relation Already Removed from DB!", 'danger')
						return redirect(url_for('patienttotrial'))
					else:
						patient_trial_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Disconnected the Patient-Trial Relation!", 'success')
						return redirect(url_for('patienttotrial'))
				elif form.action.data == 1:
					if patient_trial_connection_inf.isLive == 1:
						flash("The Patient-trial Relation Already Exists in The Database!", 'danger')
						return redirect(url_for('patienttotrial'))
					elif patient_trial_connection_inf.isLive == 0:
						patient_trial_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Updated the Patient-Sites  Relation!", 'success')
						return redirect(url_for('patienttotrial'))
			else:
				db.session.add(newPatientTrial)
				db.session.commit()
				flash("New Patient-Sites  Relation Added to the DB Successfully!", 'success')
				return redirect(url_for('patienttotrial'))		
		except Exception as Error:
			err_msg = str(Error)
			flash("Error Occured '{}'!".format(err_msg), 'danger')
			return redirect(url_for('patienttotrial'))
	
	if form.errors:
		err_msg = "Form Error: "+str(form.errors)
	
	return render_template('patienttotrial.html', form=form, err_msg=err_msg, year=datetime.date.today().year)


@app.route('/usertotrial', methods=['GET', 'POST'])
@login_required
def usertotrial():
	dt_string = get_dt_string()
	form = UserToTrialForm()

	loggedin_user_inf_chk = User.query.filter(User.username==flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	form.user_id.choices = [(user_i.idUser, "{} {} ({})".format(user_i.fname, user_i.lname, user_i.username)) for user_i in User.query.filter(User.isLive!=0).order_by(User.username).all()]
	form.trial_id.choices = [(trial_i.idTrials, "{} ({})".format(trial_i.name, trial_i.descr)) for trial_i in Trial.query.filter(Trial.isLive!=0).order_by(Trial.name).all()]
	err_msg = None
	if form.validate_on_submit():
		try:
			newUserTrial = UserTrial(idUser_Trials=None, 
									trial_id=int(form.trial_id.data), 
									user_id=int(form.user_id.data), 
									isLive=form.action.data)
			
			report_log_to_db(session["_user_id"], 'usertotrial', '{},{}'.format(str(form.trial_id.data), str(form.user_id.data)), "*Adding User-Trial Combination to the DB")
			
			user_trial_connection_inf = UserTrial.query.filter(UserTrial.trial_id==form.trial_id.data).filter(UserTrial.user_id==form.user_id.data).first()
			if user_trial_connection_inf:
				if form.action.data == 0:
					if user_trial_connection_inf.isLive == 0:
						flash("The User-Trial Relation Already Removed from DB!", 'danger')
						return redirect(url_for('usertotrial'))
					else:
						user_trial_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Disconnected the User-Trial Relation!", 'success')
						return redirect(url_for('usertotrial'))
				elif form.action.data == 1:
					if user_trial_connection_inf.isLive == 1:
						flash("The User-Trial Relation Already Exists in The Database!", 'danger')
						return redirect(url_for('usertotrial'))
					elif user_trial_connection_inf.isLive == 0:
						user_trial_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Updated the User-Trial Relation!", 'success')
						return redirect(url_for('usertotrial'))

			else:
				db.session.add(newUserTrial)
				db.session.commit()
				flash("New User-Trial Relation Added to the DB Successfully!", 'success')
				return redirect(url_for('usertotrial'))
		
		except Exception as Error:
			err_msg = str(Error)
			flash("Error Occured '{} {}'!".format(err_msg, str(traceback.format_exc())), 'danger')
			return redirect(url_for('usertotrial'))
	
	if form.errors:
		err_msg = str(form.errors)
	
	return render_template('usertotrial.html', form=form, err_msg=err_msg, year=datetime.date.today().year)


@app.route('/verifypatientlot')
@login_required
def verifypatientlot():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	allPatients = Patient.query.all()
	patient_dict = {}
	for patient in allPatients:
		patient_dict[patient.idPatient] = patient.patient_id
	#verifypatienttrial
	lot_dict = {}
	allLot = Lot.query.filter(Lot.reviewed_by!=None).all()
	
	for lot in allLot:
		lot_dict[lot.idLot] = str(lot.lot_number)+' ('+str(lot.name)+')'
	
	all_patient_lot = db.session.query(PatientLot.idPatient_Lot, PatientLot.patient_id, 
						PatientLot.lot_id, PatientLot.create_dt).filter(PatientLot.reviewed_by==None).filter(PatientLot.isLive!=0).all()
	
	return render_template('verifypatientlot.html', patient_lot=all_patient_lot, patient_dict=patient_dict, lot_dict=lot_dict, year=datetime.date.today().year)


@app.route('/verifiedPatientLot/<patientlotid>', methods=['GET', 'POST'])
@login_required
def verifiedPatientLot(patientlotid):

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	err_msg = None
	dt_string = get_dt_string()
	try:
		patient_lot_toverify =PatientLot.query.filter(PatientLot.idPatient_Lot==patientlotid).first()
		patient_lot_toverify.reviewed_by = int(session["_user_id"])
		patient_lot_toverify.reviewed_date = dt_string
		db.session.commit()
		flash("The Patient-Lot has been Successfully Verified!", 'success')
		report_log_to_db(session["_user_id"], 'verifiedPatientLot', '{}'.format(str(patientlotid)), "*Verifying Patient-Lot!")
		return redirect(url_for('verifypatientlot'))
	except Exception as Error:
		report_log_to_db(session["_user_id"], 'verifiedPatientLot', '{}'.format(str(patientlotid)), "*Verifying Patient-Lot!")
		err_msg = "Error Occured! "+str(Error)
	flash(err_msg, 'danger')
	return redirect(url_for('verifypatientlot'))


@app.route('/addnewlot', methods=['GET', 'POST'])
@login_required
def addnewlot():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))


	dt_string = get_dt_string()
	form = NewLotForm()
	err_msg = None
	if form.validate_on_submit():
		try:
			newlot = Lot(idLot=None,
					lot_number=form.lot_number.data,
					potency=form.potency.data,
					HCP = form.HCP.data,
					Chloro = form.chloro.data,
					Triton = form.triton.data,
					endo = form.endo.data,
					analysis_date = form.analysis_date.data,
					report_date = form.report_date.data,
					create_dt = dt_string,
					pH = form.pH.data,
					name = form.name.data,
					review_dt = None,
					created_by = form.created_by.data, 
					isLive=1)		#One by default
					#reviewed_by = form.reviewed_by.data)
		
			db.session.add(newlot)
			db.session.commit()
			#flash('New Lot Added to the DB Successfully!')
			#return redirect(url_for('index'))
			lotadded_msg = "New Lot '{}' Added to the DB Successfully!".format(form.lot_number.data)

			sql_query = "insert into lot values(None, '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'!".format(str(form.lot_number.data),str(form.potency.data),str(form.HCP.data),str(form.chloro.data),str(form.triton.data),str(form.endo.data),str(form.analysis_date.data),str(form.report_date.data),str(dt_string),str(form.pH.data),str(form.name.data),str(None),str(form.created_by.data))
			sql_params = "'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'!".format(str(form.lot_number.data),str(form.potency.data),str(form.HCP.data),str(form.chloro.data),str(form.triton.data),str(form.endo.data),str(form.analysis_date.data),str(form.report_date.data),str(dt_string),str(form.pH.data),str(form.name.data),str(None),str(form.created_by.data))
			
			#sql_query = "New Lot added!"
			#sql_params = "Lot Number: {}".format(str(form.lot_number.data))
			report_log_to_db(session["_user_id"], 'addnewlot', sql_params, sql_query)
			return render_template('lotadded.html', msg=lotadded_msg, year=datetime.date.today().year)
		except Exception as Error:
			err_msg = str(Error)
			#print(err_msg)
	if form.errors:
		err_msg = str(form.errors)
	#print(form.errors)
	return render_template('addnewlot.html', form=form, err_msg=err_msg, year=datetime.date.today().year)

@app.route('/verifylot')
@login_required
def verifylot():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	all_max_ids = db.session.query(func.max(Lot.idLot)).select_from(Lot).group_by(Lot.lot_number).all()
	all_max_id_list = [id_tup[0] for id_tup in all_max_ids]
	all_lots = Lot.query.filter(Lot.idLot.in_(all_max_id_list)).filter(Lot.reviewed_by==None).all()

	#print(userdict)

	return render_template('verifylot.html', lots=all_lots, userdict =get_userdict(), year=datetime.date.today().year)



@app.route('/updatepotency')
@login_required
def updatepotency():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	all_max_ids = db.session.query(func.max(Lot.idLot)).select_from(Lot).group_by(Lot.lot_number).all()
	all_max_id_list = [id_tup[0] for id_tup in all_max_ids]
	all_lots = Lot.query.filter(Lot.idLot.in_(all_max_id_list)).all()

	return render_template('updatepotency.html', lots=all_lots, userdict =get_userdict(), year=datetime.date.today().year)



@app.route('/boxtofreezerloc', methods=['GET', 'POST'])
@login_required
def boxtofreezerloc():

	dt_string = get_dt_string()
	form = BoxToFreezerLocForm()
	err_msg = None
	data = []
	if form.validate_on_submit():
		try:
			converter = convertBoxToFreezerLoc()
			freezerLoc = converter.getFreezerLocfromBox(form.boxName.data.strip())
			if freezerLoc[0] == -1:
				err_msg = "Box Name {} was not found!".format(form.boxName.data.strip())
			return render_template('boxtofreezerloc.html', form=form, err_msg=err_msg, data=freezerLoc, year=datetime.date.today().year)
		except Exception as Error:
			err_msg = str(Error)
	if form.errors:
		err_msg = str(form.errors)

	return render_template('boxtofreezerloc.html', form=form, err_msg=err_msg, data=data, year=datetime.date.today().year)




@app.route('/insert_new_potency/<lotid>', methods=['GET', 'POST'])
@login_required
def insert_new_potency(lotid):

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()
	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	dt_string = get_dt_string()
	form = LotPotencyUpdateForm()
	lot_to_update = Lot.query.filter_by(idLot=lotid).first()
	error_msg = None
	if form.validate_on_submit():
		try:
			existing_lot = Lot.query.filter(Lot.idLot==lotid).first()
			newlot = Lot(idLot=None,
					lot_number = existing_lot.lot_number,
					potency=form.potency.data,
					HCP = existing_lot.HCP,
					Chloro = existing_lot.Chloro,
					Triton = existing_lot.Triton,
					endo = existing_lot.endo,
					analysis_date = existing_lot.analysis_date,
					report_date = existing_lot.report_date,
					create_dt = dt_string,
					pH = existing_lot.pH,
					name = existing_lot.name,
					review_dt = None,
					created_by = existing_lot.created_by,
					reviewed_by = None,
					isLive = existing_lot.isLive)
			db.session.add(newlot)
			db.session.commit()
			#return render_template('potency_inserted.html', msg ="Potency Updated for Lot Id '{}'!".format(lotid))

			flash("Potency Updated for Lot Id '{}'!".format(lotid), 'success')
			#sql_query = "insert into lot values(None, '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'!".format(str(existing_lot.lot_number.data),str(form.potency.data),str(existing_lot.HCP.data),str(existing_lot.chloro.data),str(existing_lot.triton.data),str(existing_lot.endo.data),str(existing_lot.analysis_date.data),str(existing_lot.report_date.data),str(dt_string),str(existing_lot.pH.data),str(existing_lot.name.data),str(existing_lot.review_dt.data),str(existing_lot.created_by.data))
			#sql_params = "'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'!".format(str(existing_lot.lot_number.data),str(form.potency.data),str(existing_lot.HCP.data),str(existing_lot.chloro.data),str(existing_lot.triton.data),str(existing_lot.endo.data),str(existing_lot.analysis_date.data),str(existing_lot.report_date.data),str(dt_string),str(existing_lot.pH.data),str(existing_lot.name.data),str(existing_lot.review_dt.data),str(existing_lot.created_by.data))
			try:
				sql_query = "insert into lot values(None, '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'!".format(str(existing_lot.lot_number),str(form.potency),str(existing_lot.HCP),str(existing_lot.Chloro),str(existing_lot.triton),str(existing_lot.endo),str(existing_lot.analysis_date),str(existing_lot.report_date),str(dt_string),str(existing_lot.pH),str(existing_lot.name),str(existing_lot.review_dt),str(existing_lot.created_by))
				sql_params = "'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'!".format(str(existing_lot.lot_number),str(form.potency),str(existing_lot.HCP),str(existing_lot.Chloro),str(existing_lot.triton),str(existing_lot.endo),str(existing_lot.analysis_date),str(existing_lot.report_date),str(dt_string),str(existing_lot.pH),str(existing_lot.name),str(existing_lot.review_dt),str(existing_lot.created_by))
				report_log_to_db(session["_user_id"], 'insert_new_potency', sql_params, sql_query)
			except Exception as Err:
				error_msg = "Error in Log!"+str(Err)
			return redirect(url_for('updatepotency'))
		except Exception as Err:
			error_msg = "Could not Update The Database!"+str(Err)
	
	return render_template('insert_new_potency.html', lot=lot_to_update, form=form, error=error_msg, userdict =get_userdict(), year=datetime.date.today().year)

@app.route('/verify/<lotid>', methods=['GET', 'POST'])
@login_required
def verify(lotid):

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()
	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	dt_string = get_dt_string()
	form = LotForm()
	lot_to_verify = Lot.query.filter_by(idLot=lotid).first()
	error_msg = None
	if form.validate_on_submit():
		try:

			lot_row = Lot.query.filter(Lot.idLot==lotid).first()
			#lot_row.potency = form.potency.data
			#lot_row.HCP = form.HCP.data,
			#lot_row.Chloro = form.chloro.data
			#lot_row.Triton = form.triton.data
			#lot_row.endo = form.endo.data
			#lot_row.analysis_date = form.analysis_date.data
			#lot_row.report_date = form.report_date.data
			#lot_row.create_dt = form.create_dt.data
			#lot_row.pH = form.pH.data
			#lot_row.name = form.name.data
			lot_number_toupdate_patient_lot_table = form.lot_number.data
			lot_row.review_dt = dt_string
			#lot_row.created_by = form.created_by.data
			lot_row.reviewed_by = form.reviewed_by.data
			
			db.session.commit()
			sql_query  = "update Lot set Lot.reviewed_by={} and Lot.review_dt={} where Lot.idLot={}".format(str(form.reviewed_by.data), str(dt_string), str(lotid))
			sql_params = '{}, {}, {}'.format(str(form.reviewed_by.data), str(dt_string), str(lotid))
			report_log_to_db(session["_user_id"], 'verify', sql_params, sql_query)
			def_msg = update_patient_lot_table(lot_number_toupdate_patient_lot_table, lotid, session["_user_id"])
			
			return render_template('verified.html', msg ="Lot Id '{}' Successfully Verified!".format(lotid), year=datetime.date.today().year)
		except Exception as Err:
			#print("Could not Update The Database!", Err)
			error_msg = "Could not Update The Database!"+str(Err)
	if form.errors:
		error_msg = form.errors
	print(form.errors)
	return render_template('verify.html', lot=lot_to_verify, form=form, error=error_msg, userdict=get_userdict(), year=datetime.date.today().year)


@app.route('/reportlot')
@login_required
def reportlot():
	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()
	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	all_max_lot_ids = db.session.query(func.max(Lot.idLot)).select_from(Lot).group_by(Lot.lot_number).order_by(Lot.lot_number).all()
	all_max_id_list = [id_tup[0] for id_tup in all_max_lot_ids]
	all_newest_lots = Lot.query.filter(Lot.idLot.in_(all_max_id_list)).all()

	print('session', session)
	report_log_to_db(session["_user_id"], 'reportlot', "Not Applicable", "*Getting List of Most Recent Lot!")

	return render_template('reportlot.html', lots=all_newest_lots, userdict=get_userdict(), year=datetime.date.today().year)


@app.route('/report/<lotid>', methods=['GET', 'POST'])
@login_required
def report(lotid):
	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()
	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	lot_detail = Lot.query.filter_by(idLot=lotid).first()
	
	report_log_to_db(session["_user_id"], 'report', str(lotid), "select * from Lot where Lot.idLot={}".format(str(lotid)))
	
	return render_template('report.html', lot=lot_detail, userdict=get_userdict(), year=datetime.date.today().year)


@app.route('/logout')
@login_required
def logout():

	report_log_to_db(session["_user_id"], 'logout', "Not Applicable", "*User Logout.")
	
	logout_user()
	flash("You have successfully Logged out!", 'success')

	return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	dt_string = get_dt_string()
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()

		user_log = LogInfo(None, form.username.data, 'login', str(form.username.data), "*User Login Attempt", 'WEB', dt_string)
		user_log.save_to_db()

		if user is not None:
			if user.isLive == 0:
				error = "User is Disabled!"
				return render_template('login.html', error=error, form=form, year=datetime.date.today().year)
			if user.check_password(form.password.data):
				login_user(user)
				#print('Logged in successfully!')
				next = request.args.get('next')

				if next == None or not next[0]=='/':
					next = url_for('welcome')
			
				return redirect(next)
			
			else:
				error = "Incorrect Credential!"
				return render_template('login.html', error=error, form=form, year=datetime.date.today().year)
		else:
			error = "User does not exists! Please Register First!"
			return render_template('login.html', error=error, form=form, year=datetime.date.today().year)
		
	return render_template('login.html', form=form, year=datetime.date.today().year)

@app.route('/register', methods=['GET', 'POST'])
def register():


	dt_string = get_dt_string()
	form = RegistrationForm()

	if form.validate_on_submit():
		user = User(idUser=None,
					username=form.username.data,
					password=form.password.data,
					fname = form.fname.data,
					lname = form.lname.data,
					email_address = form.email_address.data,
					street1 = form.street1.data,
					street2 = form.street2.data,
					city = form.city.data,
					state = form.state.data,
					zip = form.zip.data,
					phone = form.phone.data,
					create_dt = dt_string,
					isLive = form.isLive.data,
					role_id = form.role_id.data)
		
		#print(user, 'xxx')
		db.session.add(user)
		db.session.commit()
		#flash("User is Registered!")
		#print("User is Registered!")
		
		user_log = LogInfo(None, form.username.data, 'register', " ", "Registering new username '{}'".format(form.username.data), 'WEB', dt_string)
		user_log.save_to_db()

		return redirect(url_for('login'))
	
	
	return render_template('register.html', form=form, year=datetime.date.today().year)


@app.route('/addnewuser', methods=['GET', 'POST'])
@login_required
def addnewuser():
	
	dt_string = get_dt_string()
	form = AddNewUserForm()
	
	loggedin_user_inf = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf.username), 'danger')
		return redirect(url_for('accessdenied'))
		 

	if form.validate_on_submit():
		user_password = generate_password()
		user = User(idUser=None,
					username=form.email_address.data,
					password=user_password,
					fname = form.fname.data,
					lname = form.lname.data,
					email_address = form.email_address.data,
					street1 = form.street1.data,
					street2 = form.street2.data,
					city = form.city.data,
					state = form.state.data,
					zip = form.zip.data,
					phone = form.phone.data,
					create_dt = dt_string,
					isLive = form.isLive.data,
					role_id = form.role_id.data)
		#print(user, 'xxx')
		try:
			all_trial_inf = Trial.query.filter(Trial.isLive!=0).order_by(Trial.name).all()
			trial_detail = {}
			for trial in all_trial_inf:
				trial_detail[trial.name] = trial.idTrials
			
			user_inf = User.query.filter_by(email_address=form.email_address.data).first()
			if form.trial_confirm.data not in trial_detail:
				flash("Incorrect Trial Confirmation!", 'danger')
				return render_template('addnewuser.html', form=form, year=datetime.date.today().year)
			
			elif trial_detail[form.trial_confirm.data] != form.trial.data:
				flash("Trial Name confirmation does not match!", 'danger')
				return render_template('addnewuser.html', form=form, year=datetime.date.today().year)
			
			if user_inf:
				flash("This User already exists!", 'danger')
				return render_template('addnewuser.html', form=form, year=datetime.date.today().year)
			else:
				mail_subject = "Welcome To PhageBank App {}!".format(form.fname.data)
				mail_text = "<html><head></head><body><p>Dear {} {},<br><br>\
				You have been registered to use PhageBank App. Enclosed is your User credentials.<br><br>\
				<b>Username : {}</b><br>\
				<b>Password : {}</b><br><br>\
				Please note that your credentials are specific to you and should not be shared.<br><br>\
				For detailed instructions regarding the app, please see the user guide provided during the pharmacy training.\
				Thank you and if you have any questions, please call <b>1-844-972-0500</b>, or email phagebank@aphage.com<br><br>\
				</p></body></html>".format(form.fname.data, form.lname.data, form.email_address.data, user_password)
				feedback= send_email_without_attachment(form.email_address.data, mail_subject, mail_text)
				
				if feedback == 'success':
					db.session.add(user)
					db.session.commit()
					user_just_added_to_db = User.query.filter_by(username=form.email_address.data).first()
					user_trial_obj = UserTrial(idUser_Trials = None, trial_id = form.trial.data,
					user_id = user_just_added_to_db.idUser, isLive = form.isLive.data)

					db.session.add(user_trial_obj)
					db.session.commit()

					flash("New User has been Successfully Added to DB!", 'success')
				else:
					flash("Invalid Email! eMail could not be sent! {}".format(feedback), 'danger')
				
				return render_template('addnewuser.html', form=form, year=datetime.date.today().year)
				
			user_log = LogInfo(None, form.email_address.data, 'addnewuser', " ", "Adding new User {} {}".format(form.fname.data, form.lname.data), 'WEB', dt_string)
			user_log.save_to_db()
			
		except Exception as Err:
			flash("Error: {}".format(str(Err)), 'danger')
			return render_template('addnewuser.html', form=form, year=datetime.date.today().year)
	return render_template('addnewuser.html', form=form, year=datetime.date.today().year)


@app.route('/addnewsite', methods=['GET', 'POST'])
@login_required
def addnewsite():
	dt_string = get_dt_string()
	form = AddNewSiteForm()
	
	loggedin_user_inf = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf.role_id) != 1:
		flash("User {} does not have Admin privilege!".format(loggedin_user_inf.username), 'danger')
		return redirect(url_for('accessdenied'))
		 
	if form.validate_on_submit():
		site = Sites(idSites=None,
					Descr=form.Descr.data,
					create_dt = dt_string,
					isLive = 1,
					site_id=form.site_id.data)


		all_trial_inf = Trial.query.filter(Trial.isLive!=0).order_by(Trial.name).all()
		trial_detail = {}
		for trial in all_trial_inf:
			trial_detail[trial.name] = trial.idTrials
			
		site_inf = Sites.query.filter_by(site_id=form.site_id.data).first()

		if form.conftrial.data not in trial_detail:
			flash("Incorrect Trial Confirmation!", 'danger')
			return render_template('addnewsite.html', form=form, year=datetime.date.today().year)
			
		elif trial_detail[form.conftrial.data] != form.trial.data:
			flash("Trial Name confirmation does not match!", 'danger')
			return render_template('addnewsite.html', form=form, year=datetime.date.today().year)


		try:		
			db.session.add(site)
			db.session.commit()

			site_just_added_to_db = Sites.query.filter_by(site_id=form.site_id.data).first()
			site_trial_obj = TrialSites(idTrial_Sites = None, trial_id = form.trial.data,
			location_id = site_just_added_to_db.idSites, isLive = 1)

			db.session.add(site_trial_obj)
			db.session.commit()

			flash("New Site has been successfully added to DB!", 'success')
		except Exception as Err:
			flash("Database Error: {}".format(Err), 'danger')
			return render_template('addnewsite.html', form=form, year=datetime.date.today().year)
				
		user_log = LogInfo(None, form.site_id.data, 'addnewsite', " ", "Adding new Site {} {}".format(form.Descr.data, form.site_id.data), 'WEB', dt_string)
		user_log.save_to_db()
			
	return render_template('addnewsite.html', form=form, year=datetime.date.today().year)


@app.route('/usertosite', methods=['GET', 'POST'])
@login_required
def usertosite():
	dt_string = get_dt_string()
	form = UserToSiteForm()

	loggedin_user_inf_chk = User.query.filter(User.username==flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	form.user_id.choices = [(user_i.idUser, "{} {} ({})".format(user_i.fname, user_i.lname, user_i.username)) for user_i in User.query.filter(User.isLive!=0).order_by(User.username).all()]
	form.site_id.choices = [(site_i.idSites, "{} ({})".format(site_i.site_id, site_i.Descr)) for site_i in Sites.query.filter(Sites.isLive!=0).order_by(Sites.site_id).all()]
	err_msg = None
	if form.validate_on_submit():
		try:
			newUserSite = UserSites(idUser_Sites=None, 
									site_id=int(form.site_id.data), 
									user_id=int(form.user_id.data), 
									isLive=form.action.data,
									create_dt = dt_string)
			
			report_log_to_db(session["_user_id"], 'usertosite', '{},{}'.format(str(form.site_id.data), str(form.user_id.data)), "*Adding User-Sites Combination to the DB")
			
			user_trial_connection_inf = UserSites.query.filter(UserSites.site_id==form.site_id.data).filter(UserSites.user_id==form.user_id.data).first()
			if user_trial_connection_inf:
				if form.action.data == 0:
					if user_trial_connection_inf.isLive == 0:
						flash("The User-Sites Relation Already Removed from DB!", 'danger')
						return redirect(url_for('usertosite'))
					else:
						user_trial_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Disconnected the User-Sites Relation!", 'success')
						return redirect(url_for('usertosite'))
				elif form.action.data == 1:
					if user_trial_connection_inf.isLive == 1:
						flash("The User-Sites Relation Already Exists in The Database!", 'danger')
						return redirect(url_for('usertosite'))
					elif user_trial_connection_inf.isLive == 0:
						user_trial_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Updated the User-Sites Relation!", 'success')
						return redirect(url_for('usertosite'))

			else:
				db.session.add(newUserSite)
				db.session.commit()
				flash("New User-Sites Relation Added to the DB Successfully!", 'success')
				return redirect(url_for('usertosite'))
		
		except Exception as Error:
			err_msg = str(Error)
			flash("Error Occured '{} {}'!".format(err_msg, str(traceback.format_exc())), 'danger')
			return redirect(url_for('usertosite'))
	
	if form.errors:
		err_msg = str(form.errors)
	
	return render_template('usertosites.html', form=form, err_msg=err_msg, year=datetime.date.today().year)


@app.route('/patienttosite', methods=['GET', 'POST'])
@login_required
def patienttosite():
	dt_string = get_dt_string()
	form = PatientToSiteForm()

	loggedin_user_inf_chk = User.query.filter(User.username==flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	form.site_id.choices = [(site_i.idSites, "{} ({})".format(site_i.site_id, site_i.Descr)) for site_i in Sites.query.filter(Sites.isLive!=0).order_by(Sites.idSites).all()]
	form.patient_id.choices = [(patient_i.idPatient, patient_i.patient_id) for patient_i in Patient.query.filter(Patient.isLive!=0).order_by(Patient.idPatient).all()]
	err_msg = None
	if form.validate_on_submit():
		try:
			newPatientSite  = PatientSites(idPatient_Site=None, 
									site_id=int(form.site_id.data), 
									patient_id=int(form.patient_id.data), 
									isLive=form.action.data,
									create_dt = dt_string)
			
			report_log_to_db(session["_user_id"], 'patienttosite', '{},{}'.format(str(form.site_id.data), str(form.patient_id.data)), "*Adding Patient-Sites Combination to the DB")
			
			patient_site_connection_inf = PatientSites.query.filter(PatientSites.site_id==form.site_id.data).filter(PatientSites.patient_id==form.patient_id.data).first()
			if patient_site_connection_inf:
				if form.action.data == 0:
					if patient_site_connection_inf.isLive == 0:
						flash("The Patient-Sites Relation Already Removed from DB!", 'danger')
						return redirect(url_for('patienttosite'))
					else:
						patient_site_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Disconnected the Patient-Sites Relation!", 'success')
						return redirect(url_for('patienttosite'))
				elif form.action.data == 1:
					if patient_site_connection_inf.isLive == 1:
						flash("The Patient-Sites Relation Already Exists in The Database!", 'danger')
						return redirect(url_for('patienttosite'))
					elif patient_site_connection_inf.isLive == 0:
						patient_site_connection_inf.isLive = form.action.data
						db.session.commit()
						flash("Successfully Updated the Patient-Sites  Relation!", 'success')
						return redirect(url_for('patienttosite'))

			else:
				db.session.add(newPatientSite)
				db.session.commit()
				flash("New Patient-Sites  Relation Added to the DB Successfully!", 'success')
				return redirect(url_for('patienttosite'))
		
		except Exception as Error:
			err_msg = str(Error)
			flash("Error Occured '{} {}'!".format(err_msg, str(traceback.format_exc())), 'danger')
			return redirect(url_for('patienttosite'))
	
	if form.errors:
		err_msg = str(form.errors)
	
	return render_template('patienttosite.html', form=form, err_msg=err_msg, year=datetime.date.today().year)


@app.route('/verifypatientsite')
@login_required
def verifypatientsite():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	allPatients = Patient.query.filter(Patient.isLive!=0).all()
	patient_dict = {}
	for patient in allPatients:
		patient_dict[patient.idPatient] = patient.patient_id
	
	site_dict = {}
	
	allSite = Sites.query.filter(Sites.isLive!=0).all()
	
	for site in allSite:
		site_dict[site.idSites] = '{} ({})'.format(site.site_id, site.Descr)
	
	all_patient_site = db.session.query(PatientSites.idPatient_Site, PatientSites.patient_id, 
						PatientSites.site_id, PatientSites.create_dt).filter(PatientSites.reviewed_by==None).filter(PatientSites.isLive!=0).all()
	
	return render_template('verifypatientsite.html', patient_site=all_patient_site, patient_dict=patient_dict, site_dict=site_dict, year=datetime.date.today().year)


@app.route('/verifiedPatientSite/<patientsiteid>', methods=['GET', 'POST'])
@login_required
def verifiedPatientSite(patientsiteid):

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	err_msg = None
	dt_string = get_dt_string()
	try:
		patient_site_toverify =PatientSites.query.filter(PatientSites.idPatient_Site==patientsiteid).first()
		patient_site_toverify.reviewed_by = int(session["_user_id"])
		patient_site_toverify.reviewed_date = dt_string
		db.session.commit()
		flash("The Patient-Site has been Successfully Verified!", 'success')
		report_log_to_db(session["_user_id"], 'verifiedPatientSite', '{}'.format(str(patientsiteid)), "*Verifying Patient-Sites!")
		return redirect(url_for('verifypatientsite'))
	except Exception as Error:
		report_log_to_db(session["_user_id"], 'verifiedPatientSite', '{}'.format(str(patientsiteid)), "*Verifying Patient-Sites!")
		err_msg = "Error Occured! "+str(Error)
	flash(err_msg, 'danger')
	return redirect(url_for('verifypatientsite'))

@app.route('/verifypatienttrial')
@login_required
def verifypatienttrial():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	allPatients = Patient.query.filter(Patient.isLive!=0).all()
	patient_dict = {}
	for patient in allPatients:
		patient_dict[patient.idPatient] = patient.patient_id
	
	trial_dict = {}
	allTrial = Trial.query.filter(Trial.isLive!=0).all()
	
	for trial in allTrial:
		trial_dict[trial.idTrials] = '{} ({})'.format(trial.name, trial.descr)
	
	all_patient_trial = db.session.query(PatientTrial.idTrial_Patient, PatientTrial.patient_id, 
						PatientTrial.trial_id, PatientTrial.create_dt).filter(PatientTrial.reviewed_by==None).filter(PatientTrial.isLive!=0).all()
	
	return render_template('verifypatienttrial.html', patient_trial=all_patient_trial, patient_dict=patient_dict, trial_dict=trial_dict, year=datetime.date.today().year)


@app.route('/verifiedPatientTrial/<patienttrialid>', methods=['GET', 'POST'])
@login_required
def verifiedPatientTrial(patienttrialid):

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	err_msg = None
	dt_string = get_dt_string()
	try:
		patient_trial_toverify =PatientTrial.query.filter(PatientTrial.idTrial_Patient==patienttrialid).first()
		patient_trial_toverify.reviewed_by = int(session["_user_id"])
		patient_trial_toverify.reviewed_date = dt_string
		db.session.commit()
		flash("The Patient-Site has been Successfully Verified!", 'success')
		report_log_to_db(session["_user_id"], 'verifiedPatientTrial', '{}'.format(str(patienttrialid)), "*Verifying Patient-Trial!")
		return redirect(url_for('verifypatienttrial'))
	except Exception as Error:
		report_log_to_db(session["_user_id"], 'verifiedPatientTrial', '{}'.format(str(patienttrialid)), "*Verifying Patient-Trial!")
		err_msg = "Error Occured! "+str(Error)
	flash(err_msg, 'danger')
	return redirect(url_for('verifypatienttrial'))


#1 39 40 41
'''
#Both Trails and Site Connections are Present
select Patient.idPatient, Patient.patient_id, Trials.name, Trials.descr, Sites.Descr, Sites.site_id from Patient 
join Trial_Patient on Patient.idPatient = Trial_Patient.patient_id 
join Trials on Trials.idTrials = Trial_Patient.trial_id join Patient_Sites on Patient_Sites.patient_id = Patient.idPatient 
join Sites on Sites.idSites=Patient_Sites.site_id;

#Only Trials Connection is Present.
select Patient.idPatient, Patient.patient_id, Trials.name, Trials.descr from Patient 
join Trial_Patient on Patient.idPatient = Trial_Patient.patient_id 
join Trials on Trials.idTrials = Trial_Patient.trial_id where Patient.idPatient not in (select patient_id from Patient_Sites);

#Only Sites Connection is Present.
select Patient.idPatient, Patient.patient_id, Sites.Descr, Sites.site_id from Patient 
join Patient_Sites on Patient_Sites.patient_id = Patient.idPatient 
join Sites on Sites.idSites=Patient_Sites.site_id where Patient.idPatient not in (select patient_id from Trial_Patient);
'''

@app.route('/patientconnreport')
@login_required
def patientconnreport():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	#Both Trials and Site Connections are Present
	all_patient_sites = PatientSites.query.filter(PatientSites.isLive == 1).all()
	patient_id_list_from_site = []
	for psite in all_patient_sites:
		patient_id_list_from_site.append(psite.patient_id)
	
	all_patient_trails = PatientTrial.query.filter(PatientTrial.isLive == 1).all()
	patient_id_list_from_trial = []
	for ptrial in all_patient_trails:
		patient_id_list_from_trial.append(ptrial.patient_id)
	
	#PatientLot.lot_id.in_(all_lot_ids_for_given_lotnum)
	both_connection_present = db.session.query(Patient.idPatient, Patient.patient_id, Trial.name, Trial.descr, Sites.Descr, Sites.site_id, PatientSites.reviewed_by.label('SiteReview'), PatientTrial.reviewed_by.label('TrialReview')).select_from(Patient).join(PatientTrial, Patient.idPatient == PatientTrial.patient_id).join(Trial, Trial.idTrials == PatientTrial.trial_id).join(PatientSites, PatientSites.patient_id == Patient.idPatient).join(Sites, Sites.idSites == PatientSites.site_id).filter(PatientSites.isLive == 1).filter(PatientTrial.isLive == 1).filter(PatientSites.isLive == 1).all()

	onlytrial_connection_present = db.session.query(Patient.idPatient, Patient.patient_id, Trial.name, Trial.descr, PatientTrial.reviewed_by.label('TrialReview')).select_from(Patient).join(PatientTrial, Patient.idPatient == PatientTrial.patient_id).join(Trial, Trial.idTrials == PatientTrial.trial_id).filter(Patient.idPatient.notin_(patient_id_list_from_site)).filter(PatientTrial.isLive == 1).all()
	
	onlysite_connection_present = db.session.query(Patient.idPatient, Patient.patient_id, Sites.Descr, Sites.site_id, PatientSites.reviewed_by.label('SiteReview')).select_from(Patient).join(PatientSites, Patient.idPatient == PatientSites.patient_id).join(Sites, Sites.idSites == PatientSites.site_id).filter(Patient.idPatient.notin_(patient_id_list_from_trial)).filter(PatientSites.isLive == 1).all()
	no_connection_present =  db.session.query(Patient.idPatient, Patient.patient_id, Trial.name, Trial.descr, Sites.Descr, Sites.site_id).select_from(Patient).join(PatientTrial, Patient.idPatient == PatientTrial.patient_id).join(Trial, Trial.idTrials == PatientTrial.trial_id).join(PatientSites, PatientSites.patient_id == Patient.idPatient).join(Sites, Sites.idSites == PatientSites.site_id).filter(Patient.idPatient.notin_(patient_id_list_from_site)).filter(Patient.idPatient.notin_(patient_id_list_from_trial)).filter(PatientSites.isLive == 1).filter(PatientTrial.isLive == 1).all()
	return render_template('patientconnreport.html', both_connection_present=both_connection_present, onlytrial_connection_present=onlytrial_connection_present, 
													onlysite_connection_present=onlysite_connection_present, no_connection_present=no_connection_present, year=datetime.date.today().year)


@app.route('/userconnreport')
@login_required
def userconnreport():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	#Both Trials and Site Connections are Present
	all_user_sites = UserSites.query.filter(UserSites.isLive == 1).all()
	user_id_list_from_site = []
	for usite in all_user_sites:
		user_id_list_from_site.append(usite.user_id)
	user_id_list_from_site = list(set(user_id_list_from_site))
	
	all_user_trails = UserTrial.query.filter(UserTrial.isLive == 1).all()
	user_id_list_from_trial = []
	for utrial in all_user_trails:
		user_id_list_from_trial.append(utrial.user_id)
	user_id_list_from_trial = list(set(user_id_list_from_trial))
	#PatientLot.lot_id.in_(all_lot_ids_for_given_lotnum)
	#flash(user_id_list_from_trial, 'danger')
	both_connection_present = db.session.query(User.idUser, User.fname, User.lname, User.username, Trial.name, Trial.descr, Sites.Descr, Sites.site_id).select_from(User).join(UserTrial, User.idUser == UserTrial.user_id).join(Trial, Trial.idTrials == UserTrial.trial_id).join(UserSites, UserSites.user_id == User.idUser).join(Sites, Sites.idSites == UserSites.site_id).filter(UserSites.isLive == 1).filter(UserTrial.isLive == 1).filter(User.isLive == 1).filter(Trial.isLive == 1).filter(Sites.isLive == 1).all()

	onlytrial_connection_present = db.session.query(User.idUser, User.fname, User.lname, User.username, Trial.name, Trial.descr).select_from(User).join(UserTrial, User.idUser == UserTrial.user_id).join(Trial, Trial.idTrials == UserTrial.trial_id).filter(User.idUser.notin_(user_id_list_from_site)).filter(UserTrial.isLive == 1).filter(User.isLive == 1).all()
	
	onlysite_connection_present = db.session.query(User.idUser, User.fname, User.lname, User.username, Sites.Descr, Sites.site_id).select_from(User).join(UserSites, User.idUser == UserSites.user_id).join(Sites, Sites.idSites == UserSites.site_id).filter(User.idUser.notin_(user_id_list_from_trial)).filter(UserSites.isLive == 1).filter(User.isLive == 1).all()
	#flash(onlysite_connection_present, 'warning')
	no_connection_present =  db.session.query(User.idUser, User.fname, User.lname, User.username, Trial.name, Trial.descr, Sites.Descr, Sites.site_id).select_from(User).join(UserTrial, User.idUser == UserTrial.user_id).join(Trial, Trial.idTrials == UserTrial.trial_id).join(UserSites, UserSites.user_id == User.idUser).join(Sites, Sites.idSites == UserSites.site_id).filter(User.idUser.notin_(user_id_list_from_site)).filter(User.idUser.notin_(user_id_list_from_trial)).filter(UserSites.isLive == 0).filter(UserTrial.isLive == 0).filter(User.isLive == 1).all()
	return render_template('userconnreport.html', both_connection_present=both_connection_present, onlytrial_connection_present=onlytrial_connection_present, 
													onlysite_connection_present=onlysite_connection_present, no_connection_present=no_connection_present, year=datetime.date.today().year)


@app.route('/changepassword', methods=['GET', 'POST'])
@login_required
def changepassword():
	dt_string = get_dt_string()
	form = ChangePasswordForm()

	loggedin_user_inf_chk = User.query.filter(User.username==flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	form.user_id.choices = [(user_i.idUser, "{} {} ({})".format(user_i.fname, user_i.lname, user_i.email_address)) for user_i in User.query.order_by(User.fname).all()]
	err_msg = None
	if form.validate_on_submit():
		try:
			user_inf = User.query.filter_by(idUser=form.user_id.data).first()
			user_password = generate_password()
			user_inf.password = generate_password_hash(user_password)
			
			mail_subject = "PhageBank App new password -{}!".format(user_inf.fname)
			mail_text = "<html><head></head><body><p>Dear {} {},<br><br>\
				Your password has changed. Enclosed is your new user credentials.<br><br>\
				<b>Username : {}</b><br>\
				<b>Password : {}</b><br><br>\
				Please note that your credentials are specific to you and should not be shared.<br><br>\
				For detailed instructions regarding the app, please see the user guide provided during the pharmacy training.\
				Thank you and if you have any questions, please call <b>1-844-972-0500</b>, or email phagebank@aphage.com<br><br>\
				</p></body></html>".format(user_inf.fname, user_inf.lname, user_inf.email_address, user_password)
			
			feedback = send_email_without_attachment(user_inf.email_address, mail_subject, mail_text)
			if feedback == 'success':
				db.session.commit()			
			
			report_log_to_db(session["_user_id"], 'changepassword', '{}'.format(str(form.user_id.data)), "Changing User Password!")
			flash("User has been emailed their new password!", 'success')
			return redirect(url_for('changepassword'))
		except Exception as Error:
			err_msg = str(Error)
			flash("Error!'{} {}'!".format(err_msg, str(traceback.format_exc())), 'danger')
			return redirect(url_for('changepassword'))
	
	if form.errors:
		err_msg = str(form.errors)
	
	return render_template('changepassword.html', form=form, err_msg=err_msg, year=datetime.date.today().year)


@app.route('/dosinginstruction', methods=['GET', 'POST'])
@login_required
def dosinginstruction():
	dt_string = get_dt_string()
	form = dosinginstructionForm()

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	form.patient_id.choices = [(patient.idPatient, patient.patient_id) for patient in Patient.query.order_by(Patient.patient_id).filter(Patient.isLive!=0).all()]
	dosingdata = {}
	query_patient_id = ''
	
	err_msg = None
	if form.validate_on_submit():
		try:
			
			patient_id = form.patient_id.data
			trial_inf =db.session.query(PatientTrial.trial_id, Patient.idPatient, Patient.patient_id, Trial.name, Trial.descr, PatientTrial.reviewed_by).select_from(PatientTrial).join(Patient, Patient.idPatient==form.patient_id.data).join(Trial, Trial.idTrials==PatientTrial.trial_id).filter(PatientTrial.patient_id==form.patient_id.data).filter(PatientTrial.isLive!=0).first()
			
			site_info = db.session.query(PatientSites.idPatient_Site, PatientSites.site_id, PatientSites.reviewed_by).select_from(PatientSites).filter(PatientSites.patient_id==form.patient_id.data).first()
			
			lot_information = db.session.query(PatientLot.lot_id, Lot.idLot, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.pH, Lot.name, Lot.review_dt, Lot.create_dt, Lot.reviewed_by, PatientLot.reviewed_by.label("PatientLotVerified")).select_from(PatientLot).join(Lot, Lot.idLot==PatientLot.lot_id).filter(PatientLot.patient_id == form.patient_id.data).filter(Lot.reviewed_by!=None).filter(Lot.isLive!=0).filter(PatientLot.isLive!=0).all()
			
			verificationstatus = {"Patient-Site": site_info.reviewed_by, "Patient-Trial": trial_inf.reviewed_by, "Patient-Lot": ""}

			query_patient_id = trial_inf.patient_id
			json_input = []
			for lot_info in lot_information:
				dict_t = {"patient_id": trial_inf.patient_id, "trial_id": trial_inf.trial_id, "trial_descr": trial_inf.descr, "user_id": loggedin_user_inf_chk.username, "trial_name": trial_inf.name, 
				"idLot": lot_info.idLot, "lot_number": lot_info.lot_number, "potency": lot_info.potency, "HCP": lot_info.HCP, "Chloro": lot_info.Chloro, "Triton": lot_info.Triton,
				"endo": lot_info.endo, "analysis_date": lot_info.analysis_date.strftime('%Y-%m-%d'), "report_date": lot_info.report_date.strftime('%Y-%m-%d'), "pH": lot_info.pH, "name": lot_info.name, "review_dt": lot_info.review_dt.strftime('%Y-%m-%d'), 
				"created_by": lot_info.create_dt.strftime('%Y-%m-%d'), "reviewed_by": lot_info.reviewed_by}
				
				json_input.append(dict_t)
				verificationstatus["Patient-Lot"] = lot_info.PatientLotVerified
			
			for ky in verificationstatus:
				if verificationstatus[ky] is None:
					verificationstatus[ky] = 'Unverified'
				else:
					verificationstatus[ky] = 'Verified'

			json_toreturn = {"Lots": json_input}
			#json_toreturn = json.dumps(json_toreturn)
			characters = string.ascii_letters + string.digits
			# Generate a random ID with length 8
			uniqid = ''.join(secrets.choice(characters) for _ in range(4))
			uniqid = trial_inf.patient_id+"-"+uniqid
			json_file_path = os.path.join("TMP", uniqid)
			with open(json_file_path+".json", "w") as FH:
				json.dump(json_toreturn, FH)
			
			###SWIFT CODE
			command = f"/home/ubuntu/phagebankappdbfrontend/CLI_Instructions {json_file_path}"
			output = subprocess.check_output(command, shell=True)
			
			with open(json_file_path+"_out.json", "r") as FH:
				returned_json = json.load(FH)

			dosingdata = format_dosing_inf(returned_json)

			return render_template('dosinginstruction.html', form=form, err_msg=err_msg, dosingdata=dosingdata, verificationstatus=verificationstatus, uniqid=uniqid, year=datetime.date.today())
			flash("Error Occured from CLI Instruction script ( Returned JSON is misformatted) '{}'!".format(err_msg), 'danger')
		except Exception as Error:
			err_msg = str(Error)
			flash("Error Occured from CLI Instruction script ( Returned JSON is misformatted) '{}'!".format(err_msg), 'danger')
			flash(f"Nothing was found for this Patient ID!", 'danger')
			return redirect(url_for('dosinginstruction'))
	
	if form.errors:
		err_msg = str(form.errors)

	return render_template('dosinginstruction.html', form=form, err_msg=err_msg, dosingdata=dosingdata, year=datetime.date.today())





@app.route('/DownloadReport/<filename>', methods=['GET', 'POST'])
@login_required
def DownloadReport(filename):

	try:
		command = f"/home/ubuntu/phagebankappdbfrontend/venv/bin/python pdf_report_creator.py --id  {filename}"
		output = subprocess.check_output(command, shell=True)

		file_path = "/home/ubuntu/phagebankappdbfrontend/TMP"
		pdfReport = f"{filename}-dosing-instruction.pdf"
		file_to_download = os.path.join("/home/ubuntu/phagebankappdbfrontend/TMP", pdfReport)
		return send_file(file_to_download, as_attachment=True)
	except Exception as Error:
		err_msg = str(Error)
		print(Error)
		flash("Error Occured '{}'!".format(err_msg), 'danger')



@app.route('/verifypatientinstruction')
@login_required
def verifypatientinstruction():

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))
	
	
	all_patient_dosin = db.session.query(InstructionVerificationLog.idInstruction_Verification_Log, InstructionVerificationLog.patient_id.label('idPatient'), Patient.patient_id).select_from(Patient).join(InstructionVerificationLog, Patient.idPatient==InstructionVerificationLog.patient_id).filter(InstructionVerificationLog.verified_by==None).filter(Patient.isLive!=0).all()
	
	return render_template('verifypatientinstruction.html', all_patient_dosin=all_patient_dosin, year=datetime.date.today().year)


@app.route('/verifieddosinginstruct/<patientid>', methods=['GET', 'POST'])
@login_required
def verifieddosinginstruct(patientid):

	loggedin_user_inf_chk = User.query.filter_by(username=flask_login.current_user.username).first()

	if int(loggedin_user_inf_chk.role_id) != 1:

		flash("User {} does not have Admin privilege!".format(loggedin_user_inf_chk.username), 'danger')
		return redirect(url_for('accessdenied'))

	err_msg = None
	dt_string = get_dt_string()
	try:
		patient_toverify =InstructionVerificationLog.query.filter(InstructionVerificationLog.idInstruction_Verification_Log==patientid).first()
		patient_toverify.verified_by = int(session["_user_id"])
		patient_toverify.verifyied_dt = dt_string
		db.session.commit()
		flash("The Dosing Instruction for the patient has been Successfully Verified!", 'success')
		report_log_to_db(session["_user_id"], 'verifieddosinginstruct', '{}'.format(str(patientid)), "*Verifying Patient Dosing Instruction!")
		return redirect(url_for('verifypatientinstruction'))
	except Exception as Error:
		report_log_to_db(session["_user_id"], 'verifieddosinginstruct', '{}'.format(str(patientid)), "*Verifying Patient Dosing Instruction!")
		err_msg = "Error Occured! "+str(Error)
	flash(err_msg, 'danger')
	return redirect(url_for('verifypatientinstruction'))



if __name__=='__main__':
   app.run(debug=True, host='0.0.0.0')
