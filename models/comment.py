from mongoengine import Document, StringField, IntField, DateTimeField
import datetime

class Comment(Document):
    meta = {
        "strict": False
    }
    comment = StringField() # comment là gì
    who_fullname = StringField() # tên đầy đủ người comment
    who_username = StringField() # username
    picid = StringField() # comment của bức tranh nào (dùng id của bức tranh để định danh)
    whencomment = DateTimeField(default=datetime.datetime.now()) # thời gian comment
