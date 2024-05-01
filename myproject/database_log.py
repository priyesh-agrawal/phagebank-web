from db import db
import datetime

class LogInfo(db.Model, UserMixin):
    __tablename__ = 'Log_Info'

    idLog = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(40))
    end_point = db.Column(db.String(100))
    parameters = db.Column(db.String(150))
    mysql_query = db.Column(db.String(256))
    executed_from = db.Column(db.String(3))
    execution_time = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    #user_to_usertrial =  db.relationship('UserTrial', backref = 'user_tousertrial', lazy = 'dynamic')

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