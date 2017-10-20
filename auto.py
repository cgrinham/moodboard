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
from PIL import Image
import random
import string
try:
    import cPickle as pickle
except:
    import pickle

USERSFOLDER = "static/users/"

web.config.debug = False

urls = (
    '/', 'Index',
    '/newuser', 'NewUser',
    '/login', 'Login',
    '/Login', 'Login',
    '/logout', 'Logout',
    '/account', 'Account',
    '/deleteaccount', 'DeleteAccount',
    '/thumbnails', 'GenerateThumbnails',
    '/verify', 'VerifyEmail',
    '/favourites', 'Favourites',
    '/favourites/all', 'AllFavourites',
    '/resendverification', 'ResendVerify',
    '/internet', 'Internet',
    '/(.+)/(.+)', 'Sub_User_Index',
    '/(.+)', 'User_Index'
)


# Set Up Web.py App
app = web.application(urls, globals())

# Set Up Session handler
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'loggedin': False, 'username' : '', 'favourites' : []})

#template is called "Layout"
homepage_render = web.template.render('templates/', base="homelayout")
render = web.template.render('templates/', base="userindex")
subrender = web.template.render('templates/', base="usersub")
internet = web.template.render('templates/', base="internet")


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
    user_path = os.path.join(USERSFOLDER, username)
    user_images_path = os.path.join(USERSFOLDER, username, "images")
    try: 
        os.makedirs(user_path)
        os.chown(user_path, 1000, 1000)
    except OSError:
        if not os.path.isdir(user_path):
            raise

    try: 
        os.makedirs(user_images_path)
        os.chown(user_images_path, 1000, 1000)
    except OSError:
        if not os.path.isdir(user_images_path):
            raise

def get_logtime():
    """ Return the date and time """
    return datetime.now().strftime('%Y/%m/%d %H:%M')

def make_thumbnail(cur_process, folder, thumbdir, image):
    """ Make thumnail for given image """
    #print "%s - %s: Make thumbnail %s in thumbdir %s" % (get_logtime(), cur_process, image, thumbdir)
    if not os.path.exists(os.path.join(thumbdir, image)): #if thumbnail doesn't exist
        imagepath = os.path.join(folder, image)
        print "%s - %s: PIL - File to open is: %s"  % (get_logtime(), cur_process, imagepath)
        try:
            
            img = Image.open(imagepath).convert('RGB') # open and convert to RGB

            hpercent = (float(HEIGHT) / float(img.size[1])) # find ratio of new height to old height
            wsize = int(float(img.size[0]) * hpercent) # apply ratio to create new width
            img = img.resize((int(wsize), int(HEIGHT)), Image.ANTIALIAS) # resize image with antialiasing
            img.save(os.path.join(thumbdir, image), format='JPEG', quality=90) # save with quality of 80, optimise setting caused crash
            print "%s - %s: Sucessfully resized: %s \n" % (get_logtime(), cur_process, image)
        except IOError:
            print "%s - %s: IO Error. %s will be deleted and downloaded properly next sync" % (get_logtime(), cur_process, imagepath)
            os.remove(imagepath)
    else:
        #print "%s - %s: Thumbnail for %s exists \n" % (get_logtime(), cur_process, image)
        pass

def list_files(cur_foldername, reverse):
    """ Return list of files of specified type """
    output = [f for f in os.listdir(cur_foldername) if os.path.isfile(os.path.join(cur_foldername, f)) and f.endswith(('.jpg', '.jpeg', '.png'))]

    if reverse == True:
        # Sort newFileList by date added(?)
        output.sort(key=lambda x: os.stat(os.path.join(cur_foldername, x)).st_mtime)
        output.reverse() # reverse image list so new files are first
    else:
        pass

    return output

def list_folders(cur_folder):
    """ Return list of folders in given folder """
    return [f for f in os.listdir(cur_folder) if os.path.isdir(os.path.join(cur_folder, f)) == True and f not in ("thumbs", "css", "js", "img")]

def get_images(username):
    images = db.select('images', where='owner=$username', vars=locals())
    print images

def make_image_list(cur_foldername, page):
    """ Create list of images from cur_foldername """
    cur_image_list = list_files(cur_foldername, True)

    if session.loggedin == True:
        username = session.username
        imagesperpage = int(db.select('users', where="username=$username", vars=locals())[0]["imagesperpage"])
    else:
        imagesperpage = 20 # how many images on each page?

    offset = (page - 1) * imagesperpage # offset for pagination

    # Find the current image range
    imagerange = "%d - %d" % (offset + 1, offset + imagesperpage)

    #Find the number of images in the list
    numberofimages = len(cur_image_list)

    #Find the total number of pages at current ipp
    numberofpages = numberofimages / imagesperpage

    count = 0

    new_list = [] # image list
    # For each image in the list in the range, add to new list
    for image in cur_image_list:
        if count < (0 + offset):
            count += 1
        elif count >= offset and count < (offset + imagesperpage):
            new_list.append(image)
            count += 1
        else:
            break
            

    return new_list, imagerange, numberofimages, numberofpages

def imagesbycolour(user, colour):
    """ Return images of a certain colour from acertain user """
    # Find the user id for the given user
    user_id = db.select('users', where='username=$user', vars=locals())[0]["id"]
    # Return images by colour from the given user

    if colour == "bw":
        results = db.select('images', where='owner=$user_id AND bw="1"', vars=locals())
    else:
        results = db.select('images', where="owner=$user_id AND hue1=$colour OR owner=$user_id AND hue2=$colour OR owner=$user_id AND hue3=$colour", vars=locals())
    #results = db.select('images', where="id=$user_id", vars=locals())

    """for result in results:
        if colour == "black" or "white":
        if colour in (result["hue1"], result["hue2"], result["hue3"])
        print """

    return results

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
    """ sha the input password and salt """
    salted_password = input_password + input_salt

    sha = hashlib.sha256() # get a clean object
    sha.update(salted_password) # update function with new password
    hash_out = sha.hexdigest() # return hex of hash
    return hash_out


""" WEB PAGES """

# Internet Connection Analytics Page
class Internet(object):
    def GET(self):
        return internet.internetcontent()


# Home Page
class Index(object):
    def GET(self):
        # Get folders in users folders
        folderlist = list_folders(USERSFOLDER)

        new_users_list = []

        for folder in folderlist:
            images_path = os.path.join(USERSFOLDER, folder, "images")
            cur_image_list = list_files(images_path, True)

            if cur_image_list != []:
                new_users_list.append((folder, os.path.join(images_path, cur_image_list[0]), len(cur_image_list)))
            else:
                pass

        if session.loggedin == True:
            return homepage_render.home(new_users_list, "Home: %s" % session.username, session, "")
        else:
            return homepage_render.home(new_users_list, "Home", session, "")

#User's Directory Index
class User_Index(object):
    def GET(self, user):

        try:
            try:
                if web.input().colour:
                    form = web.input(page="1")
                    results = imagesbycolour(user, web.input().colour)

                    colourlist = []

                    for result in results:
                        print result
                        colourlist.append(result["filename"])

                    folderlist = list_folders(os.path.join(USERSFOLDER, user, "images"))

                    nonemptyfolderlist = []

                    for folder in folderlist:
                        subfolderlist = list_files(os.path.join(USERSFOLDER, user, "images", folder), False)
                        if subfolderlist:
                            nonemptyfolderlist.append(folder)
                        else:
                            pass

                    folderlist = (nonemptyfolderlist, folderlist)

                    imagelist, imagerange, numberofimages, numberofpages = make_image_list(os.path.join(USERSFOLDER, user, "images" ), int(form.page))
                
                    numberofimages = len(colourlist)

                    page = int(form.page)

                    if page > 1:
                        prevpage = page - 1
                    else:
                        prevpage = 0

                    if (page - 1) < numberofpages:
                        nextpage = page + 1
                    else:
                        nextpage = 0

                    return render.usercontent(colourlist, imagerange, numberofimages, prevpage, nextpage, folderlist, user, session)

            except AttributeError:
                form = web.input(page="1")
                folderlist = list_folders(os.path.join(USERSFOLDER, user, "images"))

                nonemptyfolderlist = []

                for folder in folderlist:
                    subfolderlist = list_files(os.path.join(USERSFOLDER, user, "images", folder), False)
                    if subfolderlist:
                        nonemptyfolderlist.append(folder)
                    else:
                        pass

                folderlist = (nonemptyfolderlist, folderlist)

                imagelist, imagerange, numberofimages, numberofpages = make_image_list(os.path.join(USERSFOLDER, user, "images" ), int(form.page))
                
                page = int(form.page)

                if page > 1:
                    prevpage = page - 1
                else:
                    prevpage = 0

                if (page - 1) < numberofpages:
                    nextpage = page + 1
                else:
                    nextpage = 0

                return render.usercontent(imagelist, imagerange, numberofimages, prevpage, nextpage, folderlist, user, session)
        except OSError:
            return homepage_render.message("404 Not Found", session, "Sorry, there doesn't seem to be a %s among us" % user)

    def POST(self, user):

        print "Action"

        action = web.input().action
        print action
        prop1 = web.input().prop1
        print prop1
        prop2 = web.input().prop2
        print prop2

        username = session.username

        if action == "rotate":
            image = prop1
            direction = prop2

            HEIGHT = 350

            imagefolder, imagefile = os.path.split(image)

            img = Image.open(image).convert('RGB')
            if direction == "rotate_ccw":
                print "Rotate %s 90 degrees" % image
                img = img.rotate(90)
                img.save(image)

            elif direction == "rotate_cw":
                print "Rotate %s 270 degrees" % image
                img = img.rotate(270)
                img.save(image)

            else:
                print "Error"

            # Recreate thumbnail
            hpercent = (float(HEIGHT) / float(img.size[1]))  # find ratio of new height to old height
            wsize = int(float(img.size[0]) * hpercent)  # apply ratio to create new width
            img = img.resize((int(wsize), int(HEIGHT)), Image.ANTIALIAS)  # resize image with antialiasing
            img.save(os.path.join(imagefolder, "thumbs", imagefile), format='JPEG', quality=85)
            # add to thumbnail queue!

            return True
        elif action == "favourite":
            user = prop1

            # Get user's id
            user_id = db.select('users', where='username=$user', vars=locals())[0]["id"]

            # Get favourites list
            favouriteslist = pickle.loads(str(db.select('users', where="username=$username", vars=locals())[0]["favourites"]))

            # Add user id to favourites list
            favouriteslist.append(user_id)

            # Update the session
            session.favourites = favouriteslist

            # Update database with pickled favourites list
            db.update('users', where="username=$username", favourites=pickle.dumps(favouriteslist), vars=locals())

            print "Favourite %s" % user_id

        elif action == "move":
            # Trim leading ../
            abs_thumb_path = prop1[3:]
            new_folder = prop2

            # static/user/images/thumbs - filename
            thumbs_folder, filename = os.path.split(abs_thumb_path)
            # static/user/images - "thumbs"
            root_folder, thumbs = os.path.split(thumbs_folder)

            # Get the absolute path of the full res image
            abs_path = os.path.join(root_folder, filename)

            if new_folder not in "root":
                new_path = os.path.join(root_folder, new_folder, filename)
                new_thumb_path = os.path.join(root_folder, new_folder, "thumbs", filename)
                new_containing_folder = os.path.join(root_folder, new_folder)
            else:
                new_path = os.path.join(root_folder, filename)
                new_thumb_path = os.path.join(root_folder, "thumbs", filename)
                new_containing_folder = root_folder

            # Move image
            shutil.move(abs_path, new_path)
            # move the thumbnail
            shutil.move(abs_thumb_path, new_thumb_path)

            # Update paths in database
            db.update('images', where="filename=$filename", absolutepath=new_path, path=new_containing_folder, vars=locals())

            return True

        elif action == "delete":
            abs_path = prop1
            print "Delete %s" % abs_path

            # static/user/images/ - filename
            image_folder, filename = os.path.split(abs_path)

            # Get the thumbnail path
            abs_thumb_path = os.path.join(image_folder, "thumbs", filename)

            db.delete('images', where="absolutepath=$abs_path", vars=locals())

            # Delete full res image
            os.remove(abs_path)
            # Delete thumbnail
            os.remove(abs_thumb_path)

            return True
        else:
            print "Unrecognised action"


# User's Subdirectory Index
class Sub_User_Index(object):
    def GET(self, user, directory):
        form = web.input(page="1")
        folderlist = list_folders(os.path.join(USERSFOLDER, user, "images"))

        nonemptyfolderlist = []

        for folder in folderlist:
            subfolderlist = list_files(os.path.join(USERSFOLDER, user, "images", folder), False)
            if subfolderlist:
                nonemptyfolderlist.append(folder)
            else:
                pass

        folderlist = (nonemptyfolderlist, folderlist)

        imagelist, imagerange, numberofimages, numberofpages = make_image_list(os.path.join(USERSFOLDER, user, "images" , directory), int(form.page))

        page = int(form.page)

        if page > 1:
            prevpage = page - 1
        else:
            prevpage = 0

        if (page - 1) < numberofpages:
            nextpage = page + 1
        else:
            nextpage = 0

        return subrender.subusercontent(imagelist, imagerange, numberofimages, prevpage, nextpage, folderlist, user, directory, session)

    def POST(self, user, directory):

        action, prop1, prop2 = web.input().action, web.input().prop1, web.input().prop2

        username = session.username

        if action == "rotate":
            image = prop1
            direction = prop2

            HEIGHT = 350

            imagefolder, imagefile = os.path.split(image)

            img = Image.open(image).convert('RGB')
            if direction == "rotate_ccw":
                print "Rotate %s 90 degrees" % image
                img = img.rotate(90)
                img.save(image)

                # Recreate thumbnail
                hpercent = (float(HEIGHT) / float(img.size[1])) # find ratio of new height to old height
                wsize = int(float(img.size[0]) * hpercent) # apply ratio to create new width
                img = img.resize((int(wsize), int(HEIGHT)), Image.ANTIALIAS) # resize image with antialiasing
                img.save(os.path.join(imagefolder, "thumbs", imagefile), format='JPEG', quality=85)
                # add to thumbnail queue!

            elif direction == "rotate_cw":
                print "Rotate %s 270 degrees" % image
                img = img.rotate(270)
                img.save(image)

                # Recreate thumbnail
                hpercent = (float(HEIGHT) / float(img.size[1])) # find ratio of new height to old height
                wsize = int(float(img.size[0]) * hpercent) # apply ratio to create new width
                img = img.resize((int(wsize), int(HEIGHT)), Image.ANTIALIAS) # resize image with antialiasing
                img.save(os.path.join(imagefolder, "thumbs", imagefile), format='JPEG', quality=85)
                # add to thumbnail queue!

            else:
                print "Error"

        elif action == "favourite":
            user = prop1

            # Get user's id
            user_id = db.select('users', where='username=$user', vars=locals())[0]["id"]

            # Get favourites list
            favouriteslist = pickle.loads(str(db.select('users', where="username=$username", vars=locals())[0]["favourites"]))

            # Add user id to favourites list
            favouriteslist.append(user_id)

            # Update the session
            session.favourites = favouriteslist

            # Update database with pickled favourites list
            db.update('users', where="username=$username", favourites=pickle.dumps(favouriteslist), vars=locals())

            print "Favourite %s" % user_id

        elif action == "move":
            # Trim leading ../
            abs_thumb_path = prop1[3:]
            new_folder = prop2

            # static/user/images/folder/thumbs - filename
            thumbs_folder, filename = os.path.split(abs_thumb_path)
            print "Thumbs Folder: " + thumbs_folder
            # static/user/images/folder - "thumbs"
            sub_folder, thumbs = os.path.split(thumbs_folder)
            print "Sub folder: " + sub_folder
            # static/user/images - folder
            root_folder, sub_folder = os.path.split(sub_folder)
            print "Root Folder: " + root_folder

            # Get the absolute path of the full res image
            abs_path = os.path.join(root_folder, sub_folder, filename)

            if new_folder not in "root":
                new_path = os.path.join(root_folder, new_folder, filename)
                new_thumb_path = os.path.join(root_folder, new_folder, "thumbs", filename)
                new_containing_folder = os.path.join(root_folder, new_folder)
            else:
                new_path = os.path.join(root_folder, filename)
                new_thumb_path = os.path.join(root_folder, "thumbs", filename)
                new_containing_folder = root_folder

            # Move image
            shutil.move(abs_path, new_path)
            # move the thumbnail
            shutil.move(abs_thumb_path, new_thumb_path)

            # Update paths in database
            db.update('images', where="filename=$filename", absolutepath=new_path, path=new_containing_folder, vars=locals())

            return True

        elif action == "delete":
            abs_path = prop1
            print "Delete %s" % abs_path

            # static/user/images/ - filename
            image_folder, filename = os.path.split(abs_path)

            # Get the thumbnail path
            abs_thumb_path = os.path.join(image_folder, "thumbs", filename)

            db.delete('images', where="absolutepath=$abs_path", vars=locals())

            # Delete full res image
            os.remove(abs_path)
            # Delete thumbnail
            os.remove(abs_thumb_path)

            return True

        else:
            print "Unrecognised action"


class AllFavourites(object):
    def GET(self):
        username = session.username
        favourites = session.favourites

        message = ""

        for id in favourites:
            rows = db.select('images', where="owner=$id", vars=locals())

            # NEED TO ADD DATETIME ADDED TO DATABASE, then sort by datetime

            for row in rows:
                message += row["absolutepath"] + "\n"

        return homepage_render.message("All Favourites", session, message)


class Favourites(object):
    def GET(self):
        username = session.username

        favourites = pickle.loads(str(db.select('users', where="username=$username", vars=locals())[0]["favourites"]))

        userlist = []

        for favourite in favourites:
            username = db.select('users', where="id=$favourite", vars=locals())[0]["username"]

            userlist.append(username)

        new_users_list = []

        for favourite in userlist:
            images_path = os.path.join(USERSFOLDER, favourite, "images")
            cur_image_list = list_files(images_path, True)

            if cur_image_list != []:
                new_users_list.append((favourite, os.path.join(images_path, cur_image_list[0])))
            else:
                pass

        # return homepage_render.message(userlist, session, "")
        return homepage_render.favourites(new_users_list, "%s's Favourites" % session.username, session, "")

    def POST(self):

        action, prop1, prop2 = web.input().action, web.input().prop1, web.input().prop2

        username = session.username

        if action == "unfavourite":
            user = prop1

            # Find the user id of the favourite
            user_id = db.select('users', where='username=$user', vars=locals())[0]["id"]

            # load favourites list from database and unpickle
            favouriteslist = pickle.loads(str(db.select('users', where="username=$username", vars=locals())[0]["favourites"]))

            # Remove user id from favourite
            favouriteslist.remove(user_id)

            # Update the session
            session.favourites = favouriteslist

            # Pickle favourites list
            pickledlist = pickle.dumps(favouriteslist)

            # Update database with new favourites list
            db.update('users', where="username=$username", favourites=pickledlist, vars=locals())

        else:
            print "Unrecognised action"


class Login(object):
    def GET(self):
        return homepage_render.login('Hello', session.loggedin)

    def POST(self):
        username, password = web.input().username, web.input().password

        # retreive user's salt
        try:
            salt = db.select('users', where="username=$username", vars=locals())[0]["salt"]
        except:
            return homepage_render.login('Login Error', session.loggedin)

        password = check_password(password, salt)

        # hash password with salt
        check = db.select('users', where="username=$username AND passwordhash=$password", vars=locals())

        if check:
            favouriteslist = pickle.loads(str(db.select('users', where="username=$username", vars=locals())[0]["favourites"]))
            favouritesusernamelist = []

            for favourite in favouriteslist:
                favourite = db.select('users', where='id=$favourite', vars=locals())[0]["username"]
                favouritesusernamelist.append(favourite)

            print favouritesusernamelist
            session.favourites = favouritesusernamelist
            session.loggedin = True
            session.username = username
            raise web.seeother('/')
        else:
            return homepage_render.login('Login Failed', session.loggedin)


class Logout(object):
    def GET(self):
        session.loggedin = False
        session.kill()
        raise web.seeother('/')

# email validator
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
        return homepage_render.newuser("New User", cur_form, session.loggedin)

    def POST(self):
        cur_form = new_user_form()
        if cur_form.validates():

            username = cur_form['username'].value
            password = cur_form['password'].value
            email = cur_form['email'].value

            try: # If there are no entries in teh database, the select fails
                if username not in db.select('users', what='username')[0]["username"]:
                    print "There are entries in the database"
                    # Make user folders
                    make_new_user(username)

                    new_user_folder = os.path.join(USERSFOLDER, username)

                    # Hash Password
                    passwordhash, passwordsalt = hash_password(password)

                    emailhash = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24))

                    # Make an empty favouriteslist
                    pickledlist = pickle.dumps([])

                    makeuser = db.insert('users', username=username, emailaddress=email, passwordhash=passwordhash, salt=passwordsalt, userfolder=new_user_folder, datejoined=get_logtime(), imagesperpage="20", privilege="0", email_verified="0", emailhash=emailhash, favourites=pickledlist)

                    web.sendmail('Moodboard', email, 'Welcome!', 'Welcome to Moodboard, %s \n Please use the following address to verify your account: http://127.0.0.1:8080/verify?email=%s&hash=%s' % (username, email, emailhash))
                    # Verification link: "http://christophski.ddns.net/verify?email=%s&hash=%s" % (email, hash)

                    return homepage_render.welcome(username, session.loggedin)
                else:
                    # Error username taken
                    return homepage_render.message('Username Taken', session, "")
            except IndexError:
                print "There are no entries in the database"
                # Make user folders
                make_new_user(username)

                new_user_folder = os.path.join(USERSFOLDER, username)

                # Hash Password
                passwordhash, passwordsalt = hash_password(password)

                emailhash = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24))

                makeuser = db.insert('users', username=username, emailaddress=email, passwordhash=passwordhash, salt=passwordsalt, userfolder=new_user_folder, datejoined=get_logtime(), imagesperpage="20", privilege="0", email_verified="0", emailhash=emailhash)

                web.sendmail('Moodboard', email, 'Welcome!', 'Welcome to Moodboard, %s \n Please use the following address to verify your account: http://127.0.0.1:8080/verify?email=%s&hash=%s' % (username, email, emailhash))
                # Verification link: "http://christophski.ddns.net/verify?email=%s&hash=%s" % (email, hash)

                return homepage_render.welcome(username, session.loggedin)
        else:
            return homepage_render.newuser("New User", cur_form, session.loggedin)


class ResendVerify(object):
    def GET(self):
        username = session.username

        email = db.select('users', where='username=$username', vars=locals())[0]["emailaddress"]

        emailhash = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24))

        db.update('users', where="username=$username", emailhash=emailhash, vars=locals())

        web.sendmail('Moodboard', email, 'Verify Your Account', 'Hi %s, here is your new verification link: http://127.0.0.1:8080/verify?email=%s&hash=%s' % (username, email, emailhash))

        return homepage_render.message("Verification Email Sent", session, "")


class VerifyEmail(object):
    def GET(self):
        form = web.input(email="", hash="")

        email = form.email

        # If email is in database, compare hash. If match, verify account, else fail.
        if email in db.select('users', what='emailaddress')[0]["emailaddress"]:
            print "Email was in database"
            stored_hash = db.select('users', where='emailaddress=$email', vars=locals())[0]["emailhash"]
            print "Stored hash is %s" % stored_hash
            if form.hash == stored_hash:
                db.update('users', where="emailaddress=$email", email_verified="1", vars=locals())
                print "Updated database"

                return homepage_render.verify(session.loggedin, form.email)
            else:
                print "Email address could not be verified."
        else:
            print db.select('users', what='emailaddress')[0]["emailaddress"]
            print "Email address %s not in database." % form.email


class Account(object):
    def GET(self):

        username = session.username

        datejoined = db.select('users', where="username=$username", vars=locals())[0]["datejoined"]
        imagesperpage = db.select('users', where="username=$username", vars=locals())[0]["imagesperpage"]

        verified = db.select('users', where="username=$username", vars=locals())[0]["email_verified"]

        return homepage_render.account("Account", session.loggedin, username, datejoined, imagesperpage, verified, "")

    def POST(self):

        username = session.username

        newimagesperpage = web.input().ippselect

        db.update('users', where="username=$username", imagesperpage=newimagesperpage, vars=locals())

        datejoined = db.select('users', where="username=$username", vars=locals())[0]["datejoined"]
        imagesperpage = db.select('users', where="username=$username", vars=locals())[0]["imagesperpage"]

        verified = db.select('users', where="username=$username", vars=locals())[0]["email_verified"]

        return homepage_render.account("Account Updated", session.loggedin, username, datejoined, imagesperpage, verified, "")


delete_account_form = form.Form(form.Checkbox('confirm', description="Confirm Account Deletion", value="confirmed"), form.Button('submit', type="submit", description="Submit"))


class DeleteAccount(object):
    def GET(self):
        cur_form = delete_account_form()
        return homepage_render.deleteaccount("Delete Account", session.loggedin, cur_form, "")

    def POST(self):
        cur_form = delete_account_form()

        # THIS IS STUPIDLY HACKY AND UNDOCUMENTED ON THE WEBPY WEBSITE
        formdata = web.input()

        if formdata.has_key('confirm'):

            username = session.username

            # Delete user from database
            db.delete('users', where="username=$username", vars=locals())

            # Delete user's directory
            shutil.rmtree(os.path.join(USERSFOLDER, username))

            # Log user out
            session.loggedin = False
            session.kill()

            return  homepage_render.message("Account Deleted", session, "")
        else:
            return  homepage_render.message("Account not Deleted", session, "")


class GenerateThumbnails(object):
    def GET(self):

        username = session.username
        HEIGHT = 350

        pil_log = ""

        # Create thumbnails for user's root folder
        imagefolder = os.path.join(USERSFOLDER, username, "images")

        cur_image_list = list_files(imagefolder, False)

        thumbdir = os.path.join(imagefolder, "thumbs")

        # This should probably move to somewhere else so it doesn't occur in gif and webm folders
        if not os.path.isdir(thumbdir): # check if thumbdir exists
            os.mkdir(thumbdir) # make thumbdir
            print "Thumbnail directory created at " + thumbdir
        else:
            print "Thumbnail directory exists"

        for image in cur_image_list:
            make_thumbnail("Forced By User", imagefolder, thumbdir, image)

        # Create thumbnails for user's sub folders
        folderlist = list_folders(imagefolder)

        for folder in folderlist:

            cur_folder = os.path.join(imagefolder, folder)

            cur_image_list = list_files(cur_folder, False)

            print "List for %s is %s" % (folder, cur_image_list)

            thumbdir = os.path.join(cur_folder, "thumbs")

            if not os.path.isdir(thumbdir):  # check if thumbdir exists
                os.mkdir(thumbdir)  # make thumbdir
                print "Thumbnail directory created at " + thumbdir
            else:
                print "Thumbnail directory exists"

            for image in cur_image_list:

                make_thumbnail("Forced by User", cur_folder, thumbdir, image)

        return homepage_render.message(pil_log, session, "")

        if sesson.loggedin is True:
            return homepage_render.thumbnails("Generate Thumbnails", session, "")
        else:
            return homepage_render.message("You Must Be Logged In To Generate Thumbnails", session, "")


class UploadImage(object):
    def GET(self):
        homepage_render.uploadimage("Upload Image", session.loggedin, cur_form, "")

    def POST(self):

        username = session.username
        filedir = os.path.join(USERSFOLDER, username, 'images')


if __name__ == "__main__":
    app.run()
