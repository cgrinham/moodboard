""" 
Automatically Written version of Moodboard

Add offset
Add images per page

"""

import web
import os
from datetime import datetime
import hashlib

image_directory = "static/"


urls = (
    '/', 'Index',
    '/newuser', 'NewUser',
    '/(.+)/(.+)', 'Sub_User_Index',
    '/(.+)', 'User_Index'
    
)

# Get list of subfolders
#folderlist = [f for f in os.listdir(image_directory) if os.path.isdir(os.path.join(image_directory, f)) == True and f not in ("thumbs")]

# Add URL for each subfolder
#for folder in folderlist:
#    urls += (os.path.join("/", folder.lower()), 'Index')


app = web.application(urls, globals())
#template is called "Layout"
homepage_render = web.template.render('templates/', base="homelayout")
render = web.template.render('templates/', base="layout")
subrender = web.template.render('templates/', base="sublayout")


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

def hash_password(input_password):
    """ Returns the sha256 hash of an input and the salt """
    salt = os.urandom(16).encode('base_64') #make some salt

    salted_password = input_password + salt

    sha = hashlib.sha256() # get a clean object
    sha.update(salted_password) # update function with new password
    hash_out = sha.hexdigest() # return hex of hash
    return hash_out, salt


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


        return homepage_render.home(new_users_list, "Home")

# Create a new user page
class NewUser(object):
    def GET(self):
        return homepage_render.newuser("New User")

    def POST(self):
        form = web.input(username="", email="", password="")
        make_new_user(form.username)

        new_user_folder = os.path.join("static", form.username)

        # Hash Password
        passwordhash, passwordsalt = hash_password(form.password)

        makeuser = db.insert('users', username=form.username, emailaddress=form.email, passwordhash=passwordhash, salt=passwordsalt, userfolder=new_user_folder, datejoined=get_logtime())

        web.sendmail('Moodboard', form.email, 'Welcome!', 'Welcome to Moodboard, %s' % form.username)
        return homepage_render.welcome(form.username, form.password, passwordhash, passwordsalt)

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


# USER'S FUNCTIONS

class Settings(object):
    def POST(self):
        pass

if __name__ == "__main__":
    app.run()
