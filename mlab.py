import mongoengine

# mongodb://<dbuser>:<dbpassword>@ds149479.mlab.com:49479/colorpictures # tài khoản colorpictures

host = "ds149479.mlab.com"
port = 49479
db_name = "colorpictures"
user_name = "admin"
password = "admin1"

def connect():
    mongoengine.connect(db_name, host=host, port=port, username=user_name, password=password)