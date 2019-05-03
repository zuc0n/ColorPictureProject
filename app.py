from flask import Flask, request, render_template, session, redirect, url_for, json, jsonify
from flask_session import Session # sử dụng session này để lưu session vào server, cho phép lưu được độ dài lớn hơn, vì session flask chỉ tối đa là 4093 ký tự
# import Q để query nhiều điều kiện cùng lúc
from mongoengine.queryset.visitor import Q
# import các Class
from models.user import User
from models.rawpicture import Rawpicture
from models.savepicture import Savepicture
from models.comment import Comment
from models.like import Like
from models.mylistpicture import Mylistpicture
# import một số hàm chức năng sẽ dùng
from random import choice
import base64
import requests
# Kết nối với database
import mlab
mlab.connect()

# Hàm chuyển link ảnh sang định dạng base64
def base64encode(url):
    link1 = base64.b64encode(requests.get(url).content)
    link2 = str(link1)
    link = link2.replace("b'","data:image/jpeg;base64,").replace("'","")
    return link

app = Flask(__name__)
app.config['SECRET_KEY'] = 'teamcolorpictures'
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

@app.route('/') # Hiển thị trang chủ
def home():
    return render_template('homepage.html')

@app.route('/signup', methods=['GET', 'POST']) # Trang đăng ký tài khoản
def signup():
    username_list = User.objects().distinct('username')
    if 'token' in session:
        return render_template('homepage.html')
    if request.method == 'GET':
        return render_template("signup.html", username_list=username_list)
    else:
        form = request.form
        f = form['fullname']
        u = form['username']
        p = form['password']
        # # Tạm bỏ email cùng các phần liên quan bên dưới. 
        # # Khi nào cần thì bật lại vì trên database vẫn để email với giá trị default.
        # e = form['email']
        new_user = User(fullname=f.strip(), username=u.strip(), password=p.strip()) #, email=e)
        new_user.save()
        session['token'] = u
        # Đăng ký xong thì trả về giao diện trang Welcome
        return render_template('welcome.html', fullname=f, u=u)

@app.route('/login', methods=['GET', 'POST']) # Trang đăng nhập
def login():
    user_list = User.objects()
    user_list_2 = {}
    for u in user_list:
        user_list_2[u.username] = u.password
    users = json.dumps(user_list_2) # chuyển python dictionaty sang JSON object
    if 'token' in session:
        return render_template('homepage.html')
    if request.method == 'GET':
        return render_template('login.html', users=users)
    else:
        form = request.form
        u = form['username']
        p = form['password']
        # phần code bên dưới bị comment vì đã xử được trực tiếp bằng javascript trong html
        # user_check = User.objects(username=u).first()
        # # Check xem có nhập username và password hay không và nhập đúng hay không:
        # warning = ''
        # if user_check is None:
        #     warning = 'Username không tồn tại!'
        # else:
        #     if p != user_check.password:
        #         warning = 'Password sai!'
        # if warning != '':
        #     return render_template('login.html', warning=warning, users=users)
        # else:
        session['token'] = u
        # Đăng nhập đúng thì trả về giao diện trang Welcome
        return render_template('welcome.html', fullname=User.objects(username=u).first().fullname, u=u) 

@app.route('/logout') # Đăng xuất
def logout():
    if 'token' in session:
        del session['token']
    if 'picid' in session:
        del session['picid']
    # session.clear() # xóa toàn bộ session
    return redirect(url_for('home'))

@app.route('/top100pics') # Hiển thị 100 Pics đc nhiều like nhất
def top100pics():
    notice = ''
    top100pics = []
    # Tìm những bức tranh có like khác 0:
    finished_list = Savepicture.objects(picstatus='finished', piclikes__ne=0).order_by('-piclikes')
    if len(finished_list) == 0:
        notice = 'Danh sách trống'
    for i, v in enumerate(finished_list):
        if i == 100:
            break
        # Đưa các thông tin của pic đó vào list top 100 pics:
        toppic = {
            'picpositionintop100': i + 1,
            'picname': v.picname,
            'piclink': v.piclink,
            'piclikes': v.piclikes, 
            'picartistfullname': v.picartistfullname,
            'picartist': v.picartist,
            'picid': v.id
        }
        top100pics.append(toppic)
    return render_template('top100pics.html', notice=notice, top100pics=top100pics)

@app.route('/top100artists') # Hiển thị 100 Artists đc nhiều like nhất
def top100artists():
    notice = ''
    top100artists = []
    # Tìm tất cả các artist:
    artist_list = User.objects(totallikes__ne=0).order_by('-totallikes')
    if len(artist_list) == 0:
        notice = 'Danh sách trống'
    for i, artist in enumerate(artist_list):
        if i == 100:
            break
        # Tìm bức tranh có nhiều like nhất của artist đó:
        bestpic = Savepicture.objects(picartist=artist.username, picstatus='finished').order_by('-piclikes').first()
        topartist = {
            'positionintop100': i + 1,
            'fullname': artist.fullname,
            'username': artist.username,
            'totallikes': artist.totallikes,
            'bestpiclink': bestpic.piclink,
            'bestpicid': bestpic.id
        }
        top100artists.append(topartist)
    return render_template('top100artists.html', notice=notice, top100artists=top100artists)

@app.route('/room_of_fame') # Hiển thị tất cả những bức ảnh finished để cộng đồng vào xem và like
def room_of_fame():
    notice = ''
    piclist = Savepicture.objects(picstatus='finished').order_by('piclikes')
    if len(piclist) == 0:
        notice = 'Danh sách trống'
    return render_template('room_of_fame.html', notice=notice, piclist=piclist)

@app.route('/view/<picid>', methods=['GET', 'POST']) # Hiển thị 1 bức tranh đã hoàn thành để like và comment theo id của bức tranh đó
def view(picid):
    pic = Savepicture.objects(id=picid).first()
    picname = pic.picname
    piclikes = pic.piclikes
    artist = User.objects(username=pic.picartist).first()
    comment_list = Comment.objects(picid=picid)
    warning = 'hide'
    likebutton = 'Like'
    display = 'no'
    token = ''
    changename_warning = ''
    addbutton = 'Add to My Favorite'
    if 'token' not in session:
        warning = 'show'
        token = ''
        display = 'no'
    else:
        warning = 'hide'
        token = session['token']
        if session['token'] == artist.username:
            display = 'yes'
        else: 
            display = 'no'
    if request.method == 'GET':
        if 'token' in session:
            like_check = Like.objects(who_username=session['token'], picid=picid).first()
            f_check = Mylistpicture.objects(user=session['token'], art_id=picid, art_type='favorite').first()
            if  like_check is None :
                likebutton = 'Like'
            else:
                likebutton = 'Dislike'
            if f_check is None:
                addbutton = 'Add to My favorite'
            else:
                addbutton = 'Remove from My Favorite'
        return render_template("view.html", changename_warning=changename_warning,  display=display, token=token, pic=pic, picname=picname, piclikes=piclikes, artist=artist, comment_list=comment_list, likebutton=likebutton, warning=warning, addbutton=addbutton)
    elif request.method == 'POST':
        form = request.form
        user = User.objects(username=session['token']).first()
        like_check = Like.objects(who_username=session['token'], picid=picid).first()
        # Xử lý đổi tên:
        if 'picname' in form:
            newname = form['picname']
            if newname.strip() != '':
                picname = newname.strip()
                pic.update(set__picname=newname.strip())
                changename_warning = 'Thay đổi tên thành công!'
        # Xử lý form comment:
        if 'comment' in form:
            if  like_check is None :
                likebutton = 'Like'
            else:
                likebutton = 'Dislike'
            comment = form['comment']
            new_comment = Comment(comment=comment, who_fullname=user.fullname, who_username=user.username, picid=picid)
            pic.update(set__piccomments=pic.piccomments + 1)
            new_comment.save()
        # Xóa comment:
        for comment in comment_list:
            c = 'c' + str(comment.id)
            if c in form:
                c_id = form[c]
                comt = Comment.objects(id=c_id).first()
                pic = Savepicture.objects(id=comt.picid).first()
                number_of_comt = pic.piccomments
                comt.delete()
                pic.update(set__piccomments=number_of_comt - 1)
        # Xử lý form like:
        if 'like' in form:
            if  like_check is None:
                piclikes = pic.piclikes + 1
                # Update like vào số like của bức tranh và của user vẽ bức tranh đó:
                pic.update(set__piclikes=pic.piclikes + 1)
                artist.update(set__totallikes=artist.totallikes + 1)
                # Lưu like vào data:
                new_like = Like(who_fullname=user.fullname, who_username=session['token'], picid=picid)
                new_like.save()
                likebutton = 'Dislike' # chuyển thành nút dislike
            else:
                piclikes = pic.piclikes - 1
                # Update like vào số like của bức tranh và của user vẽ bức tranh đó:
                pic.update(set__piclikes=pic.piclikes - 1)
                artist.update(set__totallikes=artist.totallikes - 1)
                # Xóa like khỏi database
                like_check.delete()
                likebutton == 'Like' # chuyển thành nút like
        # Lưu ảnh vào album yêu thích:
        f_check = Mylistpicture.objects(user=session['token'], art_id=picid, art_type='favorite').first()
        if 'favorite' in form:
            if f_check is None:
                new_favorite = Mylistpicture(user=session['token'], art_id=picid, art_type='favorite')
                new_favorite.save()
                addbutton = 'Delete from My favorite'
            else:
                f_check.delete()
                addbutton = 'Add to My favorite'
        comment_list = Comment.objects(picid=picid)
        return render_template('view.html', changename_warning=changename_warning, display=display, token=token, pic=pic, picname=picname, piclikes=piclikes, artist=artist, comment_list=comment_list, warning=warning, likebutton=likebutton, addbutton=addbutton)

@app.route('/category') # Hiển thị trang Category tổng
def full_category():
    # Lấy id của 1 random pic, sử dụng trong mục Get me a random pic:
    pic_list = Rawpicture.objects()
    random_pic = choice(pic_list)
    categories = ['Aladdin', 'Christmas', 'Cinderella', 'Angry-Birds', 'Dragon Ball Z', 'Ben-10', 'Adiboo', '101 Dalmatians']
    category_list = []
    for c in categories:
        piclink = Rawpicture.objects(category__icontains=c).first().piclink
        category = {'category': c, 'name': c.replace('-',' ').title(), 'label': piclink}
        category_list.append(category)
    return render_template('category.html', random_pic=random_pic, category_list=category_list)

@app.route('/category/<category>', methods = ['GET', 'POST']) # Hiển thị 1 trang category cụ thể
def one_category(category):
    pic_list = Rawpicture.objects(category__icontains=category)
    cap_category = category.replace('-',' ').title()
    button_list = []
    later_list = []
    if 'token' in session:
        later_list = Mylistpicture.objects(user=session['token'], art_type='colorlater')
        for l in later_list:
            a = Rawpicture.objects(id=l.art_id).first()
            button_list.append(a.id)
    if request.method == 'GET':
        return render_template('one_category.html', pic_list=pic_list, category=cap_category, button_list=button_list)
    if request.method == 'POST':
        form = request.form
        for pic in pic_list:
            a = 'a' + str(pic.id)
            if a in form:
                a_id = form[a]
                colorlater_check = Mylistpicture.objects(user=session['token'], art_id=a_id, art_type='colorlater').first()
                a_pic = Rawpicture.objects(id=a_id).first()
                if colorlater_check is None:
                    new_later = Mylistpicture(user=session['token'], art_id=a_id, art_type='colorlater')
                    new_later.save()
                    button_list.append(a_pic.id)
                else:
                    colorlater_check.delete()
                    button_list.remove(a_pic.id)
        return render_template('one_category.html', pic_list=pic_list, category=cap_category, button_list=button_list)

@app.route('/profile/<artist>', methods=['GET', 'POST']) # Hiển thị profile
def profile(artist):
    artist_infor = User.objects(username=artist).first()
    working_arts = artist_infor.working_arts
    finished_arts = artist_infor.finished_arts
    totallikes = artist_infor.totallikes
    finished_list = Savepicture.objects(picartist=artist, picstatus='finished') # .order_by('-piclikes')
    working_list = Savepicture.objects(picartist=artist, picstatus='working')
    colorlaters = Mylistpicture.objects(user=artist, art_type='colorlater')
    colorlater_list = []
    for c in colorlaters:
        pic = Rawpicture.objects(id=c.art_id).first()
        colorlater_list.append(pic)
    c_length = len(colorlater_list)
    favorites = Mylistpicture.objects(user=artist, art_type='favorite')
    favorite_list = []
    for m in favorites:
        pic = Savepicture.objects(id=m.art_id).first()
        favorite_list.append(pic)
    m_length = len(favorite_list)
    display = 'no'
    if 'token' in session:
        if session['token'] == artist:
            display = 'yes'
    if request.method == 'GET':
        return render_template('profile.html', m_length=m_length, c_length=c_length, display=display, artist_infor=artist_infor, working_arts=working_arts, finished_arts=finished_arts, totallikes=totallikes, finished_list=finished_list, working_list=working_list, colorlater_list=colorlater_list, favorite_list=favorite_list)
    elif request.method == 'POST':
        form = request.form
        for fpic in finished_list:
            df = 'df' + str(fpic.id)
            if df in form:
                f_picid = form[df]
                pic = Savepicture.objects(id=f_picid).first()
                pic.delete()
                finished_arts = artist_infor.finished_arts - 1
                totallikes = artist_infor.totallikes - pic.piclikes
                artist_infor.update(set__finished_arts=artist_infor.finished_arts - 1, set__totallikes=artist_infor.totallikes - pic.piclikes)
        for wpic in working_list:
            up = 'up' + str(wpic.id)
            dw = 'dw' + str(wpic.id)
            if up in form:
                u_picid = form[up]
                Savepicture.objects(id=u_picid).first().update(set__picstatus="finished")
                working_arts = artist_infor.working_arts - 1
                artist_infor.update(set__working_arts=artist_infor.working_arts - 1)
                finished_arts = artist_infor.finished_arts + 1
                artist_infor.update(set__finished_arts = artist_infor.finished_arts + 1)
            if dw in form:
                w_picid = form[dw]
                Savepicture.objects(id=w_picid).first().delete()
                working_arts = artist_infor.working_arts - 1
                artist_infor.update(set__working_arts=artist_infor.working_arts - 1)
        for pic in colorlater_list:
            c = 'c' + str(pic.id)
            if c in form:
                c_id = form[c]
                art = Mylistpicture.objects(art_id=c_id).first()
                art.delete()
        for pic in favorite_list:
            m = 'm' + str(pic.id)
            if m in form:
                m_id = form[m]
                art = Mylistpicture.objects(art_id=m_id).first()
                art.delete()
        finished_list = Savepicture.objects(picartist=artist, picstatus='finished') # .order_by('-piclikes')
        working_list = Savepicture.objects(picartist=artist, picstatus='working')
        colorlaters = Mylistpicture.objects(user=artist, art_type='colorlater')
        colorlater_list = []
        for c in colorlaters:
            pic = Rawpicture.objects(id=c.art_id).first()
            colorlater_list.append(pic)
        c_length = len(colorlater_list)
        favorites = Mylistpicture.objects(user=artist, art_type='favorite')
        favorite_list = []
        for m in favorites:
            pic = Savepicture.objects(id=m.art_id).first()
            favorite_list.append(pic)
        m_length = len(favorite_list)
        return render_template('profile.html', m_length=m_length, c_length=c_length, display=display, artist_infor=artist_infor, working_arts=working_arts, finished_arts=finished_arts, totallikes=totallikes, finished_list=finished_list, working_list=working_list, colorlater_list=colorlater_list, favorite_list=favorite_list)

@app.route('/new_picture/<picid>', methods=['GET', 'POST']) # Hiển thị trang vẽ tranh của 1 bức tranh theo id của bức tranh đó
def new_picture(picid):
    pic = Rawpicture.objects(id=picid).first()
    piclinkb64 = base64encode(pic.piclink)
    token = ''
    if request.method == 'GET':
        if 'token' in session:
            token = session['token']
        if 'picid' in session:
            if ("'" + picid + "'") in session['picid']:
                unsavelink = session['picid'].replace("'" + picid + "'",'')
                del session['picid']
                return render_template('new_picture.html', piclinkb64=unsavelink, resetlinkb64=piclinkb64, token=token)
            else: 
                return render_template('new_picture.html', piclinkb64=piclinkb64, resetlinkb64=piclinkb64, token=token)
        else:
            return render_template('new_picture.html', piclinkb64=piclinkb64, resetlinkb64=piclinkb64, token=token)
    elif request.method == 'POST':
        form = request.form
        # nếu người dùng chưa đăng nhập:
        if 'token' not in session:
            unsavelink = form['unsavelink']
            session['picid'] = "'" + picid + "'" + unsavelink # thêm dấu nháy bọc quanh picid để phòng trường hợp trong chuỗi base64 có 1 đoạn ký tự trùng với picid
            return redirect(url_for('login'))
        # nếu người dùng đã đăng nhập:
        if 'token' in session:
            token = session['token']
            picname = form['picname']
            piclink = form['piclink']
            picstatus = form['picstatus']
            picartist = token
            picartistfullname = User.objects(username=token).first().fullname
            newlink = Savepicture(piclink=piclink, picname=picname.strip(), picstatus=picstatus, picartist=picartist, picartistfullname=picartistfullname, picrawid=picid)
            newlink.save()
            newid = Savepicture.objects(piclink=piclink).first().id
            # Update database của user tương ứng:
            working_arts = User.objects(username=token).first().working_arts
            finished_arts = User.objects(username=token).first().finished_arts
            if picstatus == 'working':
                User.objects(username=token).first().update(set__working_arts=working_arts+1)
            elif picstatus == 'finished':
                User.objects(username=token).first().update(set__finished_arts=finished_arts+1)
            return redirect(url_for('saved', picid=newid))

@app.route('/keep_continue/<picid>', methods=['GET', 'POST']) # Trang vẽ tiếp 1 bức đang vẽ dở
def keep_continue(picid):
    token = ''
    if 'token' not in session:
        return redirect(url_for('login'))
    else:
        if session['token'] != Savepicture.objects(id=picid).first().picartist:
            return render_template('not_allow.html')
        else:
            token = session['token']
            pic = Savepicture.objects(id=picid).first()
            piclinkb64 = pic.piclink
            if request.method == 'GET':
                return render_template('keep_continue.html', pic=pic, piclinkb64=piclinkb64, token=token)
            elif request.method == 'POST':
                form = request.form
                picname = form['picname']
                piclink = form['piclink']
                picstatus = form['picstatus']
                # Update:
                if picname.strip() != '':
                    pic.update(set__picname=picname.strip())
                working_arts = User.objects(username=token).first().working_arts
                finished_arts = User.objects(username=token).first().finished_arts
                if picstatus == 'working':
                    pic.update(set__piclink=piclink)
                elif picstatus == 'finished':
                    pic.update(set__piclink=piclink, set__picstatus=picstatus)
                    User.objects(username=token).first().update(set__finished_arts=finished_arts+1)
                    User.objects(username=token).first().update(set__working_arts=working_arts-1)
                return redirect(url_for('saved', picid=picid))

@app.route("/saved/<picid>") # Hiển thị trang lưu ảnh thành công
def saved(picid):
    warning = 'Bạn chưa đăng nhập!'
    if 'token' not in session:
        return render_template('login.html', warning=warning)
    else:
        if session['token'] != Savepicture.objects(id=picid).first().picartist:
            return render_template('not_allow.html')
        else:
            pic = Savepicture.objects(id=picid).first()
            return render_template('saved.html', pic=pic)

@app.route("/profile/<artist>/change_infor", methods = ['GET', 'POST']) # Hiển thị trang thay đổi thông tin người dùng
def change_infor(artist):
    if 'token' not in session:
        return redirect(url_for('login'))
    else:
        if session['token'] != artist:
            return render_template('not_allow.html')
        else:
            artist_infor = User.objects(username=artist).first()
            pic_list = Savepicture.objects(picartist=artist)
            like_list = Like.objects(who_username=artist)
            comment_list = Comment.objects(who_username=artist)
            notice = ''
            if request.method == 'GET':
                return render_template('change_infor.html', fullname=artist_infor.fullname, password=artist_infor.password, notice=notice)
            elif request.method == 'POST':
                form = request.form
                new_fullname = form['fullname']
                new_username = form['username']
                new_password = form['password']
                if new_fullname.strip() != '':
                    artist_infor.update(set__fullname=new_fullname.strip())
                    for pic in pic_list:
                        pic.update(set__picartistfullname=new_fullname.strip())
                    for like in like_list:
                        like.update(set__who_fullname=new_fullname.strip())
                    for comment in comment_list:
                        comment.update(set__who_fullname=new_fullname.strip())
                if (new_username.strip() != '') and (' ' not in new_username):
                    artist = new_username
                    artist_infor.update(set__username=new_username.strip())
                    for pic in pic_list:
                        pic.update(set__picartist=new_username.strip())
                    for like in like_list:
                        like.update(set__who_username=new_username.strip())
                    for comment in comment_list:
                        comment.update(set__who_username=new_username.strip())
                if (new_password.strip() != '') and (' ' not in new_username):
                    artist_infor.update(set__password=new_password.strip())
                artist_infor = User.objects(username=artist).first()
                if new_fullname.strip() != '' or ((new_username.strip() != '') and (' ' not in new_username)) or ((new_password.strip() != '') and (' ' not in new_username)):
                    notice = 'Bạn đã thay đổi thông tin thành công!'
                return render_template('change_infor.html', fullname=artist_infor.fullname, password=artist_infor.password, notice=notice)

@app.route("/not_allow") # Hiển thị khi người dùng truy cập 1 trang không được phép
def not_allow():
    return render_template('not_allow.html')

@app.route("/search", methods = ['GET', 'POST']) # Trang tìm kiếm
def search():
    if request.method == 'GET':
        return render_template('search.html')
    elif request.method == 'POST':
        form = request.form
        searchword = form['searchword']
        field1 = form.get('field1') # form checkbox dùng form.get['inputname'] thay vì form['inputname']
        field2 = form.get('field2') # kết quả trả về là none hoặc value của checkbox. nếu đặt name các checkbox giống nhau thì trả về 1 list value (?)
        field3 = form.get('field3')
        raw_list = []
        finished_list = []
        artist_list = []
        warn1 = warn2 = warn3 = ''
        display = display1 = display2 = display3 = 'no'
        s_list = []
        if searchword != '':
            display = 'yes'
            s_list = searchword.replace('-', ' ').split()
            for s in s_list:
                r_list = Rawpicture.objects(Q(picname__icontains=s) | Q(category__icontains=s))
                for r in r_list:
                    if r not in raw_list:
                        raw_list.append(r)
                f_list = Savepicture.objects(picstatus='finished', picname__icontains=s)
                for f in f_list:
                    if f not in finished_list:
                        finished_list.append(f)
                a_list = User.objects(Q(username__icontains=s) | Q(fullname__icontains=s))
                for a in a_list:
                    if a not in artist_list:
                        artist_list.append(a)     
        if len(raw_list) == 0:
            warn1 = 'No raw picture found!'
        if len(finished_list) == 0:
            warn2 = 'No finished picture found!'
        if len(artist_list) == 0:
            warn3 = 'No artist found!'
        if field1 is not None:
            display1 = 'yes'
        if field2 is not None:
            display2 = 'yes'
        if field3 is not None:
            display3 = 'yes'
        if (field1 is None) and (field2 is None) and (field3 is None):
            display1 = display2 = display3 = 'yes'
        return render_template('search.html', searchword=searchword, raw_list=raw_list, finished_list=finished_list, artist_list=artist_list, warn1=warn1, warn2=warn2, warn3=warn3, display=display, display1=display1, display2=display2, display3=display3)

@app.route("/update") # Trang thông tin update thay đổi của trang web
def update():
    return render_template("update.html")

if __name__ == '__main__':
  app.run(debug=True)