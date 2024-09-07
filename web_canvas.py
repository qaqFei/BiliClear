from __future__ import annotations
from ctypes import windll
from os import chdir
from os.path import abspath, dirname
from sys import argv
from random import randint
import threading
import typing
import http.server
import time

import webview

selfdir = dirname(argv[0])
if selfdir == "": selfdir = abspath(".")
chdir(selfdir)

current_thread = threading.current_thread
screen_width = windll.user32.GetSystemMetrics(0)
screen_height = windll.user32.GetSystemMetrics(1)

class WebCanvas_FileServerHandler(http.server.BaseHTTPRequestHandler):
    _canvas:WebCanvas

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "image/png")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","*")
        self.send_header("Access-Control-Allow-Headers","Authorization, Content-Type")
        self.end_headers()
        if self.path[1:] in self._canvas._regres:
            data:bytes = self._canvas._regres[self.path[1:]]
            self.wfile.write(data)
        else:
            self.wfile.write(bytes())
    
    def log_request(self, *args, **kwargs) -> None: ...

class JsApi:
    def __init__(self) -> None:
        self.things:dict[str, typing.Any] = {}
    
    def __repr__(self):
        return "JsApi"
    
    def get_thing(self,name:str):
        return self.things[name]
    
    def set_thing(self,name:str,value:typing.Any):
        self.things[name] = value
    
    def get_attr(self,name:str):
        return getattr(self,name)
    
    def set_attr(self,name:str,value:typing.Any):
        setattr(self,name,value)
    
    def call_attr(self,name:str,*args,**kwargs):
        return getattr(self,name)(*args,**kwargs)

def ban_threadtest_current_thread():
    obj = current_thread()
    obj.name = "MainThread"
    return obj

webview.threading.current_thread = ban_threadtest_current_thread

class WebCanvas:
    def __init__(
        self,
        width:int,height:int,
        x:int,y:int,
        hidden:bool = False,
        debug:bool = False,
        title:str = "WebCanvas",
        resizable:bool = True,
        frameless:bool = False,
        web_kwargs:typing.Mapping = {},
        html_path:str = ".\\web_canvas.html"
    ):
        self.jsapi = JsApi()
        self._web = webview.create_window(
            title=title,
            url=abspath(html_path),
            resizable = resizable,
            js_api=self.jsapi,
            frameless=frameless,
            **web_kwargs
        )
        self._web_init_var = {
            "width":width,
            "height":height,
            "x":x,
            "y":y
        }
        self._destroyed = False
        self.debug = debug
        self._regres:dict[str, bytes] = {}
        self._JavaScript_WaitToExecute_CodeArray:list[str] = []
        threading.Thread(target=webview.start,kwargs={"debug":self.debug},daemon=True).start()
        self._init()
        if hidden:
            self.withdraw()
    
    def title(
        self,title:typing.Union[str,None]
    ) -> str:
        if title is None:
            return self._web.title
        self._web.set_title(title)
        return title
    
    def winfo_screenwidth(
        self
    ) -> int:
        return screen_width
    
    def winfo_screenheight(
        self
    ) -> int:
        return screen_height
    
    def winfo_width(
        self
    ) -> int:
        return self._web.width
    
    def winfo_height(
        self
    ) -> int:
        return self._web.height
    
    def winfo_x(
        self
    ) -> int:
        return self._web.x
    
    def winfo_y(
        self
    ) -> int:
        return self._web.y
    
    def winfo_focus(
        self
    ) -> bool:
        return self._web.focus

    def winfo_hwnd(
        self
    ) -> int:
        return self._web_hwnd
    
    def winfo_legacywindowwidth(
        self
    ) -> int:
        return self._web.evaluate_js("window.innerWidth;")
    
    def winfo_legacywindowheight(
        self
    ) -> int:
        return self._web.evaluate_js("window.innerHeight;")

    def destroy(
        self
    ):
        self._web.destroy()
    
    def maximize(
        self
    ):
        self._web.maximize()
    
    def resize(
        self,
        width:int,height:int
    ):
        self._web.resize(width=width,height=height)
    
    def move(
        self,
        x:int,y:int
    ):
        self._web.move(x=x,y=y)
    
    def withdraw(
        self
    ):
        self._web.hide()
    
    def deiconify(
        self
    ):
        self._web.show()
    
    def iconify(
        self
    ):
        self._web.minimize()
    
    def run_js_code(
        self,
        code:str,
        threading_:bool = False,
        add_code_array:bool = False
    ):
        if add_code_array:
            self.Add_Code_To_JavaScript_WaitToExecute_CodeArray(code)
        else:
            if threading_:
                threading.Thread(target=self._web.evaluate_js,args=(code,),daemon=True).start()
            else:
                return self._web.evaluate_js(code)
    
    def run_js_wait_code(
        self
    ):
        self._web.evaluate_js(f"JavaScript_WaitToExecute_CodeArray = {self._JavaScript_WaitToExecute_CodeArray};")
        self._web.evaluate_js("process_jswteca();")
        self._JavaScript_WaitToExecute_CodeArray.clear()
    
    def Add_Code_To_JavaScript_WaitToExecute_CodeArray(
        self,code:str
    ):
        self._JavaScript_WaitToExecute_CodeArray.append(code)
    
    def add_thing_to_javascript(
        self,
        name:str,value:typing.Any
    ):
        self.jsapi.things.update({name:value})
    
    def _set_style_fill_stroke(
        self,
        fillStyle:typing.Union[str,None] = None,
        strokeStyle:typing.Union[str,None] = None
    ) -> str:
        code = ""
        if fillStyle is not None:
            code += f"ctx.fillStyle = \"{fillStyle}\";"
        else:
            code += "ctx.fillStyle = \"#000000\";"
        if strokeStyle is not None:
            code += f"ctx.strokeStyle = \"{strokeStyle}\";"
        else:
            code += "ctx.strokeStyle = \"#000000\";"
        return code
    
    def _set_style_font_textAlign_textBaseline_direction(
        self,
        font:typing.Union[str,None] = None,
        textAlign:typing.Literal["start","end","left","right","center"] = "start",
        textBaseline:typing.Literal["top","hanging","middle","alphabetic","ideographic","bottom"] = "alphabetic",
        direction:typing.Literal["ltr","rtl","inherit"] = "inherit"
    ) -> str:
        code = ""
        if font is not None:
            code += f"ctx.font = \"{font}\";"
        else:
            code += "ctx.font = \"10px sans-serif\";"
        code += f"ctx.textAlign = \"{textAlign}\";"
        code += f"ctx.textBaseline = \"{textBaseline}\";"
        code += f"ctx.direction = \"{direction}\";"
        return code
    
    def process_code_string_syntax_tostring(
        self,code:str
    ):
        return code.replace("\\","\\\\").replace("'","\\'").replace("\"","\\\"").replace("`","\\`").replace("\n", "\\n")
    
    def create_rectangle(
        self,
        x0:typing.Union[int,float],y0:typing.Union[int,float],
        x1:typing.Union[int,float],y1:typing.Union[int,float],
        fillStyle:typing.Union[str,None] = None,
        strokeStyle:typing.Union[str,None] = None,
        threading_:bool = False,
        wait_execute:bool = False
    ) -> None:
        code = self._set_style_fill_stroke(fillStyle,strokeStyle) + f"\
            ctx.fillRect({x0},{y0},{x1-x0},{y1-y0});\
        "
        self.run_js_code(code,threading_,wait_execute)
    
    def create_text(
        self,
        x:typing.Union[int,float],y:typing.Union[int,float],
        text:str,
        font:typing.Union[str,None] = None,
        textAlign:typing.Literal["start","end","left","right","center"] = "start",
        textBaseline:typing.Literal["top","hanging","middle","alphabetic","ideographic","bottom"] = "alphabetic",
        direction:typing.Literal["ltr","rtl","inherit"] = "inherit",
        fillStyle:typing.Union[str,None] = None,
        strokeStyle:typing.Union[str,None] = None,
        threading_:bool = False,
        wait_execute:bool = False
    ) -> None:
        text = self.process_code_string_syntax_tostring(text)
        code = self._set_style_fill_stroke(fillStyle,strokeStyle) + self._set_style_font_textAlign_textBaseline_direction(font,textAlign,textBaseline,direction) + f"\
            ctx.fillText(\"{text}\",{x},{y});\
        "
        self.run_js_code(code,threading_,wait_execute)
    
    def clear_rectangle(
        self,
        x0:typing.Union[int,float],y0:typing.Union[int,float],
        x1:typing.Union[int,float],y1:typing.Union[int,float],
        threading_:bool = False,
        wait_execute:bool = False
    ) -> None:
        self.run_js_code(f"ctx.clearRect({x0},{y0},{x1-x0},{y1-y0});",threading_,wait_execute)
    
    def clear_canvas(
        self,
        threading_:bool = False,
        wait_execute:bool = False
    ) -> None:
        self.run_js_code("ctx.clearRect(0,0,canvas_ele.width,canvas_ele.height);",threading_,wait_execute)
    
    def reg_res(
        self,res_data:bytes,
        name:str
    ) -> None:
        self._regres.update({name:res_data})
    
    def reg_event(
        self,name:str,
        callback:typing.Callable
    ) -> None:
        setattr(self._web.events, name, getattr(self._web.events, name) + callback)
    
    def dereg_event(
        self,name:str,
        callback:typing.Callable
    ) -> None:
        setattr(self._web.events, name, getattr(self._web.events, name) - callback)
    
    def loop_to_close(
        self
    ) -> None:
        while True:
            if self._destroyed:
                return None
            time.sleep(0.05)
    
    def shutdown_fileserver(
        self
    ) -> None:
        self._file_server.shutdown()
    
    def get_resource_path(
        self,name:str
    ) -> str:
        return f"http://127.0.0.1:{self._web_port + 1}/{name}"
    
    def _closed_callback(
        self
    ) -> None:
        self._destroyed = True
    
    def _init(
        self
    ) -> None:
        self._web.resize(width=self._web_init_var["width"],height=self._web_init_var["height"])
        self._web.move(x=self._web_init_var["x"],y=self._web_init_var["y"])
        self._web_init_var.clear()
        self._web.events.closed += self._closed_callback
        
        title = self._web.title
        temp_title = self._web.title + " " * randint(0, 4096)
        self._web.set_title(temp_title)
        while True:
            self._web_hwnd = windll.user32.FindWindowW(None, temp_title)
            if self._web_hwnd:
                break
        self._web.set_title(title)
        
        self._web_port = int(self._web._server.address.split(":")[2].split("/")[0])
        WebCanvas_FileServerHandler._canvas = self
        self._file_server = http.server.HTTPServer(("localhost",self._web_port + 1),WebCanvas_FileServerHandler)
        threading.Thread(target=lambda:self._file_server.serve_forever(poll_interval=0),daemon=True).start()