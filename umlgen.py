import re

_generic_regex = r"\<\w+\>"#matches a generic declaration
_name_regex    = r"[^\W ]+"#matches one variable-, function-, or classname
_datatype_regex= r"(?:[^\W ]|[\<\>])+(?:\[\])*"#matches one datatype (including arrays and generics)
_params_regex  = r" *(?:(final) +)?("+_datatype_regex+r") +("+_name_regex+r") *,? *"#matches one parameter in a function
#TODO: still works → func(int a int b) ← missing comma
_state_regex   = r"(public|protected|private|package)"#matches a publicity state

class_search = re.compile(_state_regex+r" +class +("+_name_regex+r")(?: *("+_generic_regex+r"))?")
vars_search  = re.compile(r"(?:(final) +)?"+_state_regex+r" +(?:(static) +)?("+_datatype_regex+r") +("+_name_regex+r") *(?:\= *([^;]*?) *)?;")
funcs_search = re.compile(_state_regex+r" +(?:(static) +)?(?:("+_generic_regex+r") *)?(?:("+_datatype_regex+r") +)?("+_name_regex+") *\((("+_params_regex+r")*)\)")
params_search= re.compile(_params_regex)

import gi
gi.require_version("Gtk","3.0")
from gi.repository import Gtk,Gio,GLib,Gdk,GdkPixbuf
Gtk.init()

def escape(txt:str)->str:
	return txt.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

class Status:
	_dc_map=["public","protected","private","package"]
	_ec_map=['+','#','-','~','?']
	def __init__(self,stat):
		if type(stat)==int:
			if 0<=stat<=4:
				self.val=stat
			else:
				self.val=4
		elif type(stat)==str:
			self.val=self.stat2val(stat)
	def format(self):
		return self._ec_map[self.val]
	@classmethod	
	def stat2val(cls,status:str)->int:
		if status in cls._dc_map:
			return cls._dc_map.index(status)
		else:
			return 4

class Klasse:
	def __init__(self,status:Status,name:str):
		self.name=name
		self.status=status
	def format(self,y,x):
		return f"<text y=\"{y}\" x=\"{x}\" text-anchor=\"middle\">{self.status.format()}{self.name}</text>"
	def format_simple(self):
		return f"{self.status.format()}{self.name}"
	def width(self):
		return len(self.name)+1
	@classmethod
	def search(cls,txt:str):
		kls=class_search.search(txt)
		return cls(Status(kls[1]),kls[2])#TODO get multiple classes in one file

class Variable:
	def __init__(self,status:Status,static:bool,dtype:str,name:str,final:bool=False,val:str=None):
		self.status=status
		self.static=static
		self.dtype=dtype
		self.name=name
		self.final=final
		self.val=val;
	def format(self,y):
		return f"<text y=\"{y}\" x=\"5\">{self.status.format()}{self.format_name()}: {escape(self.dtype)}{self.format_val()}{self.format_final()}</text>"
	def format_name(self):
		if self.static:
			return f"<tspan class=\"static\">{self.name}</tspan>"
		else:
			return self.name
	def format_val(self):
		if self.val:
			return " = "+self.val
		else:
			return ""
	def format_final(self):
		if self.final:
			return "{readOnly}"
		else:
			return ""
	def format_simple(self):
		return f"{self.status.format()}{self.format_name_simple()}: {self.dtype}{self.format_val()}{self.format_final()}"
	def format_name_simple(self):
		if self.static:
			return f"_{self.name}_"
		else:
			return self.name
	def width(self):
		return len(self.name)+3+len(self.dtype)
	@classmethod
	def search(cls,txt:str):
		return [cls(Status(vr[1]),vr[2]=="static",vr[3],vr[4],vr[0]=="final",vr[5]) for vr in vars_search.findall(txt)]

class Parameter:
	def __init__(self,dtype:str,name:str,final:bool=False):
		self.dtype=dtype
		self.name=name
	def format(self):
		return f"{self.name}: {self.dtype}"
	def width(self):
		return len(self.name)+len(self.dtype)+2
	@classmethod
	def search(cls,txt:str):
		return [cls(pr[1],pr[2],pr[0]=="final") for pr in params_search.findall(txt)]

class Method:
	def __init__(self,status:Status,static:bool,rtype:str,name:str,params:[Parameter],generic:str):
		self.status=status
		self.static=static
		self.rtype=rtype
		self.name=name
		self.params=params
		self.generic=generic
	def format(self,y):
		return f"<text y=\"{y}\" x=\"5\">{self.status.format()}{escape(self.generic)}{self.format_main()}{escape(self.format_rtype())}</text>"
	def format_rtype(self):
		if self.rtype and self.rtype!="void":
			return ": "+self.rtype
		else:
			return ""
	def format_main(self):
		string=f"{self.name}({', '.join([escape(p.format()) for p in self.params])})";
		if self.static:
			return f"<tspan class=\"static\">{string}</tspan>"
		else:
			return string
	def format_simple(self):
		return f"{self.status.format()}{self.generic}{self.format_main_simple()}{self.format_rtype()}"
	def format_main_simple(self):
		string=f"{self.name}({', '.join([p.format() for p in self.params])})";
		if self.static:
			return f"_{string}_"
		else:
			return string
	def width(self):
		return sum(param.width() for param in self.params)+(len(self.params)-1)*2+len(self.name)+(5 if self.rtype else 3)+len(self.rtype)
	@classmethod
	def search(cls,txt:str):
		return [cls(Status(mt[0]),mt[1]=="static",mt[3],mt[4],Parameter.search(mt[5]),mt[2]) for mt in funcs_search.findall(txt)]

def quit_for_good(widget):#this is also because nuitka triggers something idk
	Gtk.main_quit()

class MainWin(Gtk.Window):
	def __init__(self):
		Gtk.Window.__init__(self, title="C# is net so sharp")
		
		self.box=Gtk.Box(spacing=2,orientation=Gtk.Orientation.VERTICAL,homogeneous=False)
		
		self.viewbox=Gtk.Box(spacing=2,orientation=Gtk.Orientation.HORIZONTAL,homogeneous=False)
		
		self.tv=Gtk.TextView(editable=False,cursor_visible=False,left_margin=12,top_margin=8,right_margin=8)
		self.buf=Gtk.TextBuffer()
		self.tv.set_buffer(self.buf)
		self.viewbox.pack_start(self.tv,True,True,2)
		
		stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(b"<svg></svg>"))
		pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
		self.svgwidget = Gtk.Image.new_from_pixbuf(pixbuf)
		self.viewbox.pack_start(self.svgwidget,True,True,2)
		
		self.box.pack_start(self.viewbox,True,True,2)
		
		self.fc=Gtk.FileChooserButton()
		self.ff=Gtk.FileFilter()
		self.ff.add_pattern("*.java")
		self.fc.add_filter(self.ff)
		self.fc.connect("file-set",self.on_fileset)
		self.box.pack_start(self.fc,False,True,0)
		
		self.add(self.box)
	def on_fileset(self,widget):
		fn=widget.get_filename()
		with open(fn, 'r') as f:
			txt = f.read()
		cls=Klasse.search(txt)
		vrs=Variable.search(txt)
		meths=Method.search(txt)
		allobjs=(cls,*vrs,*meths)
		maxwidth=0
		for obj in allobjs:
			width=obj.width()
			if width>maxwidth:
				maxwidth=width
		width=5*maxwidth+10#assuming font-size:10px and that characters are roughly half as wide as they're tall
		height=len(allobjs)*12+6
		text=	f"<svg width=\"{width}\" height=\"{height}\" xmlns=\"http://www.w3.org/2000/svg\">"\
				"<!--Created with umlgen by Riedler-->"\
				"<style>.static{text-decoration:underline}text{font-size:10px}path{fill:#FFF;stroke:#000}</style>"\
				f"<path d=\"M0.5 0v{height-0.5}h{width-1}v-{height-1}h-{width-1}M0.5 13.5h{width-1}M0.5 {15.5+len(vrs)*12}h{width-1}\"/>"\
				f"{cls.format(10,width/2)}{''.join([obj.format(12+i*12) for i,obj in enumerate(vrs,1)])}{''.join([obj.format(13+i*12) for i,obj in enumerate(meths,len(vrs)+1)])}</svg>"
		simple="\n\n".join("\n".join(obj.format_simple() for obj in objs) for objs in ((cls,),vrs,meths))
		self.buf.set_text(simple,len(simple))
		fp=fn+".svg"
		with open(fp,"w+") as f:
			f.write(text)
		self.update_svgview(fp)
	def update_svgview(self,fp):
		rect=self.svgwidget.get_allocation()
		buf=GdkPixbuf.Pixbuf.new_from_file_at_scale(fp,rect.width,rect.height,True)
		self.svgwidget.set_from_pixbuf(buf)

win=MainWin()
win.connect("destroy",quit_for_good)
win.show_all()
Gtk.main()
