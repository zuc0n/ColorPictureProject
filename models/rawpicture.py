from mongoengine import Document, StringField, IntField

class Rawpicture(Document):
    meta = {
        "strict": False
    }
    picname = StringField(default='smt') # Tên ảnh
    piclink = StringField() # Link ảnh để hiển thị
    category = StringField() # Thuộc catetory nào: Animals, Nature, ....
