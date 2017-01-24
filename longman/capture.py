from Xlib import display
import gtk.gdk
from PIL import Image
import sys

def cursor_pos():
    c = display.Display().screen().root.query_pointer()._data
    x = c["root_x"]
    y = c["root_y"]
    print x, y
    return x, y

def grab_at(x1, y1, width, height):
    w = gtk.gdk.get_default_root_window()
    wi, he = w.get_size()
    #pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,wi,he)
    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,width,height)
    pb = pb.get_from_drawable(w, w.get_colormap(),
                              x1, y1, 0, 0,
                              width, height)
    if (pb == None):
        return False
    else:
        width,height = pb.get_width(),pb.get_height()
        try:
            return Image.fromstring("RGB",(width,height),pb.get_pixels() )
        except:
            return Image.frombytes("RGB",(width,height),pb.get_pixels() )

def capture(filename, width, height):
    cx, cy = cursor_pos()
    img = grab_at(cx - width / 2, cy - height / 2, width, height)
    #img.save(filename)
    return img

if __name__ == '__main__':
    filename = sys.argv[1]
    width, height = int(sys.argv[2]), int(sys.argv[3])
    img = capture(filename, width, height)
    img.save(filename)
    print(img)
#from pdb import set_trace; set_trace()

#img = ImageGrab.grab()
#from ipdb import set_trace; set_trace()
#print('done')
