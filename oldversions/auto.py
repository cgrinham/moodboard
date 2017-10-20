""" 
Automatically Written version of Moodboard

Add offset
Add images per page

"""

import web
import os
from datetime import datetime

image_directory = "static/images"



urls = (
    '/(.+)', 'Sub_Index',
    '/', 'Index'
)

# Get list of subfolders
folderlist = [f for f in os.listdir(image_directory) if os.path.isdir(os.path.join(image_directory, f)) == True and f not in ("thumbs")]

# Add URL for each subfolder
#for folder in folderlist:
#    urls += (os.path.join("/", folder.lower()), 'Index')


app = web.application(urls, globals())
#template is called "Layout"
homepage_render = web.template.render('templates/', base="homepage")
render = web.template.render('templates/', base="layout")



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


class Sub_Index(object):
    def GET(self, directory):
        form = web.input(page="1")

        imagelist, imagerange, numberofimages, numberofpages = make_image_list(os.path.join(image_directory, directory), int(form.page))
        
        page = int(form.page)

        if page > 1:
            prevpage = page - 1
        else:
            prevpage = 0

        if (page - 1) < numberofpages:
            nextpage = page + 1
        else:
            nextpage = 0

        return render.index(imagelist, imagerange, numberofimages, prevpage, nextpage, urls, folderlist)

class Index(object):
    def GET(self):
        form = web.input(page="1")

        imagelist, imagerange, numberofimages, numberofpages = make_image_list(image_directory, int(form.page))
        
        page = int(form.page)

        if page > 1:
            prevpage = page - 1
        else:
            prevpage = 0

        if (page - 1) < numberofpages:
            nextpage = page + 1
        else:
            nextpage = 0

        return render.index(imagelist, imagerange, numberofimages, prevpage, nextpage, urls, folderlist)


class Settings(object):
    def POST(self):
        pass

if __name__ == "__main__":
    app.run()
