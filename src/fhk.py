#!/usr/bin/python
#
# Copyright (c) 2009 by Simeon Felis <simeonfelis@googlemail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# For more information on the GPL, please go to:
# http://www.gnu.org/copyleft/gpl.html
#


import os
#import pango
import pygtk
pygtk.require('2.0')
import gtk
import subprocess
import socket
import fcntl
import struct
import array
import re
#import gnome
#import gconf
import sys

class Par:
	def __init__(self):
		self.username=''                # -U
		self.codepage='cp850'           # -p
		self.charset='utf8'             # -y
		self.noupcasepasswd=True        # -C
		self.multiple=True              # -m

		self.drives = ['F', 'G', 'H', 'K', 'P']

		self.mounts = {'F': False,
		               'G': True,
		               'H': False,
		               'K': False,
		               'P': False}

		self.paths = {'F': os.path.expanduser('~/F'),
		              'G': os.path.expanduser('~/G'),
		              'H': os.path.expanduser('~/H'),
		              'K': os.path.expanduser('~/K'),
		              'P': os.path.expanduser('~/P')}

		self.volumes = {'F': 'soft1',
		                'G': '',    # Extracted from login name
		                'H': 'DATA1/fb',
		                'K': 'DATA3/kurs',
		                'P': 'DATA2/Projekt'}

		self.servers = {'F': 'fh-saturn1',
		                'G': '',
		                'H': 'fh-kroesus',
		                'K': 'fh-kroesus',
		                'P': 'fh-kroesus'}

		self.dns_names = {'F': 'fh-saturn1.fh-regensburg.de',
		                  'G': '', # Extracted from login name
		                  'H': 'fh-kroesus.fh-regensburg.de',
		                  'K': 'fh-kroesus.fh-regensburg.de',
		                  'P': 'fh-kroesus.fh-regensburg.de'}



class Fhk:
	def checkIPAddress (self):
	# returns true if an network interface is found
	# which has an IP address in the range of the University Regensburg
		#get all network interfaces
		max_possible = 128  # arbitrary. raise if needed.
		bytes = max_possible * 32
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		names = array.array('B', '\0' * bytes)
		outbytes = struct.unpack('iL', fcntl.ioctl(s.fileno(),
		                                           0x8912,  # SIOCGIFCONF
		                                           struct.pack('iL',
		                                                       bytes,
		                                                       names.buffer_info()[0])
		                                           ))[0]
		namestr = names.tostring()
		interfaces = [namestr[i:i+32].split('\0', 1)[0] for i in range(0, outbytes, 32)]
		print "Found following interfaces: "
		print interfaces

		# loop through all interfaces
		for face in interfaces:
			if (face != "lo"):		# don't check loopback
				s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				ipAddress=socket.inet_ntoa(fcntl.ioctl(s.fileno(),
				                                       0x8915,
				                                       struct.pack('256s', face))[20:24])
				#FIXME: IP check always TRUE!
				if (cmp(ipAddress[:10], '194.94.155') == 0 or cmp(ipAddress[:7], '172.16.' == 0)):			# HS Regensburg Bibliothek IP
					print "Using interface " + face + " with IP " + ipAddress
					return True
				else:
					print "No good interface found"
					return False

	def warningIPAddress(self):
		# Returns True if user wants to connect anyway
		builder = gtk.Builder()
		builder.add_from_file("diaIPAddressWarning.xml")
		dia = builder.get_object("diaIPAddressWarning")
		dia.show_all()
		if (dia.run() == gtk.RESPONSE_YES):
			dia.destroy()
			return True
		else:
			dia.destroy()
			return False

		return False

	def pathCleanup(self, path):
		if os.path.exists(path):
			if os.path.ismount(path):
				print path + " still mounted. Not removed"
				return False
			else:
				try:
					os.rmdir(path)
				except:
					print path + " not empty or no permissions for removing. Not removed"
					return False

		return True

	def pathCreate(self, path):
		if os.path.ismount(path):
			print "%s already mounted" % path
			return False
		else:
			if os.path.exists(path):
				print "%s already exists" % path
			else:
				try:
					os.mkdir(path)
				except:
					print "%s cannot be created" % path
					return False
		return True

	def on_entryUsername_changed(self, widget, data=None):
		# Extract information for storage server and folder name
		name = widget.get_text()
		#print name
		#parted = re.match(r"(?P<short_name>^\w{3}\d{5})\.(?P<context_number>\d)\.(?P<context_type>.+)\.(?P<context_end>[f|h][h|s]-regensburg\.de)$", name)
		#print parted.groupdict()

		entryVolume_G = self.builder.get_object("entryVolume_G")
		entryServer_G = self.builder.get_object("entryServer_G")
		entryDNSName_G = self.builder.get_object("entryDNSName_G")

		exp = re.compile(r"(^\.{0,1}\w{3}\d{5})")
		short_name = exp.search(name)
		exp = re.compile(r"(?<=\w{3}\d{5}\.)(\d)")
		number = exp.search(name)
		exp = re.compile(r"(?<=\w{3}\d{5}\.\d\.)(\w+)")
		type = exp.search(name)
		exp = re.compile(r"[f|h][h|s]-regensburg.de$")
		context = exp.search(name)

		try:
			if short_name.group(0)[0] == '.':
				short_name = short_name.group(0)[1:]
			else:
				short_name = short_name.group(0)
			entryVolume_G.set_text("user" + number.group(0) + "/" + number.group(0) + "/" + short_name)
			entryDNSName_G.set_text("fh-mars-user" + number.group(0) + ".hs-regensburg.de")
			entryServer_G.set_text("hs-mars")

			# When full context found, enable the Connect button
			type.group(0)
			context.group(0)
			self.btnConnect.set_sensitive(True)

		except:
			print "No full name context found"
			self.btnConnect.set_sensitive(False)

	def on_checkbuttonMounts_toggled(self, widget, data=None):
		for drive in self.par.drives:
			if self.checkbuttonHandles[drive].get_active():
				self.par.mounts[drive] = True
			else:
				self.par.mounts[drive] = False

	def on_btn_connect_clicked(self, widget, data=None):
		if self.entryPassword.get_text() == "":
			a = gtk.MessageDialog(parent=None,
			                      flags=gtk.DIALOG_MODAL,
			                      type=gtk.MESSAGE_ERROR,
			                      buttons=gtk.BUTTONS_CLOSE,
			                      message_format="Kein Passwort angegeben")
			a.show()
			a.run()
			a.destroy()
			return

		if (self.checkIPAddress() == False):
			if (self.warningIPAddress()):
				print "Trying to connect through unsecure network"
			else:
				return
		else:
			print "IP address OK"

		success = False
		for drive in self.par.drives:
			if self.par.mounts[drive]:
				if not self.pathCreate(self.entryPathHandles[drive].get_text()):
					continue #jump over that drive
				try:
					tmpCall = ["ncpmount",
					           "-V", self.entryVolumeHandles[drive].get_text(),
					           "-S", self.entryServerHandles[drive].get_text(),
					           "-A", self.entryDNSNameHandles[drive].get_text(),
					           "-U", self.entryUsername.get_text(),
					           "-P", self.entryPassword.get_text(),
					           "-p", self.entryCodepage.get_text(),
					           "-y", self.entryCharset.get_text(),
					           "-r", "2",
					           "-C", "-m",
					           self.entryPathHandles[drive].get_text()]
					#print "Calling "
					#for i in tmpCall:
					#	print "    " + i
					retcode = subprocess.call(tmpCall)
					if not retcode:
						success = True
					else:
						print "Returned %s" %retcode
						self.pathCleanup(self.entryPathHandles[drive].get_text())
						continue
				except:
					print "invalid arguments on ncpmount"
					continue

				print drive + " mounted"

			if success:
				self.btnDisconnect.set_sensitive(True)

		#gksu "ncpmount -S fh-kroesus -A fh-kroesus.fh-regensburg.de -P $PW -V DATA1/kurs -U fes37620.0.stud.fh-regensburg.de -C -m -p cp850 -y utf8 /media/K/"

	def on_btn_umount_clicked(self, widget, data=None):
		try:
			retcode = subprocess.call(["ncpumount", "-a"])
			print "Return %s" %retcode
		except ValueError:
			print "invalid arguments on ncpumount"
			return

		for drive in self.par.drives:
			self.pathCleanup(self.entryPathHandles[drive].get_text())

		tmpError = False
		for drive in self.par.drives:
			if os.path.ismount(self.entryPathHandles[drive].get_text()):
				tmpError = True

		if not tmpError: #Wenn kein Fehler aufgetreten ist
			self.btnDisconnect.set_sensitive(False)
			self.btnConnect.set_sensitive(True)
		else:

			a = gtk.MessageDialog(parent = None,
			                      flags=gtk.DIALOG_MODAL,
			                      type=gtk.MESSAGE_WARNING,
			                      buttons=gtk.BUTTONS_CLOSE,
			                      message_format=
"""Laufwerke koennen nicht ausgehaengt werden.
Versuchen Sie es nochmal""")
			swin=gtk.ScrolledWindow()
			swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
#			swin.add_with_viewport(view)
			swin.show_all()

			a.vbox.pack_start(swin)
			a.show()
			a.run()
			a.destroy()


	def on_btn_cancel_clicked(self, widget, data=None):
		gtk.main_quit()
		print "canceled"

	def on_window_destroy(self, widget, data=None):
		print "destroy"
		gtk.main_quit()

	def delete_event(self, widget, event, data=None):
		gtk.main_quit()
		return False

	def destroy(self, widget, data=None):
		gtk.main_quit()

	def main(self, data=None):
		gtk.main()

	def __init__(self):
#		program=gnome.program_init(app_id="fhk",
#		                           app_version="0.1 beta")#,
#		                           #module_info=[])#,
#		                           #argc=len(sys.argv))#,
#		                           #argv=sys.argv)
#
#
#		client = gconf.client_get_default()
#		clientPath = gnome.gconf_get_app_settings_relative(program, "")
#		client.add_dir(dir=clientPath,
#		               preload=gconf.CLIENT_PRELOAD_NONE)
#
#		try:
#			test = client.get_int("test")
#			print test
#		except:
#			print "couldn't retrieve key"
#		try:
#			value = gconf.value_new(GCONF_VALUE_INT)
#		except:
#			print "no success value new"
#
#		try:
#			gconf.value_set(value, 42)
#		except:
#			print "no  success value set"
#		try:
#			client.set_int("apps/fhk/test", 42)
#		except:
#			print "no successset_int"



		self.builder = gtk.Builder()
		self.builder.add_from_file("window.xml")
		self.builder.connect_signals(self)
		self.window = self.builder.get_object("window")
		self.window.show()
		self.par = Par()

		# Get some handles to UI
		self.entryUsername = self.builder.get_object("entryUsername")
		self.entryPassword = self.builder.get_object("entryPassword")
		self.labelWarning = gtk.Label
		self.labelWarning = self.builder.get_object("labelWarning")
		self.btnDisconnect = self.builder.get_object("btn_umount")
		self.btnConnect = self.builder.get_object("btn_connect")
		self.entryCodepage = self.builder.get_object("entryCodepage")
		self.entryCharset = self.builder.get_object("entryCharset")
		self.entryPathHandles = {}
		self.entryVolumeHandles = {}
		self.entryServerHandles = {}
		self.entryDNSNameHandles = {}
		self.checkbuttonHandles = {}
		self.expanderHandles = {}
		for drive in self.par.drives:
			self.entryPathHandles.setdefault( drive,
				self.builder.get_object("entryPath_" + drive) )
			self.entryVolumeHandles.setdefault( drive,
				self.builder.get_object("entryVolume_" + drive) )
			self.entryServerHandles.setdefault( drive,
				self.builder.get_object("entryServer_" + drive) )
			self.entryDNSNameHandles.setdefault( drive,
				self.builder.get_object("entryDNSName_" + drive) )
			self.checkbuttonHandles.setdefault( drive,
				self.builder.get_object("checkbuttonMount_" + drive) )
			self.expanderHandles.setdefault(drive,
				self.builder.get_object("expander_" + drive) )

		#init gui
		self.entryCodepage.set_text(self.par.codepage)
		self.entryCharset.set_text(self.par.charset)
		self.btnDisconnect.set_sensitive(False)
		for drive in self.par.drives:
			self.entryPathHandles[drive].set_text(self.par.paths[drive])
			self.entryVolumeHandles[drive].set_text(self.par.volumes[drive])
			self.entryServerHandles[drive].set_text(self.par.servers[drive])
			self.entryDNSNameHandles[drive].set_text(self.par.dns_names[drive])
			self.checkbuttonHandles[drive].set_sensitive(True)
			self.checkbuttonHandles[drive].set_active(self.par.mounts[drive])
			self.expanderHandles[drive].set_sensitive(True)
			if os.path.ismount( self.par.paths[drive] ):
				print drive + " aready mounted"
				self.btnDisconnect.set_sensitive(True)
		# try to fill in G drive parameters:
		self.on_entryUsername_changed(self.entryUsername)

if __name__ == '__main__':
	fhk = Fhk()
	fhk.main()
