from mongoengine import Document, StringField, IntField, DateTimeField

class Like(Document):
    meta = {
        "strict": False
    }
    who_username = StringField() # ai là người like
    who_fullname = StringField() # tên đầy đủ người like
    picid = StringField() # like của bức tranh nào (dùng id của bức tranh để định danh)
