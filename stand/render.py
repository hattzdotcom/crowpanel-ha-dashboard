"""Quick matplotlib renders of the stand (assembly at several angles + parts)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def _tris(shape, tol=0.3):
    v, t = shape.tessellate(tol, 0.3)
    return [[(v[i].x, v[i].y, v[i].z) for i in tri] for tri in t]


def _draw(ax, items, elev, azim):
    allp = []
    for shape, color, alpha in items:
        tris = _tris(shape)
        allp += [p for tr in tris for p in tr]
        ax.add_collection3d(Poly3DCollection(tris, facecolors=color, edgecolors=color, alpha=alpha, shade=True))
    xs, ys, zs = zip(*allp)
    c = [(max(a) + min(a)) / 2 for a in (xs, ys, zs)]
    r = max(max(a) - min(a) for a in (xs, ys, zs)) / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev, azim); ax.set_axis_off()


def render_all(cradle, base, panel, place, here):
    out = os.path.join(here, "renders"); os.makedirs(out, exist_ok=True)
    for th in (45, 65, 90):
        fig = plt.figure(figsize=(12, 6))
        for k, (elev, azim, ttl) in enumerate(((15, 60, "front 3/4"), (5, 0, "side"))):
            ax = fig.add_subplot(1, 2, k + 1, projection="3d")
            items = [(base, "#4a7ab0", 1.0), (place(cradle, th), "#d0d0d0", 1.0)]
            if panel is not None:
                items.append((place(panel, th), "#303030", 0.8))
            _draw(ax, items, elev, azim); ax.set_title(f"{th} deg - {ttl}")
        fig.tight_layout(); fig.savefig(os.path.join(out, f"assembly_{th}.png"), dpi=90); plt.close(fig)
    fig = plt.figure(figsize=(12, 6))
    for k, (s, ttl, elev, azim) in enumerate(((cradle, "cradle (back)", 25, 210), (base, "base", 35, 120))):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        _draw(ax, [(s, "#c0c0c0", 1.0)], elev, azim); ax.set_title(ttl)
    fig.tight_layout(); fig.savefig(os.path.join(out, "parts.png"), dpi=90); plt.close(fig)
    print("renders ->", out)
