##!/usr/bin/python

# use a Tkinter label as a panel/frame with a background image
# note that Tkinter only reads gif and ppm images
# use the Python Image Library (PIL) for other image formats
# free from [url]http://www.pythonware.com/products/pil/index.htm[/url]
# give Tkinter a namespace to avoid conflicts with PIL
# (they both have a class named Image)

import time

import Tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from ttk import Frame, Button, Style

#import numpy
import cv2
#import cv2.cv as cv

from capture import capture
from textblock import find_text_block

REDRAW_DELAY = 1000

class Example(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        imageFile = "three.png"
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

        #self.update_image()
        self.original = Image.open(imageFile)

        self.image = ImageTk.PhotoImage(self.original)
        self.display = tk.Canvas(self, bd=0, highlightthickness=0)
        self.display.create_image(0, 0, image=self.image, anchor=tk.NW, tags="IMG")
        self.display.grid(row=0, sticky=tk.W+tk.E+tk.N+tk.S)
        self.pack(fill=tk.BOTH, expand=1)
        self.bind("<Configure>", self.resize_event)

        # pick an image file you have .bmp  .jpg  .gif.  .png
        # load the file and covert it to a Tkinter image object
        self.image = ImageTk.PhotoImage(Image.open(imageFile))
        #self.image2 = ImageTk.PhotoImage(Image.open("three.png"))

        # get the image size
        #w = self.image1.width()
        #h = self.image1.height()

        # position coordinates of root 'upper left corner'
        x = 0
        y = 0

        # make the root window the size of the image
        #self.root.geometry("%dx%d+%d+%d" % (w/2, h/2, x, y))

        # root has no image argument, so use a label as a panel
        #self.panel1 = tk.Label(self.root, image=self.image1)
        #self.display = self.image1
        #self.panel1.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        print("Display image1")

        self.bind("<Configure>", self.resize)

        self.after(REDRAW_DELAY, self.update_image)
        #self.root.mainloop()

    def update_image(self):
        # if self.display == self.image1:
        #     self.panel1.configure(image=self.image2)
        #     print "Display image2"
        #     self.display = self.image2
        # else:
        #     self.panel1.configure(image=self.image1)
        #     print "Display image1"
        #     self.display = self.image1

        captured = capture('page.png', 800, 600)
        captured.save('page.png')
        #find_text_block('page.png', 'marked.png', 'dilated.png')

        #dilated, marked = find_text_block(toOpenCV(captured))
        #dilated, _ = find_text_block(toOpenCV(captured))
        dilated, marked = find_text_block('page.png')
        cv2.imwrite('dilated.png', dilated)
        cv2.imwrite('marked.png', marked)
        #dilated = toPILImage(dilated)
        ##dilated, marked = toPILImage(dilated), toPILImage(marked)

        new_image = merge4('page.png', 'dilated.png', 'marked.png') #. save('three.png')
        new_image.save('three.png')

        #new_image = merge4(captured, dilated, marked) #. save('three.png')
        #new_image = merge4(captured, dilated, captured) #. save('three.png')
        #new_image.save('three.png')

        #self.original = new_image.copy()

        self.original = Image.open('three.png')
        self.resize((self.winfo_width(), self.winfo_height()))

        #self.image = ImageTk.PhotoImage(Image.open("three.png"))
        #self.panel1.configure(image=self.image)
        #self.panel1.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)

        self.after(REDRAW_DELAY, self.update_image)

    def resize(self, size):
        resized = self.original.resize(size, Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(resized)
        self.display.delete("IMG")
        self.display.create_image(0, 0, image=self.image, anchor=tk.NW, tags="IMG")

    def resize_event(self, event):
        size = event.width, event.height
        self.resize(size)

# def toOpenCV(pil_image):
#     return cv2.cvtColor(numpy.array(pil_image.copy()), cv2.COLOR_RGB2BGR)

# def toPILImage(opencv_image):
#     #from pdb import set_trace; set_trace()
#     #return Image.fromstring("RGB", cv.GetSize(opencv_image), opencv_image.tostring())
#     img = Image.fromarray(opencv_image.copy()) #, "RGB")
#     return img
#     #img_rgb = Image.merge('RGB', (img, img, img))
#     #return img_rgb

def merge4(name1, name2, name3):
#def merge4(img1, img2, img3):
    img1 = Image.open(name1)
    img2 = Image.open(name2)
    img3 = Image.open(name3)

    w, h = img1.size
    #w1, h1 = img1.size
    #w2, h2 = img2.size
    #w3, h3 = img3.size

    new = Image.new('RGB', (w * 2, h * 2))
    new.paste(img1, (0, 0))
    new.paste(img2, (w, 0))
    new.paste(img3, (0, h))

    draw = ImageDraw.Draw(new)
    draw.line((w, 0, w, h*2), fill=128, width=5)
    draw.line((0, h, w*2, h), fill=128, width=5)

    return new


def main():
    #app = Example()
    root = tk.Tk()
    root.title('My Pictures')
    app = Example(root)
    root.geometry("%dx%d+%d+%d" % (1200, 800, 0, 0))
    app.mainloop()
    root.destroy()


if __name__ == '__main__':
    main()
