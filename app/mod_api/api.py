from flask import Flask, Blueprint, jsonify
from flask_restful import Resource, Api, reqparse, abort
from flask_restful import fields, marshal_with
from flask.ext.login import login_required
from app.models import Contact, Project, TimeEntry
from datetime import datetime
from sqlalchemy.sql import func

from .. import db

api_mod = Blueprint('api', __name__, url_prefix = '/api')
api = Api(api_mod)

contact_fields = {
	'id': fields.Integer,
	'name': fields.String,
	'email': fields.String,
	'notes': fields.String,
	'uri': fields.Url('api.contactlist')
}
project_fields = {
	'id': fields.Integer,
	'contact': fields.String,
	'contact_id': fields.String,
	'name': fields.String,
	'notes': fields.String,
	'uri': fields.Url('api.contactlist')	
}
time_entry = {
		'project_name' : fields.String,
		'start' : fields.String,
		'stop' : fields.String,
		'delta' : fields.String,
	}
time_entries = {
	
	'entries' : fields.List(fields.Nested(time_entry)),
	'entries_total' : fields.String
}
def abort_if_dne(model_type, model_id):
	if not db.session.query(model_type).get(model_id):
		abort(404, message="%s %s doesn't exist" % (model_type, model_id))


parser = reqparse.RequestParser()
parser.add_argument('contact_name',  type=str, help='Contact Name')
parser.add_argument('contact_email', type=str, help='Contact Email')
parser.add_argument('contact_notes', type=str, help='Contact Notes')
parser.add_argument('contact_id', type=int, help='Contact ID')

# Single Resources
class TabsContact(Resource):
	@marshal_with(contact_fields)
	def get(self, contact_id):
		abort_if_dne(Contact, contact_id)
		return db.session.query(Contact).get(contact_id)
	@marshal_with(contact_fields)
	def delete(self, contact_id):
		abort_if_dne(Contact, contact_id)
		to_del = Contact.query.get(contact_id)
		db.session.delete(to_del)
		db.session.commit()
		return []
	@marshal_with(contact_fields)
	def put(self, contact_id):
		abort_if_dne(Contact, contact_id)
		args = parser.parse_args()
		c = Contact.query.get(contact_id)
		print(args['contact_name'])
		c.name = args['contact_name']
		c.email = args['contact_email']
		c.notes = args['contact_notes']
		db.session.commit()
		return c

		
class TabsProject(Resource):
	decorators = [login_required]
	@marshal_with(project_fields)
	def get(self, project_id):
		abort_if_dne(Project, contact_id)
		return db.session.query(Project).get(project_id)

class TabsTimeEntry(Resource):
	@marshal_with(time_entry)
	def get(self, contact_id):
		abort_if_dne(TimeEntry, time_entry_id)
		return db.session.query(TimeEntry).get(time_entry_id)


# Collections

class ContactList(Resource):
	decorators = [login_required]
	@marshal_with(contact_fields)
	def get(self):
		return db.session.query(Contact).all()

	@marshal_with(contact_fields)
	def post(self):
		args = parser.parse_args()
		nc = Contact()
		nc.name  = args['contact_name']
		nc.email = args['contact_email']
		nc.notes = args['contact_notes']
		db.session.add(nc)
		db.session.commit()
		return nc , 201

class ProjectList(Resource):
	decorators = [login_required]
	@marshal_with(project_fields)
	def get(self):
		return db.session.query(Project).join(Contact).all()

class TimeEntryList(Resource):
	decorators = [login_required]
	@marshal_with(time_entries)
	def get(self):
		#return [ (x.project.name, x.start.strftime(), lambda: x.stop.strftime('%x %H:%M') or '' ) for x in db.session.query(TimeEntry).join(Project).all() ]
		#dlambda = lambda s : s.stop.strftime('%x %H:%M') or ""
		dl2 = lambda y : y or ''
		def dlambda(s):
			try:
				return s.stop.strftime('%x %H:%M')
			except:
				return ""
		dlist = [ {
					'project_name':x.project.name,
					'start' : x.start.strftime('%x %H:%M'),
					'stop' : dlambda(x),
					'delta': dl2(x.delta) } for x in db.session.query(TimeEntry).join(Project).all() ]
		#raise ValueError(dlist)
		#total = db.session.query(TimeEntry).join(Project).all()
		total = db.session.query(func.sum(TimeEntry.delta).label('entries_total')).first()
		#raise ValueError(total)
		#return [{'time_entries':dlist}] + [{'entries_total': str(total[0])}]
		return [{'entries': dlist , 'entries_total': str(total[0])}]
		#return jsonify(dlist = dlist)

# Setup the API resource routing here
api.add_resource(TabsContact,  '/contact/<contact_id>')
api.add_resource(TabsProject,  '/projects/<project_id>')
api.add_resource(TabsTimeEntry,'/time_entries/<time_entry_id>')
api.add_resource(ContactList,  '/contacts')
api.add_resource(ProjectList,  '/projects')
api.add_resource(TimeEntryList,  '/entries')


