# moodboard

Moodboard Database Schema

CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, emailaddress TEXT, passwordhash TEXT, salt TEXT, userfolder TEXT, datejoined TEXT, imagesperpage INTEGER, privilege INTEGER default "0", email_verified INTEGER default "0", emailhash TEXT, favourites TEXT);
CREATE TABLE images(id INTEGER PRIMARY KEY, owner INTEGER, absolutepath TEXT UNIQUE, filename TEXT, path TEXT, hexcolour TEXT, hsv1 TEXT, hue1 TEXT, hsv2 TEXT, hue2 TEXT, hsv3 TEXT, hue3 TEXT, tags TEXT, bw INTEGER);


Colours Database Schema

CREATE TABLE images(id INTEGER PRIMARY KEY, owner INTEGER, absolutepath TEXT UNIQUE, filename TEXT, path TEXT, hexcolour TEXT, hsv1 TEXT, hue1 TEXT, hsv2 TEXT, hue2 TEXT, hsv3 TEXT, hue3 TEXT);
