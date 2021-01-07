import re

class_search = re.compile(r"(private|public|protected) class (\w+)[\n\s+\{]")
vars_search = re.compile(r"(private|public|protected) +(static +)?(\w+) +([\w( *\, *)]+) *(\=[^;]*)?;")
funcs_search = re.compile(r"(public|private|protected) (static )?([^\(\)\{\;\}\n ]* )?([^\(\)\{\;\}\n ]*)\(([^)]*)\)")

from PIL import Image as Img
from PIL import ImageDraw as Draw
from PIL import ImageFont as Font
import gi

gi.require_version("Gtk","3.0")
from gi.repository import Gtk
Gtk.init()#because for some reason if nuitka is used, a bug in gtk is triggered that isn't considered a bug by the gtk devs…

def quit_for_good(widget):#this is also because nuitka triggers something idk
	Gtk.main_quit()

def format_params(params):
	return ", ".join(": ".join(reversed(param.split(" "))) for param in params.split(",") if param.replace(" ",""))

def format_return(ret):
	if ret:
		return f": {ret}"
	else:
		return ""

def format_publicity(pub):
	if pub=="public":
		return "+"
	elif pub=="protected":
		return "#"
	elif pub=="private":
		return "-"
	elif pub=="package":
		return "~"
	else:
		return "?"
def format_static(stat):
	if "static" in stat:
		return "\033[4m"
	else:
		return "\033[0m"

def format_varnames(varnames):
	return varnames.replace(" ","").replace(",",", ")

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
		fn=widget.get_filename()
		thing=self.get_thing(fn)
		while "\n\n\n" in thing:
			thing=thing.replace("\n\n\n","\n\n")
		print(thing)
		stuff=thing.replace("\033[0m","\033[4m").replace("\033[4m","")
		self.buf.set_text(stuff,len(stuff))
		self.to_png(thing,fn+".png")
	def to_png(self,thing,fn):
		things=thing.split("\n")
		try:
			fnt=Font.truetype("arial.ttf",10)
		except OSError:
			fnt=Font.truetype("NimbusRoman-Regular.otf")
		width=max(len(x) for x in things)*5+6
		height=len(things)*11+6
		img=Img.new(mode='RGB',size=(width,height),color=(255,255,255))
		draw=Draw.Draw(img)
		for i,line in enumerate(things):
			if line:
				if line[0]=="\033":
					static=line[2]=="4"
					line=line[4:]
				else:
					static=False
				le,he=draw.textsize(line,font=fnt)
				draw.text((3,3+i*11),line,font=fnt,fill=(0,0,0))
				if static:
					draw.line((3,3+he+i*11,3+le,3+he+i*11),fill=(0,0,0))
			else:
				draw.rectangle((0,5+i*11,width,8+i*11),fill=(0,0,0))
		draw.rectangle((0,0,width-1,height-1),outline=(0,0,0),width=2)
		img.save(fn)
	def get_thing(self,fn):
		with open(fn, 'r') as f:
			txt = f.read()
		cls=class_search.search(txt).group(2)
		vrs="\n".join([f"{format_static(vr[1])}{format_publicity(vr[0])}{vr[3]}: {format_varnames(vr[2])}" for vr in vars_search.findall(txt)])
		fncs="\n".join([f"{format_static(vr[1])}{format_publicity(vr[0])}{vr[3]}({format_params(vr[4])}){format_return(vr[2])}" for vr in funcs_search.findall(txt)])
		return f"{cls}\n\n{vrs}\n\n{fncs}"

win=MainWin()
win.connect("destroy",quit_for_good)
win.show_all()
Gtk.main()
