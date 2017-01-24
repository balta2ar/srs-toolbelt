// Compile as follows:
//
// gcc overlay.c -o overlay -lX11 -lXfixes -lXcomposite -lcairo
//

#include <assert.h>
#include <stdio.h>
#include <time.h>
#include <X11/Xlib.h>

#include <X11/extensions/Xcomposite.h>
#include <X11/extensions/Xfixes.h>
#include <X11/extensions/shape.h>

#include <cairo/cairo.h>
#include <cairo/cairo-xlib.h>

Display *d;
Window overlay;
Window root;
int width, height;

void
allow_input_passthrough (Window w)
{
    XserverRegion region = XFixesCreateRegion (d, NULL, 0);

    XFixesSetWindowShapeRegion (d, w, ShapeBounding, 0, 0, 0);
    XFixesSetWindowShapeRegion (d, w, ShapeInput, 0, 0, region);

    XFixesDestroyRegion (d, region);
}

void
prep_overlay (void)
{
    overlay = XCompositeGetOverlayWindow (d, root);
    allow_input_passthrough (overlay);
}

void draw(cairo_t *cr) {
    int quarter_w = width / 4;
    int quarter_h = height / 4;
    cairo_set_source_rgb(cr, 1.0, 0.0, 0.0);
    cairo_rectangle(cr, quarter_w, quarter_h, quarter_w * 2, quarter_h * 2);
    cairo_fill(cr);
}

int main() {
    struct timespec ts = {0, 5000000};

    d = XOpenDisplay(NULL);

    int s = DefaultScreen(d);
    root = RootWindow(d, s);

    XCompositeRedirectSubwindows (d, root, CompositeRedirectAutomatic);
    XSelectInput (d, root, SubstructureNotifyMask);

    width = DisplayWidth(d, s);
    height = DisplayHeight(d, s);

    prep_overlay();

    cairo_surface_t *surf = cairo_xlib_surface_create(d, overlay,
                                  DefaultVisual(d, s),
                                  width, height);
    cairo_t *cr = cairo_create(surf);

    XSelectInput(d, overlay, ExposureMask);

    draw(cr);

    XEvent ev;
    while(1) {
      overlay = XCompositeGetOverlayWindow (d, root);
      draw(cr);
      XCompositeReleaseOverlayWindow (d, root);
      nanosleep(&ts, NULL);
    }

    cairo_destroy(cr);
    cairo_surface_destroy(surf);
    XCloseDisplay(d);
    return 0;
}
