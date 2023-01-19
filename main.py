import DeviceFuncs
from datetime import datetime
import re

# *************************************************************************************
# **                          UPNP FETCH BOX EXTRACTOR                               **
# **                                By Deslea Judd                                   **
# *************************************************************************************
# This application extracts data about recorded media from a Fetch TV box and assembles
# a list of recordings available. Recordings are then prepared into a script for
# streaming to VLC for re-encoding to MP4, but the script is not executed (see below).
#
#  TODO: Future enhancement of text file record of recordings already made and
#   checks for duplicates, some flagging options are pre-provisioned.
#
# The end product is a BAT script; it is intended for the user to be able to work
# with the script manually from that point on (for instance, to run the jobs in batches
# overnight).
#
# It is not known to what extent the database schema of the Fetch box is common or
# custom to my provider; some customisation of variables may be required. There is
# guidance given for diagnosing and customising for this scenario in DeviceFuncs.py
# *************************************************************************************

# USER VARIABLES
# TRANSCODE_OPTS & DOWNSCALE_OPTS: VLC command line options, see https://wiki.videolan.org/transcode/
# DEST_DIR is where your bat file will be saved, and the location given in the script for your transcoded recordings.
# FETCHBOX_ADDR is the URI on the front of all your recording before the ID (including trailing forward slash), which 
#   you can find by looking at the Content URI in the Resource properties for any recording on the box in the uPNP Tools 
#   app AV Media Controller. 
# If you have a non-standard location for VLC, you also will need to edit this in two places below (search for newCom).
#   There are finicky interactions between Python, VLC, and .bat escaping, so this is not easily done as a variable here.
TRANSCODE_OPTS = "{vcodec=h264,scale=Auto,acodec=mpga,ab=128,channels=2,samplerate=44100,scodec=none,delinterlace}"
DOWNSCALE_OPTS = "{vcodec=h264,scale=Auto,fps=25,vb=1500,acodec=mpga,ab=128,channels=2,samplerate=44100,scodec=none,delinterlace}"
DEST_DIR = "C:\\Temp\\"
FETCHBOX_ADDR = "http://192.168.1.5:49152/web/"


# Get initial list of container and media objects

objList = []
seen = []

result = DeviceFuncs.get_children("0")
objList.extend(result)

for each in objList:
    if each['id'] in seen:
        pass
    else:
        result = DeviceFuncs.get_children(each['id'])
        objList.extend(result)
        seen.append(each['id'])

for each in objList:
    if each['id'] in seen:
        pass
    else:
        result = DeviceFuncs.get_children(each['id'])
        objList.extend(result)
        seen.append(each['id'])

# These iterations should be sufficient for boxes with a typical structure of Recordings/Show/Episode, but you can
# add more if needed. If adapting script for other uPNP devices with denser structures, use a recursive function.

# Create recording list

recordings = []
containers = {}
for each in objList:
    if each['type'] == 'container':
        containers[each['id']] = each['name']
    else:
        parentname = containers[each['parentID']]
        raw_fname = parentname + ' ' + each['name']
        stripped_fname = re.sub(r'[\W_]', '', raw_fname)
        fname = stripped_fname + '.mp4'
        fname = fname.replace('ampamp', 'And')
        fname = fname.replace('ampaposs', 's')
        uriLink = FETCHBOX_ADDR + each['id']
        recording = {"filename": fname, "uri": uriLink, "flag": "", "downscale": ""}
        recordings.append(recording)

# Create recording batch file

myScript = []
now = datetime.now()
batFile = DEST_DIR + now.strftime("%Y-%m-%d %H-%M-%S") + ".bat"

for each in recordings:
    if each['flag'] != "":
        continue
    elif each['downscale'] != "":
        newCom = "\"%PROGRAMFILES(x86)%\VideoLAN\VLC\\vlc.exe\" -I dummy " + each['uri'] + " :sout=#transcode" + DOWNSCALE_OPTS + ":std{access=file{no-overwrite},mux=mp4,dst=\"'" + DEST_DIR + each['filename'] + "'\"} vlc://quit"
    else:
        newCom = "\"%PROGRAMFILES(x86)%\VideoLAN\VLC\\vlc.exe\" -I dummy " + each['uri'] +" :sout=#transcode" + TRANSCODE_OPTS + ":std{access=file{no-overwrite},mux=mp4,dst=\"'" + DEST_DIR + each['filename'] + "'\"} vlc://quit"
    myScript.append(newCom)

f = open(batFile, "a")
f.write('@echo off\n')
f.write("echo This file will process the streams you have configured from the Fetch box.\n")
f.write("echo You may need to manually remove unwanted recordings (ie, ones already processed).\n")
f.write("echo You should also consider breaking the file into smaller batches, eg to run overnight.\n\n")

f.write("echo.\n")
f.write("echo There is no in-progress screen output. You will see 'Processing finished' when done.\n")
f.write("echo You can confirm the job is working by watching the destination folder for new video files.\n")
f.write("echo If a transcode seems 'stuck', close the command window and use Task Manager to terminate VLC.\n")
f.write("echo Delete the failed file, edit the BAT to remove the finished jobs, then run again.\n\n")

f.write("echo.\n")
f.write("echo IMPORTANT: If you have just created the script, some recordings may still be in progress.\n")
f.write("echo By default, a delay timer runs for 60 minutes before processing starts to avoid failed jobs.\n")
f.write("echo If you know there are no configured recordings still running, press a key to end the timer early.\n\n")

f.write("echo.\n")
f.write("TIMEOUT /T 3600")
f.write("\n\necho Processing started: \n")
f.write("time /t\n\n")

f.write("echo.\n")

for ea in myScript:
    f.write(ea)
    f.write('\n')

f.write("\n")
f.write("echo.\n")
f.write("echo Processing finished: \n")
f.write("time /t\n")
f.write("echo.\n")
f.write('\npause\n')
f.write('EXIT')
f.close()

