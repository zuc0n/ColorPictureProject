from mongoengine import Document, StringField

class Mylistpicture(Document):
    user = StringField()
    art_id = StringField()
    art_type = StringField()