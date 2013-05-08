from flask import Flask, render_template, g, flash, request, redirect, url_for
import MySQLdb as mdb
from datetime import datetime
from dbprocess import dbprocess
from config import state, dayofweek, repeat, tags

app = Flask(__name__)
app.config.from_object('config')
process = dbprocess()

user = {'uid': 1,
		'username': 'James',
		'email': 'James@gmail.com',
		'profile_id': 6,
		'last_loc_name': 'soho',
		'state_id': 2,
		'state_name': 'at work'}

def connect_db():
	return mdb.connect('127.0.0.1', 'root', 'root', 'Jingo_DB', port=8889)

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	g.db.close()

@app.route('/show_all_notes')
def show_all_notes():
	cur = g.db.cursor()
	query_field = "SHOW FIELDS FROM NOTE"
	query_data = "SELECT * FROM NOTE"
	flash(query_data)
	cur.execute(query_field)
	fields = [row[0] for row in cur.fetchall()]
	cur.execute(query_data)
	results = cur.fetchall()
	return render_template('show_notes.html',
		title = 'Show All Notes',
		table = 'NOTES',
		fields = fields,
		results = results)

@app.route('/write_notes', methods=['GET', 'POST'])
def write_notes():
	form_content = {'words': '',
					'startdatetime': '',
					'enddatetime': '',
					'starttime': '',
					'endtime': '',
					'radius': 500,
					'selecttag': '',
					'addtag': ''}
	if request.method == 'POST':
		if not request.form['words']:
			flash("Please input some words.")
		elif not request.form['loc']:
			form_content['words'] = request.form['words']
			flash("Location is required.")
		elif not ((request.form['startdatetime'] and request.form['enddatetime']) or (request.form['starttime'] and request.form['endtime'])):
			form_content['words'] = request.form['words']
			flash("Schedule is required.")
		elif not (request.form['jquery-tagbox-select'] or request.form['jquery-tagbox-text']):
			form_content['words'] = request.form['words']
			flash("Tag is required.")
		else:
			selecttag = request.form['jquery-tagbox-select'].split(',')
			addtag = request.form['jquery-tagbox-text'].split(',')
			loc_id = process.get_location_id(loc=request.form['loc'])
			schedule_id = process.get_schedule_id(repeat=request.form['repeat_sel'], startdatetime=request.form['startdatetime'],
												  enddatetime=request.form['enddatetime'], starttime=request.form['starttime'], 
												  endtime=request.form['endtime'], dow=request.form['dow_sel'])
			process.insert_note(uid=user['uid'], words=request.form['words'], link=request.form['link'], loc_id=loc_id, 
								radius=request.form['radius'], schedule_id=schedule_id, selecttag=selecttag, addtag=addtag)
			return redirect(url_for("show_all_notes"))
	return render_template('write_notes.html',
		user = user,
		dayofweek = dayofweek,
		repeat = repeat,
		tags = tags,
		form_content = form_content)

@app.route('/recieve_notes')
def recieve_notes():
	cur = g.db.cursor()
	query_field = "SHOW FIELDS FROM NOTE"
	query_rec = "CALL recnotesproc (%s, %s, %s)"
	cur.execute(query_field)
	fields = [row[0] for row in cur.fetchall()]
	cur.execute(query_rec, (user['uid'], user['state_id'], user['last_loc_name']))
	results = cur.fetchall()
	flash(user['username'] + " in " + user['last_loc_name'] + " at " + str(datetime.now()) + " recieve following notes.")
	return render_template('show_notes.html',
		title = 'Show Recieve Notes',
		table = 'NOTES',
		fields = fields,
		results = results)

@app.route('/my_notes')
def my_notes():
	cur = g.db.cursor()
	query_field = "SHOW FIELDS FROM NOTE"
	query_my = "SELECT * FROM NOTE WHERE uid = %s"
	cur.execute(query_field)
	fields = [row[0] for row in cur.fetchall()]
	cur.execute(query_my, (user['uid'],))
	results = cur.fetchall()
	flash(user['username'] + " published following notes.")
	return render_template('show_notes.html',
		title = 'Show My Notes',
		table = 'NOTES',
		fields = fields,
		results = results)

@app.route('/filter', methods=['GET', 'POST'])
def filter():
	cur = g.db.cursor()
	if request.method == 'POST':
		valid = True
		state_id = None
		if not request.form['newstate'] and not request.form['state_sel']:
			flash("State is required.")
			valid = False
		elif request.form['state_sel']:
			cur.execute("SELECT state_id FROM STATE WHERE uid = %s AND state_name = %s", (user['uid'], request.form['state_sel']))
			results = cur.fetchone()
			if results is not None:
				state_id = results[0]
			else:
				state_id = process.add_state(user['uid'], request.form['state_sel'])	# add state to db
			user['state_name'] = request.form['state_sel']
		elif request.form['newstate']:
			cur.execute("SELECT state_id FROM STATE WHERE uid = %s AND state_name = %s", (user['uid'], request.form['newstate']))
			results = cur.fetchone()
			if results is not None:
				state_id = results[0]
			else:
				state_id = process.add_state(user['uid'], request.form['newstate'])	# add state to db
			user['state_name'] = request.form['newstate']

		if not ((request.form['startdatetime'] and request.form['enddatetime']) or (request.form['starttime'] and request.form['endtime'])):
			valid = False
			flash("Schedule is required.")

		if valid:
			# add schedule to db
			schedule_id = process.get_schedule_id(repeat=request.form['repeat_sel'], startdatetime=request.form['startdatetime'],
												  enddatetime=request.form['enddatetime'], starttime=request.form['starttime'], 
												  endtime=request.form['endtime'], dow=request.form['dow_sel'])
			if request.form['loc']:
				loc_id = process.get_location_id(loc=request.form['loc'])
			else:
				loc_id = None
			selecttag = request.form['jquery-tagbox-select'].split(',')
			addtag = request.form['jquery-tagbox-text'].split(',')
			# add a new filter
			process.add_filter(state_id=state_id, schedule_id=schedule_id, loc_id=loc_id, filter_radius=request.form['filter_radius'],
								selecttag=selecttag, addtag=addtag)
	fields = ['uid', 'username', 'state_id', 'state_name', 'filter_id', 'filter_radius', 'schedule_id', 'starttime', 'endtime', 'dow_name', 'location_id', 'location_name', 'tag_name']
	query_filter = "SELECT uid, username, state_id, state_name, filter_id, filter_radius, schedule_id, starttime, endtime, dow_name, location_id, location_name, tag_name \
		FROM USER NATURAL JOIN STATE NATURAL JOIN FILTER NATURAL JOIN SCHEDULE NATURAL LEFT JOIN LOCATION NATURAL JOIN DAYOFWEEK NATURAL LEFT JOIN TAGS_IN_FILTER NATURAL LEFT JOIN TAG \
		WHERE dayofweek = dow_id AND uid = %s"
	cur.execute(query_filter, (user['uid'],))
	results = cur.fetchall()
	return render_template('filter.html',
		user = user,
		dayofweek = dayofweek,
		repeat = repeat,
		tags = tags,
		state = state,
		results = results,
		fields = fields)

@app.route('/map')
def map():
	return render_template('map.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
	distance = None
	if request.method == 'POST':
		distance = process.cal_distance(39, 40)
	return render_template('test.html', distance=distance)