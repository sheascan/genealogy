import os, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import cairo


from gramps.gen.utils.callback import Callback
from gramps.gen.dbstate import DbState
from gramps.gui.dbloader import DbLoader
import gramps.gui.widgets.fanchart as fanchart

class MockUIState(Callback):
    def __init__(self):
        super().__init__()
        self.symbols = False
        self.death_symbol = 0
        self.window = None
        self._active = {}

    def get_active(self, name):
        return self._active.get(name)

    def set_active(self, name, value):
        self._active[name] = value
        self.emit('active-changed', (name, value))

MockUIState.__signals__ = {'active-changed': (str, object)}

DB_DIR = os.path.expanduser("~/.gramps/grampsdb/6adf1de1")
OUT_SVG = os.path.expanduser("~/Genealogy/website/Ancestry.svg")

dbstate = DbState()
uistate = MockUIState()
loader = DbLoader(dbstate, uistate)
loader.read_file(DB_DIR)
db = dbstate.db

root_person = None
for h in db.get_person_handles():
    p = db.get_person_from_handle(h)
    if p.get_gramps_id() == "I500003":
        root_person = p
        break

if root_person:
    first_name = root_person.get_primary_name().get_first_name()
    last_name = root_person.get_primary_name().get_surname()
    print(f"Root Ancestor: {first_name} {last_name} ({root_person.get_gramps_id()})")

    widget = fanchart.FanChartWidget(dbstate, uistate)
    widget.set_values(
        root_person_handle=root_person.handle,
        maxgen=5,
        background=0,
        childring=0,
        flipupsidedownname=True,
        twolinename=False,
        radialtext=False,
        fontdescr="",
        grad_start="#f59e0b",
        grad_end="#388da8",
        filtr=None,
        alpha_filter=1.0,
        form=0,
        showid=False
    )

    # Compute data structures and build angles
    widget.reset()

    hd = widget.halfdist()
    dim = int(2 * (hd + 80))
    print(f"FanChart dimensions: {dim}x{dim}")

    surface = cairo.SVGSurface(OUT_SVG, dim, dim)
    cr = cairo.Context(surface)
    widget.draw(ctx=cr, scale=1.0)
    surface.finish()

    print(f"SUCCESS: Ancestry.svg saved to {OUT_SVG}")
else:
    print("Could not find person I500003")

dbstate.db.close()
