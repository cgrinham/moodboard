"""
moodboard Uploader 0.57

Copyright Christie Grinham 2014
Contact: christiegrinham@gmail.com

This is a very early version of the software and as such I have not decided on
a software licence. Currently I will not allow any copying or commercial usage
of this software without prior written consent, which can be obtainer by using
the email address provided above. 

TO USE:

Replace "TYPE IMAGE FOLDER HERE" with the path to your imagefolder then run the script.

"""



import socket
import struct
import os
import pickle
import getpass
import time
from datetime import datetime
from sys import argv


local = 2

if local == 0:
    server_address = ("127.0.0.1", 10000) # address, port
    initimagefolder = 'input'
elif local == 1:
    server_address = ("192.168.1.100", 10000) # address, port
    initimagefolder = 'TYPE IMAGE FOLDER HERE'
else:
    server_address = ("christophski.ddns.net", 10000) # address, port
    initimagefolder = 'TYPE IMAGE FOLDER HERE'



def get_logtime():
    """ Return the date and time """
    return datetime.now().strftime('%Y/%m/%d %H:%M')

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    """Helper function to recv n bytes or return None if EOF is hit"""
    data = ''

    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet

    return data

def login(username, password):
    print "%s: Log in to server" % get_logtime()
    send_msg(connection, "login") # request login

    incoming = recv_msg(connection)

    if incoming == "username": # if server requests username
        send_msg(connection, username) # send username to server

        incoming = recv_msg(connection)
        if incoming == "password": # if server requests password
            send_msg(connection, password)

            incoming = recv_msg(connection)
            #print >>sys.stderr, incoming

            if incoming == "login_success":
                return True, "Login Successful"
            elif incoming == "unverified":
                return False, "Login Unsuccessful, please verify your account before uploading."
            else:
                return False, "Login Unsuccessful. Username or password incorrect."

        else:
            return False, "Server requested something unexpected. Expect 'password' request, received '%s' instead" % incoming
    else:
        return False, "Server requested something unexpected. Expect 'username' request, received '%s' instead" % incoming


def upload(folder):
    """ Upload all the files in a folder """

    imagefolder = initimagefolder

    print 'Uploading folder "%s"' % folder
    send_msg(connection, "list") # request list of files on server

    send_msg(connection, folder)

    server_list = pickle.loads(recv_msg(connection)) # receive list of files

    #print server_list

    newlist = []

    if folder == "root":
        pass
    else:
        imagefolder = os.path.join(imagefolder, folder)
        print "New imagefolder is %s" % imagefolder


    filelist = [f for f in os.listdir(imagefolder) if os.path.isfile(os.path.join(imagefolder, f)) and f.endswith(('.jpg', '.jpeg', '.png')) and not f.startswith('.')]

    #print "filelist for %s is %s" % (imagefolder, filelist)

    # Sort filelist by date added(?)
    filelist.sort(key=lambda x: os.stat(os.path.join(imagefolder, x)).st_mtime)
    #filelist.reverse() # reverse image list so new files are first

    # If file isn't on server, add to list to be uploaded
    for userfile in filelist:
        if userfile not in server_list:
            newlist.append(userfile)
        else:
            pass

    # If the list isn't empty, upload the files
    if newlist:
        for filename in newlist:

            print "%s: Sending %s" % (get_logtime(), filename)

            send_msg(connection, "upload")

            cur_file = open(os.path.join(imagefolder, filename), 'rb') # open file
            strf = cur_file.read() # read file into variable

            send_msg(connection, filename)

            send_msg(connection, strf)

            print "%s: File sent" % get_logtime()
            print
        print "%s: Moodboard is up to date" % get_logtime()
    else:
        print "%s: Moodboard is up to date" % get_logtime()



print "moodboard Uploader 0.57"

print "Enter username:"
USERNAME = raw_input() # ask user for username

print "Enter password:"
PASSWORD = getpass.getpass()

while True:

    # Connect to server
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.connect(server_address)
    # Log in to server
    login_success, message = login(USERNAME, PASSWORD)


    if login_success == True:
        print "%s: %s" % (get_logtime(), message)


        # request folders listing
        print "Requesting directory listing"
        send_msg(connection, "listfolders")

        server_folder_list = pickle.loads(recv_msg(connection))

        print "Should be a folder list: %s" % server_folder_list

        # List local folder
        folderlist = [f for f in os.listdir(initimagefolder) if os.path.isdir(os.path.join(initimagefolder, f)) == True and f not in ("thumbs", "css", "js", "img")]

        newfolderlist = []

        # If local folder not in server list, add to new list
        for folder in folderlist:
            if folder not in server_folder_list:
                print "%s is new, adding it to newfolderlist" % folder
                newfolderlist.append(folder)
            else:
                print "No new folders"

        print newfolderlist

        # If newfolder list not empty, send it to server
        # else continue (Does the server need to know?)
        if newfolderlist:
            send_msg(connection, "makedir") # Tell server to make directories

            send_msg(connection, pickle.dumps(newfolderlist)) # send list of directories to make
            incoming = recv_msg(connection)
            print incoming
        else:
            pass

        upload("root")

        for folder in folderlist:
            upload(folder)

        print "Finished syncing, disconnecting from server"
        send_msg(connection, "finished")
    else:
        print "%s: %s" % (get_logtime(), message)
        quit()

    time.sleep(60)
