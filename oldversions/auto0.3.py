#!/usr/bin/env python
""" 
Automatically Written version of Moodboard

Add offset
Add images per page

"""

import web
from web import form
import os
from datetime import datetime
import hashlib
import shutil

image_directory = "static/"

web.config.debug = False

urls = (
    '/', 'Index',
    '/newuser', 'NewUser',
    '/login', 'Login',
    '/Login', 'Login',
    '/logout', 'Logout',
    '/account', 'Account',
    '/deleteaccount', 'DeleteAccount',
    '/(.+)/(.+)', 'Sub_User_Index',
    '/(.+)', 'User_Index'
    
)


# Set Up Web.py App
app = web.application(urls, globals())

# Set Up Session handler
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'loggedin': False, 'username' : ''})

#template is called "Layout"
homepage_render = web.template.render('templates/', base="homelayout")
render = web.template.render('templates/', base="layout")
subrender = web.template.render('templates/', base="sublayout")
message_render = web.template.render('templates/', base="test")


""" DATABASING """
""" 
Users Table:
id integer primary key
username text
email text
passwordhash text
salt text
userfolder text
datejoined text

"""

db = web.database(dbn="sqlite", db="moodboard.db")



""" FUNCTIONS """

def make_new_user(username):
    """ Set up a new user account """
    user_path = os.path.join("static", username)
    user_images_path = os.path.join("static", username, "images")
    try: 
        os.makedirs(user_path)
    except OSError:
        if not os.path.isdir(user_path):
            raise

    try: 
        os.makedirs(user_images_path)
    except OSError:
        if not os.path.isdir(user_path):
            raise

def get_logtime():
    """ Return the date and time """
    return datetime.now().strftime('%Y/%m/%d %H:%M')

def make_image_list(cur_foldername, page):
    """ Create list of images from cur_foldername """
    cur_image_list = [f for f in os.listdir(cur_foldername) if os.path.isfile(os.path.join(cur_foldername, f)) and f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webm'))]
    # Sort newFileList by date added(?)
    cur_image_list.sort(key=lambda x: os.stat(os.path.join(cur_foldername, x)).st_mtime)
    cur_image_list.reverse() # reverse image list so new files are first

    new_list = []

    imagesperpage = 20 # how many images on each page?

    offset = (page - 1) * imagesperpage # offset for pagination

    # Find the current image range
    imagerange = "%d - %d" % (offset + 1, offset + imagesperpage)

    #Find the number of images in the list
    numberofimages = len(cur_image_list)

    #Find the total number of pages at current ipp
    numberofpages = numberofimages / imagesperpage

    count = 0
    # For each image in the list in the range, add to new list
    for image in cur_image_list:
        if count < (0 + offset):
            count += 1
        elif count >= offset and count < (offset + imagesperpage):
            newf = os.path.join(cur_foldername, image)
            new_list.append(newf)
            count += 1
        else:
            break
            

    return new_list, imagerange, numberofimages, numberofpages


""" PASSWORD STUFF """
def hash_password(input_password):
    """ Returns the sha256 hash of an input and the salt """
    salt = os.urandom(16).encode('base_64') #make some salt

    salted_password = input_password + salt

    sha = hashlib.sha256() # get a clean object
    sha.update(salted_password) # update function with new password
    hash_out = sha.hexdigest() # return hex of hash
    return hash_out, salt

def check_password(input_password, input_salt):
    salted_password = input_password + input_salt

    sha = hashlib.sha256() # get a clean object
    sha.update(salted_password) # update function with new password
    hash_out = sha.hexdigest() # return hex of hash
    return hash_out


""" WEB PAGES """
# Home Page
class Index(object):
    def GET(self):
        folderlist = [f for f in os.listdir(image_directory) if os.path.isdir(os.path.join(image_directory, f)) == True and f not in ("thumbs")]

        new_users_list = []

        for folder in folderlist:
            images_path = os.path.join("static", folder, "images")
            cur_image_list = [f for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f)) and f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webm'))]
            # Sort newFileList by date added(?)
            cur_image_list.sort(key=lambda x: os.stat(os.path.join(images_path, x)).st_mtime)
            cur_image_list.reverse() # reverse image list so new files are first
            if cur_image_list != []:
                new_users_list.append((folder, os.path.join(images_path, cur_image_list[0])))
            else:
                pass

        if session._initializer['loggedin'] == True:
            return homepage_render.home(new_users_list, "Home: %s" % session._initializer['username'], session._initializer['loggedin'], "")
        else:
            return homepage_render.home(new_users_list, "Home", session._initializer['loggedin'], "")

        # return homepage_render.home(new_users_list, str(session.get('username')))



#User's Directory Index
class User_Index(object):
    def GET(self, user):
        form = web.input(page="1")
        folderlist = [f for f in os.listdir(os.path.join(image_directory, user, "images")) if os.path.isdir(os.path.join(image_directory, user, "images",    f)) == True and f not in ("thumbs")]


        imagelist, imagerange, numberofimages, numberofpages = make_image_list(os.path.join("static", user, "images" ), int(form.page))
        
        page = int(form.page)

        if page > 1:
            prevpage = page - 1
        else:
            prevpage = 0

        if (page - 1) < numberofpages:
            nextpage = page + 1
        else:
            nextpage = 0

        return render.usercontent(imagelist, imagerange, numberofimages, prevpage, nextpage, folderlist, user)


# User's Subdirectory Index
class Sub_User_Index(object):
    def GET(self, user, directory):
        form = web.input(page="1")
        folderlist = [f for f in os.listdir(os.path.join(image_directory, user, "images")) if os.path.isdir(os.path.join(image_directory, user, "images", f)) == True and f not in ("thumbs")]


        imagelist, imagerange, numberofimages, numberofpages = make_image_list(os.path.join("static", user, "images" , directory), int(form.page))
        
        page = int(form.page)

        if page > 1:
            prevpage = page - 1
        else:
            prevpage = 0

        if (page - 1) < numberofpages:
            nextpage = page + 1
        else:
            nextpage = 0

        return subrender.subusercontent(imagelist, imagerange, numberofimages, prevpage, nextpage, folderlist, user)


class Login(object):
    def GET(self):
        return homepage_render.login('Hello', session._initializer['loggedin'])

    def POST(self):
        username, password = web.input().username, web.input().password

        #retreive user's salt
        try:
            salt = db.select('users', where="username=$username", vars=locals())[0]["salt"]
        except:
            return homepage_render.login('Login Error', session._initializer['loggedin'])

        password = check_password(password, salt)

        #hash password with salt
        check = db.select('users', where="username=$username AND passwordhash=$password", vars=locals())

        if check:
            session._initializer['loggedin'] = True
            session._initializer['username'] = username
            raise web.seeother('/')
        else:
            return homepage_render.newuser('Failed')

class Logout(object):
    def GET(self):
        session._initializer['loggedin'] = False
        session.kill()
        raise web.seeother('/')

#email validator
vemail = form.regexp(r".*@.*", "must be a valid email address")

# New user form
new_user_form = form.Form(
    form.Textbox('username', description="Username"),
    form.Textbox('email', vemail, description="E-Mail"),
    form.Password('password', description="Password"),
    form.Password('password_again', description="Confirm Password"),
    validators=[form.Validator("Passwords didn't match.", lambda i: i.password == i.password_again)]
)

# Create a new user page
class NewUser(object):
    def GET(self):
        cur_form = new_user_form()
        return homepage_render.newuser("New User", cur_form, session._initializer['loggedin'])

    def POST(self):
        cur_form = new_user_form()
        if cur_form.validates():

            username = cur_form['username'].value
            password = cur_form['password'].value
            email = cur_form['email'].value

            if username not in db.select('users', what='username'):

                # Make user folders
                make_new_user(username)

                new_user_folder = os.path.join("static", username)

                # Hash Password
                passwordhash, passwordsalt = hash_password(password)

                makeuser = db.insert('users', username=username, emailaddress=email, passwordhash=passwordhash, salt=passwordsalt, userfolder=new_user_folder, datejoined=get_logtime())

                web.sendmail('Moodboard', email, 'Welcome!', 'Welcome to Moodboard, %s' % username)
                return homepage_render.welcome(username, password, passwordhash, passwordsalt, session._initializer['loggedin'])
            else:
                # Error username taken
                return message_render.message('Username Taken')
        else:
            return homepage_render.newuser("New User", cur_form, session._initializer['loggedin'])

class Account(object):
    def GET(self):
        return homepage_render.account("Account", session._initializer['loggedin'], "")

delete_account_form = form.Form(form.Checkbox('confirm', description="Confirm Account Deletion", value="confirmed"), form.Button('submit', type="submit", description="Submit"))


class DeleteAccount(object):
    def GET(self):
        cur_form = delete_account_form()
        return homepage_render.deleteaccount("Delete Account", session._initializer['loggedin'], cur_form, "")

    def POST(self):
        cur_form = delete_account_form()

        # THIS IS STUPIDLY HACKY AND UNDOCUMENTED ON THE WEBPY WEBSITE
        formdata = web.input()
        
        if formdata.has_key('confirm'):

            username = session._initializer['username']

            # Delete user from database
            db.delete('users', where="username=$username", vars=locals())

            # Delete user's directory
            shutil.rmtree(os.path.join('static', username))


            return  message_render.message("Account Deleted")
        else:
            return  message_render.message("Account not Deleted")


class UploadImage(object):
    def GET(self):
        homepage_render.uploadimage("Upload Image", session._initializer['loggedin'], cur_form, "")

    def POST(self):

        username = session._initializer['username']
        filedir = os.path.join('static', username, 'images' )


if __name__ == "__main__":
    app.run()
