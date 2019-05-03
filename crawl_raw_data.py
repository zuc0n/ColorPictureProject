import urllib
import urllib.request
import requests
from bs4 import BeautifulSoup
from models.rawpicture import Rawpicture
import mlab

mlab.connect()

def make_soup(url):
    thepage = urllib.request.urlopen(url)
    soupdata = BeautifulSoup(thepage,"html.parser")
    return soupdata

# soup = make_soup("http://www.coloring-book.info/coloring/coloring_page.php?id=7")
# soup = make_soup("http://www.coloring-book.info/coloring/coloring_page.php?id=4")
# soup = make_soup("http://www.coloring-book.info/coloring/coloring_page.php?id=1")
# soup = make_soup("http://www.coloring-book.info/coloring/coloring_page.php?id=19")
# soup = make_soup("http://www.coloring-book.info/coloring/coloring_page.php?id=20")
# soup = make_soup("http://www.coloring-book.info/coloring/coloring_page.php?id=296")
soup = make_soup("http://www.coloring-book.info/coloring/coloring_page.php?id=129")

infor_list = soup.findAll('img')
sourcelist = []
for i in infor_list:
    if '.jpg' in i.get('src'):
        sourcelist.append(i)
for img in sourcelist:
    temp = img.get('src')
    tmp = temp.replace("_m","").replace("/thumbs","")
    image = "http://www.coloring-book.info/coloring/" + tmp if "http" not in tmp else tmp
    category = ''
    for i in tmp:
        if i != "/":
            category += i
        else:
            break
    picname = tmp.replace(category,'').replace('.jpg', '').replace('/', '')
    rawpic = Rawpicture(picname=picname, piclink=image, category=category)
    rawpic.save()
