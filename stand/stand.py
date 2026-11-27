"""
Adjustable desktop stand for the Elecrow CrowPanel Advance 2.8" HMI (v1.2 housing).

Two printed parts:
  cradle - landscape pocket the panel slides into from the top; pivot lugs at the bottom
  base   - foot with two hinge cheeks + a pocket for a ~2000mAh pouch LiPo behind the hinge

Hinge = friction: one M3 bolt per side, through the cheek into a captive nut in the cradle lug.
Tighten until it holds angle.  A peg on each lug rides an arc slot in the cheek -> hard stops
at 45 deg and 90 deg (screen angle measured from the table).

Coordinates: the cradle is modelled in the panel's own frame from Elecrow's STEP
(reference/crowpanel28_v1.2_normalized.step):  X 0..83 (width), Y 0..58.5 (height),
screen faces -Z (glass front z=-7.9, bezel front z=-6.7, back cover z=8.0, screw heads to 9.0).

Run:  python stand.py            -> out/*.stl, out/*.3mf, out/*.step, checks printed
      python stand.py --render   -> also renders/*.png
"""
import math, sys, os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- panel (from STEP) ----------------
PW, PH = 83.0, 58.5
Z_BEZEL, Z_BACK = -6.7, 8.0
CORNER_SCREWS = [(4.0, 5.25), (79.0, 5.25), (4.0, 53.25), (79.0, 53.25)]  # front M3 / back M2.5 heads, 6mm dia

# ---------------- tunables ----------------
C = 0.3            # panel-to-pocket clearance (sides)
WALL = 2.5         # cradle side/top wall
# Bare-board mount (rev 3): Elecrow housing removed; PCB held off the face plate by spacers.
PCB_FRONT = -1.6   # PCB front surface (STEP). Glass front is -7.9 -> 6.3 mm (user calipers: ~6.0)
FACE_T = 1.0       # face plate
SPACER_H = 5.0     # FACE_T + SPACER_H = PCB-to-glass-front distance (6.0 measured; 6.3 per STEP)
SPACER_D = 6.5     # round spacer, flat-clipped on the display side
SPACER_CLR = 0.25  # clearance from spacer flat to the display module (x 6.9..76.1)
SCREW_HOLE = 3.4   # M3 clearance through face + spacer
GLASS = (6.9, 76.1, 4.25, 54.25)   # glass extents from STEP (calipers: ~69 x 50)
WIN_C = 0.25       # window clearance around glass, per side
BACK_RAIL = 2.0    # rail left along the back edge of windowed walls
LEDGE_T = 3.0      # bottom ledge the panel sits on
LUG_T = 5.5        # pivot lug thickness (x)
PIVOT_DROP = 8.0   # pivot centre below ledge bottom
GAP = 0.2          # lug-to-cheek gap (bolt clamps it shut = friction)
CHEEK_T = 4.0
CHEEK_R = 11.0
BOLT_D = 3.4       # M3 clearance
NUT_AF = 5.5 + 0.35
NUT_DEPTH = 2.6
PEG_R_POS = 5.0    # peg distance from pivot
PEG_D = 3.0
PEG_H = 1.2
SLOT_W = PEG_D + 0.5
SLOT_DEPTH = PEG_H + 0.4
ANG_MIN, ANG_MAX = 45.0, 90.0

BASE_T = 4.0
PIVOT_H = 14.0     # pivot height above base top
FRONT = 22.0       # base extends this far in front of pivot (toward viewer)
# battery pocket (fits up to ~62 x 52 x 10.5; e.g. 103450/104050/605060-ish 2000mAh packs)
BAT_X, BAT_Y, BAT_Z = 63.0, 53.0, 11.0
BAT_WALL = 2.0
BAT_GAP = 20.0     # pocket front wall distance behind pivot
FOOT_D, FOOT_DEPTH = 10.5, 1.0

# ---------------- derived ----------------
X_IN0, X_IN1 = -C, PW + C
X_OUT0, X_OUT1 = X_IN0 - WALL, X_IN1 + WALL
Z_OUT0, Z_OUT1 = PCB_FRONT - SPACER_H - FACE_T, Z_BACK   # face plate front .. walls end flush with panel back
Z_FACE = Z_OUT0 + FACE_T   # back of face plate
Y_BOT = -C - LEDGE_T
Y_TOP = PH + C + WALL
PY = Y_BOT - PIVOT_DROP
PZ = (Z_OUT0 + Z_OUT1) / 2
LUG_R = (Z_OUT1 - Z_OUT0) / 2   # lug stays inside the face plane so the cradle prints face-down flat


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def zcyl(x, y, r, z0, z1):
    return cq.Workplane("XY").circle(r).extrude(z1 - z0).translate((x, y, z0))


def xcyl(y, z, r, x0, x1):
    return cq.Workplane("YZ").circle(r).extrude(x1 - x0).translate((x0, y, z))


# ============================ CRADLE ============================
def make_cradle():
    # Face plate + perimeter walls. Panel drops in from the back (open), glass pokes through a
    # glass-sized window flush with the face, and the panel's own front M3 corner screws go
    # back in through slots in the face plate.
    body = box(X_OUT0, X_OUT1, Y_BOT, Y_TOP, Z_OUT0, Z_OUT1)
    body = body.cut(box(X_IN0, X_IN1, -C, PH + C, Z_FACE, Z_OUT1 + 1))                   # pocket, open back
    gx0, gx1, gy0, gy1 = GLASS
    body = body.cut(box(gx0 - WIN_C, gx1 + WIN_C, gy0 - WIN_C, gy1 + WIN_C, Z_OUT0 - 1, Z_FACE + .01))  # window
    # PCB spacers at the 4 corner holes (75 x 48 c/c); M3 through face + spacer + PCB, nut behind PCB
    for x, y in CORNER_SCREWS:
        sp = zcyl(x, y, SPACER_D / 2, Z_FACE - .01, Z_FACE + SPACER_H)
        clip_x = gx0 - SPACER_CLR if x < PW / 2 else gx1 + SPACER_CLR   # flat facing the display module
        sp = sp.cut(box(clip_x, clip_x + 20, y - 10, y + 10, Z_FACE - 1, Z_FACE + SPACER_H + 1) if x < PW / 2
                    else box(clip_x - 20, clip_x, y - 10, y + 10, Z_FACE - 1, Z_FACE + SPACER_H + 1))
        body = body.union(sp)
        body = body.cut(zcyl(x, y, SCREW_HOLE / 2, Z_OUT0 - 1, Z_FACE + SPACER_H + 1))
    # side windows: USB-C x2 on one short edge, openings on the other (y 8..46) -> both sides,
    # a 2 mm rail is kept along the back edge for stiffness (USB-C overmold sits at z ~-2..4.5)
    for xs in ((X_OUT0 - 1, X_IN0 + .01), (X_IN1 - .01, X_OUT1 + 1)):
        body = body.cut(box(*xs, 7.0, 47.5, Z_FACE + 1.0, Z_OUT1 - BACK_RAIL))
    # long-edge windows (housing opening x 6.8..27.7 on one long edge; mirrored top+bottom so either way up fits)
    for x0, x1 in ((6.0, 28.5), (PW - 28.5, PW - 6.0)):
        body = body.cut(box(x0, x1, Y_BOT - 1, -C + .01, Z_FACE + 1.0, Z_OUT1 - BACK_RAIL))
        body = body.cut(box(x0, x1, PH + C - .01, Y_TOP + 1, Z_FACE + 1.0, Z_OUT1 - BACK_RAIL))

    # pivot lugs
    for xo, sign in ((X_OUT0, +1), (X_OUT1, -1)):
        xa, xb = sorted((xo, xo + sign * LUG_T))
        lug = box(xa, xb, PY, Y_BOT + .01, PZ - LUG_R, PZ + LUG_R).union(xcyl(PY, PZ, LUG_R, xa, xb))
        lug = lug.cut(xcyl(PY, PZ, BOLT_D / 2, xa - 1, xb + 1))
        # captive nut on the inner face (vertex along Z = up when printed face-down -> no support)
        xin = xb if sign > 0 else xa
        nut = (cq.Workplane("YZ").transformed(rotate=(0, 0, 30))
               .polygon(6, NUT_AF / math.cos(math.pi / 6)).extrude(NUT_DEPTH)
               .translate((xin - NUT_DEPTH if sign > 0 else xin, PY, PZ)))
        lug = lug.cut(nut)
        # stop peg on outer face, pointing +Z (cradle back) from the pivot
        xp0, xp1 = (xa - PEG_H, xa + .01) if sign > 0 else (xb - .01, xb + PEG_H)
        lug = lug.union(xcyl(PY, PZ + PEG_R_POS, PEG_D / 2, xp0, xp1))
        body = body.union(lug)
    return body


# ===================== world placement =====================
# World: X same as panel, Y = toward viewer (+), Z up. Pivot at (Y=0, Z=BASE_T+PIVOT_H).
PIVOT_W = cq.Vector(0, 0, BASE_T + PIVOT_H)


def place(shape, theta):
    """theta = screen angle from table (90 = vertical, 45 = reclined)."""
    return (shape.translate((0, -PY, -PZ))
            .rotate((0, 0, 0), (1, 0, 0), 180 - theta)
            .translate(PIVOT_W))


def peg_world(theta):
    rot = math.radians(180 - theta)
    dy, dz = 0.0, PEG_R_POS
    return (dy * math.cos(rot) - dz * math.sin(rot), dy * math.sin(rot) + dz * math.cos(rot))


# ============================ BASE ============================
def make_base():
    x_ch_in0, x_ch_in1 = X_OUT0 - GAP, X_OUT1 + GAP
    x0, x1 = x_ch_in0 - CHEEK_T - 2, x_ch_in1 + CHEEK_T + 2
    pocket_front = -BAT_GAP - BAT_WALL
    y_back = pocket_front - BAT_Y - 2 * BAT_WALL
    xc = (X_OUT0 + X_OUT1) / 2
    base = box(x0, x1, y_back, FRONT, 0, BASE_T).edges("|Z").fillet(6)

    # battery pocket walls
    bx0, bx1 = xc - BAT_X / 2 - BAT_WALL, xc + BAT_X / 2 + BAT_WALL
    tray = box(bx0, bx1, y_back, pocket_front + BAT_WALL, BASE_T - .01, BASE_T + BAT_Z)
    tray = tray.cut(box(bx0 + BAT_WALL, bx1 - BAT_WALL, y_back + BAT_WALL, pocket_front, BASE_T, BASE_T + BAT_Z + 1))
    tray = tray.cut(box(xc - 6, xc + 6, pocket_front - 1, pocket_front + BAT_WALL + 1, BASE_T + 3, BASE_T + BAT_Z + 1))  # cable notch
    tray = tray.cut(box(xc - 12, xc + 12, y_back - 1, y_back + BAT_WALL + 1, BASE_T + 4, BASE_T + BAT_Z + 1))  # finger notch
    base = base.union(tray)
    # strap slots (velcro tie) through floor, both ends of pocket
    for sx in (bx0 + BAT_WALL + 6, bx1 - BAT_WALL - 6):
        base = base.cut(box(sx - 1.5, sx + 1.5, pocket_front - BAT_Y / 2 - 11, pocket_front - BAT_Y / 2 + 11, -1, BASE_T + 1))

    # cheeks
    pz = PIVOT_W.z
    p_lo, p_hi = peg_world(ANG_MIN), peg_world(ANG_MAX)
    a_lo = math.atan2(p_lo[1], p_lo[0]); a_hi = math.atan2(p_hi[1], p_hi[0])
    if a_hi - a_lo > math.pi: a_hi -= 2 * math.pi   # take the short way round
    if a_lo - a_hi > math.pi: a_hi += 2 * math.pi
    for xin, sign in ((x_ch_in0, -1), (x_ch_in1, +1)):
        xa, xb = sorted((xin, xin + sign * CHEEK_T))
        ch = box(xa, xb, -CHEEK_R, CHEEK_R, BASE_T - .01, pz).union(xcyl(0, pz, CHEEK_R, xa, xb))
        # gusset outward
        ch = ch.union(box(*sorted((xb if sign > 0 else xa, (xb if sign > 0 else xa) + sign * 2)), -CHEEK_R, CHEEK_R, BASE_T - .01, BASE_T + 6))
        ch = ch.cut(xcyl(0, pz, BOLT_D / 2, xa - 3, xb + 3))
        # stop-slot arc on inner face
        xs0, xs1 = (xin - SLOT_DEPTH, xin + .01) if sign < 0 else (xin - .01, xin + SLOT_DEPTH)
        n = 24
        for i in range(n + 1):
            a = a_lo + (a_hi - a_lo) * i / n
            ch = ch.cut(xcyl(PEG_R_POS * math.cos(a), pz + PEG_R_POS * math.sin(a), SLOT_W / 2, xs0, xs1))
        base = base.union(ch)

    # rubber-foot recesses
    for fx in (x0 + 8, x1 - 8):
        for fy in (y_back + 8, FRONT - 8):
            base = base.cut(zcyl(fx, fy, FOOT_D / 2, -1, FOOT_DEPTH))
    return base


# ============================ checks ============================
def load_panel():
    p = os.path.join(HERE, "reference", "crowpanel28_v1.2_normalized.step")
    if not os.path.exists(p):
        return None
    sols = cq.importers.importStep(p).val().Solids()
    # drop the 4 front M3x12 corner screws: they get reinstalled through the face-plate slots
    # bare board: drop the housing (bezel/shell/back, all 83 mm wide) and the corner screws
    keep = [s for s in sols if s.BoundingBox().xlen < 82.9
            and not (s.BoundingBox().xlen < 7 and (s.BoundingBox().zmin < -7.5 or s.BoundingBox().zmax > 8.9))]
    print(f"panel: {len(sols)} solids, {len(sols) - len(keep)} housing/screw solids excluded (bare-board mount)")
    print(f"glass front vs face front: {(-7.9) - Z_OUT0:+.2f} mm (negative = glass proud of face)")
    return cq.Compound.makeCompound(keep)


def vol(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:
        return float("nan")


def main():
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    cradle = make_cradle()
    base = make_base()
    cs, bs = cradle.val(), base.val()
    print(f"cradle bbox {cs.BoundingBox().xlen:.1f} x {cs.BoundingBox().ylen:.1f} x {cs.BoundingBox().zlen:.1f}  vol {cs.Volume()/1000:.1f} cm3")
    print(f"base   bbox {bs.BoundingBox().xlen:.1f} x {bs.BoundingBox().ylen:.1f} x {bs.BoundingBox().zlen:.1f}  vol {bs.Volume()/1000:.1f} cm3")

    panel = load_panel()
    if panel is not None:
        # bounding box of panel solids that collide with cradle (exclude screws which sit in reliefs)
        print(f"panel  x  cradle volume: {vol(panel, cs):.3f} mm3 (want 0)")

    # mass / CoG: PLA ~1.24 g/cc @ ~40% effective; panel 100 g; battery ~40 g
    pla = 1.24e-3 * 0.4
    bat_c = cq.Vector((X_OUT0 + X_OUT1) / 2, -BAT_GAP - BAT_WALL - BAT_Y / 2, BASE_T + BAT_Z / 2)
    y_back = -BAT_GAP - 2 * BAT_WALL - BAT_Y - BAT_WALL
    for th in (45, 55, 65, 75, 90):
        c = place(cs, th)
        inter = vol(c, bs)
        pc = place(cq.Vertex.makeVertex(PW / 2, PH / 2, 0.5), th).Center()
        m = [(100, pc), (40, bat_c), (cs.Volume() * pla, c.Center()), (bs.Volume() * pla, bs.Center())]
        M = sum(w for w, _ in m)
        cog_y = sum(w * v.y for w, v in m) / M
        line = f"theta {th:>3}: cradle x base {inter:7.3f} mm3 | lowest cradle Z {c.BoundingBox().zmin:5.1f} | CoG Y {cog_y:6.1f} (base {y_back:.0f}..{FRONT:.0f}) mass {M:.0f} g"
        if panel is not None:
            line += f" | panel x base {vol(place(panel, th), bs):.3f}"
        print(line)

    for name, s in (("cradle", cradle), ("base", base)):
        for ext in ("stl", "step", "3mf"):
            try:
                cq.exporters.export(s, os.path.join(HERE, "out", f"{name}.{ext}"))
            except Exception as e:
                print(f"export {name}.{ext} failed: {e}")
    if "--render" in sys.argv:
        import render
        render.render_all(cs, bs, panel, place, HERE)


if __name__ == "__main__":
    main()
