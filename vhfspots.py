#!/usr/bin/python
#
# vhfspots.py
#
# 04/01/2019
#
# Copyright 2019 Brian Graves - VA3DXV
#
# va3dxv@gmail.com
#
# https://github.com/va3dxv
#
#   This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# pulls band predictions from dxlite
#
# This script requires access to http://api.voicerss.org (it's free)
# as well as lame and sox to create the .ul file for asterisk
#
# Run this file from roots crontab to create the audio file every hour
# 0 */1 * * * /usr/local/sbin/vhfspots.py >/dev/null 2>&1
#
# Add this to /etc/asterisk/rpt.conf under [functions]
# 85=cmd,asterisk -rx "rpt localplay 99999 /etc/asterisk/custom/vhfspots"
#
# (where 99999 is your node number)
#
#################################
import datetime
import shlex
import subprocess

import pytz
import requests
import xmltodict

#
# configuration
#
# set your voicerss API key here
voicersskey = "yourvoicerssapikeygoeshere"
# set your desired voice language here
voicersslang = "en-us"
# set speed of speech here
voicerssspeed = "-2"
# set format of initial audio before converting to ulaw
voicerssformat = "44khz_16bit_mono"
#
# end configuration
#
temppath = "/tmp/"
aslpath = "/etc/asterisk/custom/"
scriptname = "vhfspots"
aslfile = aslpath + "vhfspots"
filetxt = temppath + scriptname + ".txt"
filemp3 = temppath + scriptname + ".mp3"
filewav = temppath + scriptname + ".wav"
fileul = aslfile + ".ul"
xml_data = requests.get(
    url="http://dxlite.g7vjr.org/?xml=1&band=vhf&dxcc=001&limit=3")
spots_data = xmltodict.parse(xml_data.text)
textfile = open(filetxt, "w")
textfile.write(
    "Here are the three most recent DX spots for six meters and up...\n")
for spots in spots_data["spots"]["spot"]:
    date_string = spots["time"]
    utc = pytz.utc
    est = pytz.timezone("US/Eastern")
    utc_datetime = utc.localize(datetime.datetime.strptime(
        date_string, "%Y-%m-%d %H:%M:%S"))
    textfile.write(spots["spotter"] + " spotted " + spots["dx"] + " on " + spots["frequency"].split(".")
                   [0] + " on " + utc_datetime.astimezone(est).strftime("%B %d") + " at " + utc_datetime.astimezone(est).strftime("%I:%M%p") + "...\n")
textfile.write("End of report.")
textfile.close()
dxspots = open(filetxt, "r")
getmp3 = requests.get("http://api.voicerss.org/", data={
                      "key": voicersskey, "r": voicerssspeed, "src": dxspots, "hl": voicersslang, "f": voicerssformat})
mp3file = open(filemp3, "wb")
mp3file.write(getmp3.content)
mp3file.close()
# convert to wav with lame (apt-get install lame) then to ulaw with sox (apt-get install sox)
subprocess.call(shlex.split("lame --decode " + filemp3 + " " + filewav))
subprocess.call(shlex.split("sox -V " + filewav +
                            " -r 8000 -c 1 -t ul " + fileul))
# cleanup
subprocess.call(shlex.split("rm -f " + filetxt))
subprocess.call(shlex.split("rm -f " + filemp3))
subprocess.call(shlex.split("rm -f " + filewav))
