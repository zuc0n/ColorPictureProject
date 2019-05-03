from mongoengine import Document, StringField, IntField, DateTimeField

class Savepicture(Document):
    meta = {
        "strict": False
    }
    picname = StringField(default='noname') # Tên bức tranh
    picstatus = StringField(default='unsave') # working or finished or colorlater
    picartist = StringField(default='noartist') 
    picartistfullname = StringField(default='noartist')
    piclikes = IntField(default=0) 
    piccomments = IntField(default=0) 
    picrawid = StringField() # id của bức ảnh gốc đã tạo nên bức này
    piclink = StringField() # link tranh để hiển thị trên web