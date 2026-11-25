#!/usr/bin/env python3
"""
Rebuilds assets/about.svg with your photos fading in on the right side.
With several photos they cross-fade one after another, in a loop.

Usage (run from the repo root):
    python3 scripts/add_photos.py photo1.jpg
    python3 scripts/add_photos.py photo1.jpg photo2.jpg photo3.jpg
    python3 scripts/add_photos.py            # no photos, text only

Options:
    --color        keep the original photo colors (default: black and white)
    --seconds N    how long each photo stays (default: 5)

Needs ImageMagick (the "magick" or "convert" command) when you pass photos.
"""
import argparse
import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

W, H = 900, 400          # whole banner
PX, PW = 480, 420        # photo area: starts at x=480, 420 wide, full height
FADE = 1.2               # cross-fade length, seconds
PEAK = 0.92              # photo opacity when fully visible

TAGLINE = "building infrastructure, one commit at a time"
T_START, T_STEP = 1.2, 0.03   # typing: first letter at 1.2s, one letter every 0.03s

ABOUT = [
    "IT student at the Bucharest University",
    "of Economic Studies.",
]
INTERESTS = [
    "Interested in infrastructure as code,",
    "cloud networking, automation and reliable",
    "systems. Security is next on my list.",
]
STATUS = "Open to internships and junior roles"


def photo_b64(path: str) -> str:
    im = shutil.which("magick") or shutil.which("convert")
    if not im:
        sys.exit("ImageMagick not found. Install it first: sudo apt install imagemagick")
    with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
        subprocess.run(
            [im, path, "-auto-orient", "-resize", f"{PW*2}x{H*2}^", "-gravity", "center",
             "-extent", f"{PW*2}x{H*2}", "-strip", "-quality", "78", tmp.name],
            check=True,
        )
        return base64.b64encode(Path(tmp.name).read_bytes()).decode()


def build(photos: list[str], color: bool, hold: float) -> str:
    n = len(photos)
    typed = "".join(
        f'<tspan class="c" style="animation-delay:{T_START + i * T_STEP:.3f}s">'
        f'{"&#160;" if ch == " " else ch}</tspan>'
        for i, ch in enumerate(TAGLINE)
    )
    cursor_delay = T_START + len(TAGLINE) * T_STEP + 0.2

    about = "".join(f'<text class="sans body t" x="60" y="{214 + i * 22}">{t}</text>' for i, t in enumerate(ABOUT))
    interests = "".join(f'<text class="sans body t hi" x="60" y="{276 + i * 22}">{t}</text>' for i, t in enumerate(INTERESTS))

    # photos
    photo_css, photo_svg = "", ""
    if n:
        flt = "" if color else ' filter="url(#bw)"'
        if n == 1:
            photo_css = f".p {{ opacity:0; animation:p-in 2.4s ease-out 1s forwards; }}\n    @keyframes p-in {{ to {{ opacity:{PEAK} }} }}"
        else:
            d = n * hold
            pct = lambda s: f"{s / d * 100:.3f}%"
            photo_css = (
                f".p {{ opacity:0; animation:xf {d:.2f}s linear infinite; }}\n"
                + "".join(f"    .p{i} {{ animation-delay:{1 + i * hold:.2f}s; }}\n" for i in range(n))
                + f"    @keyframes xf {{ 0% {{ opacity:0 }} {pct(FADE)} {{ opacity:{PEAK} }} "
                f"{pct(hold)} {{ opacity:{PEAK} }} {pct(hold + FADE)} {{ opacity:0 }} 100% {{ opacity:0 }} }}"
            )
        imgs = "".join(
            f'<image class="p p{i}" x="{PX}" y="0" width="{PW}" height="{H}" preserveAspectRatio="xMidYMid slice"{flt} '
            f'xlink:href="data:image/jpeg;base64,{photo_b64(p)}"/>'
            for i, p in enumerate(photos)
        )
        photo_svg = f'<g mask="url(#fade-y)"><g mask="url(#fade-x)">{imgs}</g></g>'

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" role="img" aria-label="Mihai. Building infrastructure, one commit at a time. IT student at the Bucharest University of Economic Studies. Open to internships and junior roles.">
  <title>Mihai</title>
  <style>
    :root {{ --fg:#e6edf3; --body:#c9d1d9; --mute:#8b949e; --accent:#e3a857; }}
    @media (prefers-color-scheme: light) {{
      :root {{ --fg:#1f2328; --body:#3d444d; --mute:#59636e; --accent:#9a6700; }}
    }}
    .sans {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Helvetica Neue",Helvetica,Arial,sans-serif; }}
    .mono {{ font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace; }}

    .rule  {{ stroke:var(--accent); stroke-width:2; stroke-dasharray:84; stroke-dashoffset:84;
             animation:draw .9s cubic-bezier(.2,.7,.2,1) .1s forwards; }}
    .name  {{ fill:var(--fg); font-size:64px; font-weight:600; letter-spacing:-2px; opacity:0;
             animation:rise 1s cubic-bezier(.2,.7,.2,1) .4s forwards; }}
    .cmd   {{ fill:var(--mute); font-size:15px; white-space:pre; }}
    .c     {{ opacity:0; animation:on 0s linear forwards; }}
    .cur   {{ fill:var(--accent); opacity:0; animation:blink 1.1s steps(1) {cursor_delay:.2f}s infinite; }}
    .body  {{ font-size:15px; fill:var(--body); }}
    .hi    {{ fill:var(--fg); }}
    .t, .status {{ opacity:0; animation:fade 1s ease-out 2.4s forwards; }}
    .status {{ font-size:14px; fill:var(--mute); }}
    .dot   {{ fill:var(--accent); }}
    .ring  {{ fill:none; stroke:var(--accent); stroke-width:1.5; opacity:0; transform-box:fill-box; transform-origin:center;
             animation:pulse 2.6s ease-out 3s infinite; }}
    {photo_css}

    @keyframes draw  {{ to {{ stroke-dashoffset:0 }} }}
    @keyframes rise  {{ from {{ opacity:0; transform:translateY(10px) }} to {{ opacity:1; transform:none }} }}
    @keyframes on    {{ to {{ opacity:1 }} }}
    @keyframes fade  {{ to {{ opacity:1 }} }}
    @keyframes blink {{ 0%,49.99% {{ opacity:1 }} 50%,100% {{ opacity:0 }} }}
    @keyframes pulse {{ 0% {{ transform:scale(1); opacity:.7 }} 100% {{ transform:scale(3.4); opacity:0 }} }}

    @media (prefers-reduced-motion: reduce) {{
      * {{ animation:none !important; }}
      .name, .c, .cur, .t, .status {{ opacity:1 !important; }}
      .rule {{ stroke-dashoffset:0 !important; }}
      .ring {{ opacity:0 !important; }}
      .p {{ opacity:0 !important; }}
      .p0 {{ opacity:{PEAK} !important; }}
    }}
  </style>

  <defs>
    <linearGradient id="gx" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000"/><stop offset=".45" stop-color="#fff"/>
      <stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#000"/>
    </linearGradient>
    <linearGradient id="gy" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000"/><stop offset=".14" stop-color="#fff"/>
      <stop offset=".86" stop-color="#fff"/><stop offset="1" stop-color="#000"/>
    </linearGradient>
    <mask id="fade-x" maskUnits="userSpaceOnUse" x="{PX}" y="0" width="{PW}" height="{H}"><rect x="{PX}" y="0" width="{PW}" height="{H}" fill="url(#gx)"/></mask>
    <mask id="fade-y" maskUnits="userSpaceOnUse" x="{PX}" y="0" width="{PW}" height="{H}"><rect x="{PX}" y="0" width="{PW}" height="{H}" fill="url(#gy)"/></mask>
    <filter id="bw"><feColorMatrix type="saturate" values="0"/></filter>
  </defs>

  {photo_svg}

  <line class="rule" x1="60" y1="60" x2="144" y2="60"/>
  <text class="sans name" x="60" y="122">Mihai</text>
  <text class="mono cmd" x="60" y="160" xml:space="preserve">{typed}<tspan class="cur">_</tspan></text>
  {about}
  {interests}
  <circle class="ring" cx="64" cy="359" r="4"/>
  <circle class="dot status" cx="64" cy="359" r="4"/>
  <text class="sans status" x="80" y="364">{STATUS}</text>
</svg>
'''


def main() -> None:
    ap = argparse.ArgumentParser(description="Build assets/about.svg with fading photos.")
    ap.add_argument("photos", nargs="*", help="up to 5 photos (jpg/png)")
    ap.add_argument("--color", action="store_true", help="keep photo colors")
    ap.add_argument("--seconds", type=float, default=5.0, help="seconds per photo")
    a = ap.parse_args()
    if len(a.photos) > 5:
        sys.exit("Use at most 5 photos.")
    out = Path(__file__).resolve().parent.parent / "assets" / "about.svg"
    out.write_text(build(a.photos, a.color, a.seconds), encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB, {len(a.photos)} photo(s))")


if __name__ == "__main__":
    main()
