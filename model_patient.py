from db import db

class Patient(db.Model):
    __tablename__ = 'patient'

    patient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    create_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_update_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    chat_end = db.Column(db.Boolean, nullable=False, default=False)
    overall_end = db.Column(db.Boolean, nullable=False, default=False)
    chat_log = db.Column(db.Text, nullable=True)
    department_count = db.Column(db.JSON, nullable=True)
    preferences = db.Column(db.JSON, nullable=True)
    preference_step = db.Column(db.Integer, nullable=True, default=0)
    department_count = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f'<Patient {self.patient_id}>'
    
    def __init__(self):
        super().__init__()
