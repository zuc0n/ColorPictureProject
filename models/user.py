from mongoengine import Document, StringField, IntField, DateTimeField

class User(Document):
    meta = {
        "strict": False
    }
    fullname = StringField() # Tên đầy đủ
    username = StringField() 
    password = StringField()
    finished_arts = IntField(default=0)
    working_arts = IntField(default=0)
    totallikes = IntField(default=0)
