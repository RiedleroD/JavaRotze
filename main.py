import re
import os

class_search = r"(private|public|protected) class (\w+)[\n\s+\{]"
vars_search = r"(private|public|protected) (\w+) (\w+)[\s*\=\s*\w+]?;"
general_search = r"(public|private|protected) ([^\(\)\{\;\}\n ]* )?([^\(\)\{\;\}\n ]*)\(([^)]*)\)"

import gi

gi.require_version("Gtk","3.0")
from gi.repository import Gtk
Gtk.init()#because for some reason if nuitka is used, a bug in gtk is triggered that isn't considered a bug by the gtk devs…

def quit_for_good(widget):#this is also because nuitka triggers something idk
	Gtk.main_quit()

class MainWin(Gtk.Window):
	def __init__(self):
		Gtk.Window.__init__(self, title="C# is net so sharp")
		
		self.box=Gtk.Box(spacing=2,orientation=Gtk.Orientation.VERTICAL,homogeneous=False)
		self.add(self.box)
		
		self.tv=Gtk.TextView(editable=False,cursor_visible=False,left_margin=12,top_margin=8,right_margin=8)
		self.buf=Gtk.TextBuffer()
		self.tv.set_buffer(self.buf)
		self.box.pack_start(self.tv,True,True,2)
		
		self.fc=Gtk.FileChooserButton()
		self.ff=Gtk.FileFilter()
		self.ff.add_pattern("*.java")
		self.fc.add_filter(self.ff)
		self.fc.connect("file-set",self.on_fileset)
		self.box.pack_start(self.fc,False,True,0)
	def on_fileset(self,widget):
		thing=self.get_thing(widget.get_filename())
		print(thing)
		self.buf.set_text(thing,len(thing))
	def get_thing(self,fn):
		with open(fn, 'r') as f:
			text = f.read()
		final = []
		class_text = re.findall(class_search, text)
		if len(class_text) == 0:
			return "No class found"
		class_text = class_text[0][1]
		final += class_text + "\n\n"
		variables = re.findall(vars_search, text)
		if len(variables) > 0:
			for var in variables:
				if var[0] == 'private' or var[0] == 'protected':
					final.append("- ")
				else:
					final.append("+ ")
				final.append(f"{var[2]}: {var[1]}\n")
			final.append("\n")
		methods = re.findall(general_search, text)
		if len(methods) > 0:
			for mtd in methods:
				if mtd[0] == 'private' or mtd[0] == 'protected':
					final.append("- ")
				else:
					final.append("+ ")
				final.append(mtd[2] + "(")
				params = []
				if mtd[3] != '':
					for param in mtd[3].split(","):
						if param.startswith(" "):
							param = ''.join(param[1:])
						param = param.split(" ")
						params.append(f"{param[1]}: {param[0]}")
				final.append(', '.join(params) + ")")
				modifier = mtd[1].replace(" ", "")
				if modifier != '':
					final.append(": ")
				final.append(modifier + "\n")
		final="".join(final)
		while final.endswith("\n"):
			final=final[:-1]
		return final

win=MainWin()
win.connect("destroy",quit_for_good)
win.show_all()
Gtk.main()
