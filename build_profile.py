"""Build the GitHub README artwork and matching local previews with Pillow."""

import base64
from html import escape
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "profile"
OUT.mkdir(exist_ok=True)
WIDTH, HEADER_HEIGHT, HEIGHT = 960, 40, 872
CARD_WIDTH, CARD_HEIGHT, CONTACT_GAP = 320, 120, 16
SOCIALS = [
    ("linkedin", "LinkedIn", "uzuw", "https://www.linkedin.com/in/uzuw/"),
    ("instagram", "Instagram", "@uwuzu_", "https://www.instagram.com/uwuzu_"),
    ("discord", "Discord", "@uzuw", None),
]
BG, INK, MUTED, RULE = "#08121b", "#dce6e5", "#91a6af", "#20323e"
PAGE_BG, LINK = "#0d1117", "#b6d7df"
FONT = ROOT / "fonts/CommitMono-Regular.woff2"
font_data = base64.b64encode(FONT.read_bytes()).decode("ascii")
HEADER_TEXT = [("Ujjwal Rana Magar", 16, 13, INK, "start"),
               ("building", 198, 12, INK, "start"),
               ("github.com/uzuw", 944, 12, MUTED, "end")]
SPINNER_CELLS = [(178, 15), (183, 15), (178, 20), (183, 20)]
NAME = "Ujjwal Rana Magar."
NAME_INK = "#b9cbd2"
NAME_BOX = (24, HEADER_HEIGHT + 380, WIDTH - 24, HEADER_HEIGHT + 480)
NAME_MASK = Image.new("L", (NAME_BOX[2] - NAME_BOX[0], NAME_BOX[3] - NAME_BOX[1]))
ImageDraw.Draw(NAME_MASK).text((48 - NAME_BOX[0], HEADER_HEIGHT + 450 - NAME_BOX[1]), NAME,
                              font=ImageFont.truetype(str(FONT), 58), fill=255, anchor="ls")
namespace = "http://www.w3.org/2000/svg"
ET.register_namespace("", namespace)
ocean = ET.parse(ROOT / "mocks/moonwash.svg").getroot()
images = ocean.findall(f"{{{namespace}}}image")
assert len(images) == 2, "Moonwash needs its animation and reduced-motion still"
for image in images:
    image.set("y", str(HEADER_HEIGHT))
animation = Image.open(BytesIO(base64.b64decode(images[0].attrib["href"].split(",", 1)[1])))
assert animation.size == (240, 90) and animation.n_frames == 144

preview = Image.new("RGB", (WIDTH, HEIGHT), BG)
preview.paste(animation.convert("RGB").resize((WIDTH, 360), Image.Resampling.NEAREST), (0, HEADER_HEIGHT))
draw = ImageDraw.Draw(preview)
markup = []
copy = []


def text(value, x, y, size, color=INK, align="left"):
    y += HEADER_HEIGHT
    font = ImageFont.truetype(str(FONT), size)
    anchor = "ls" if align == "left" else "rs"
    bounds = draw.textbbox((x, y), value, font=font, anchor=anchor)
    assert 24 <= bounds[0] < bounds[2] <= WIDTH - 24, f"Text overflows: {value}"
    assert HEADER_HEIGHT + 360 <= bounds[1] < bounds[3] <= HEIGHT - 24, f"Text overflows: {value}"
    draw.text((x, y), value, font=font, fill=color, anchor=anchor)
    markup.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{"start" if align == "left" else "end"}">{escape(value)}</text>')
    copy.append(value)


def rule(y):
    y += HEADER_HEIGHT
    draw.line((48, y, 912, y), fill=RULE)
    markup.append(f'<path d="M48 {y}.5H912" stroke="{RULE}"/>')


def draw_header(canvas, seconds):
    header_draw = ImageDraw.Draw(canvas)
    header_draw.rectangle((0, 0, WIDTH - 1, HEADER_HEIGHT - 1), fill="#12222d")
    header_draw.line((0, HEADER_HEIGHT - 1, WIDTH - 1, HEADER_HEIGHT - 1), fill=RULE)
    for value, x, size, color, align in HEADER_TEXT:
        header_draw.text((x, 26), value, font=ImageFont.truetype(str(FONT), size),
                         fill=color, anchor="ls" if align == "start" else "rs")
    active = int((seconds % 0.8) / 0.2) % 4
    for index, (x, y) in enumerate(SPINNER_CELLS):
        header_draw.rectangle((x, y, x + 2, y + 2), fill=INK if index == active else "#40515a")


def draw_name_shine(canvas, seconds):
    center = -160 + 1200 * ((seconds % 8) / 8)
    values = []
    for x in range(NAME_MASK.width):
        distance = abs((x + NAME_BOX[0] - center) / 120)
        light = max(0, 1 - distance * 0.85 / 0.3) if distance <= 0.3 else max(0, 0.15 * (1 - distance) / 0.7)
        values.append(round(light * 255))
    band = Image.new("L", (NAME_MASK.width, 1))
    band.putdata(values)
    shine = ImageChops.multiply(NAME_MASK, band.resize(NAME_MASK.size))
    glow = shine.filter(ImageFilter.GaussianBlur(2.6)).point(lambda value: round(value * 0.6))
    canvas.paste(LINK, NAME_BOX, glow)
    canvas.paste("#f4ffff", NAME_BOX, shine)


draw_header(preview, 0)
text(NAME, 48, 450, 58, NAME_INK)
name_glyphs = markup.pop().replace(f'fill="{NAME_INK}"', 'id="name-glyphs"')
markup.append(f'<use href="#name-glyphs" fill="{NAME_INK}"/><g class="motion"><use href="#name-glyphs" fill="url(#name-light)" filter="url(#name-glow)"/></g>')
text("@uzuw", 912, 442, 16, MUTED, "right")
text("Hello git!!", 48, 498, 20)
text("Curious by default", 48, 536, 18, MUTED)
rule(582)
text("Right now", 48, 628, 15, MUTED)
text("Listening to Drake", 48, 668, 18)
text("and Frank Ocean.", 48, 698, 18)
text("Drawn to", 512, 628, 15, MUTED)
text("Code, design, and the small details", 512, 668, 18)
text("that make something feel alive.", 512, 698, 18)
rule(744)
text("Glad you washed up here.", 48, 793, 16)
text("stay curious.", 912, 793, 14, MUTED, "right")

description = " ".join(copy)
header_labels = ''.join(f'<text x="{x}" y="26" font-size="{size}" fill="{color}" text-anchor="{align}">{escape(value)}</text>'
                        for value, x, size, color, align in HEADER_TEXT)
loading, loading_still = [], []
for index, (x, y) in enumerate(SPINNER_CELLS):
    values = ';'.join('1' if step % 4 == index else '.25' for step in range(5))
    loading.append(f'<rect x="{x}" y="{y}" width="3" height="3" fill="{INK}"><animate attributeName="opacity" values="{values}" dur="0.8s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    loading_still.append(f'<rect x="{x}" y="{y}" width="3" height="3" fill="{INK if index == 0 else "#40515a"}"/>')
svg = f'''<svg xmlns="{namespace}" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Ujjwal Rana Magar — a little corner of the internet</title>
  <desc id="desc">A profile strip with a loading indicator above a moonlit ocean with rolling waves, twinkling stars, and drifting spiral clouds. {escape(description)}</desc>
  <style>
    @font-face {{ font-family: CommitMono; src: url(data:font/woff2;base64,{font_data}) format('woff2'); font-weight: 400; }}
    text {{ font-family: CommitMono, monospace; font-weight: 400; }}
    image {{ image-rendering: pixelated; }}
    .still {{ display: none; }}
    @media (prefers-reduced-motion: reduce) {{ .motion {{ display: none; }} .still {{ display: inline; }} }}
  </style>
  <defs>
    {name_glyphs}
    <linearGradient id="name-light" gradientUnits="userSpaceOnUse" x1="-280" y1="0" x2="-40" y2="0">
      <stop offset="0" stop-color="#f4ffff" stop-opacity="0"/>
      <stop offset=".35" stop-color="#f4ffff" stop-opacity=".15"/>
      <stop offset=".5" stop-color="#f4ffff"/>
      <stop offset=".65" stop-color="#f4ffff" stop-opacity=".15"/>
      <stop offset="1" stop-color="#f4ffff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="1200 0" dur="8s" repeatCount="indefinite"/>
    </linearGradient>
    <filter id="name-glow" x="-15%" y="-60%" width="130%" height="220%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="2.6" result="blur"/>
      <feComponentTransfer in="blur" result="glow"><feFuncA type="linear" slope=".6"/></feComponentTransfer>
      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <path fill="{BG}" d="M0 0H{WIDTH}V{HEIGHT}H0Z"/>
  <path fill="#12222d" d="M0 0H960V40H0Z"/><path d="M0 39.5H960" stroke="{RULE}"/>
  {header_labels}<g class="motion">{''.join(loading)}</g><g class="still">{''.join(loading_still)}</g>
  {''.join(ET.tostring(image, encoding='unicode') for image in images)}
  {''.join(markup)}
</svg>
'''
ET.fromstring(svg)
assert svg.count("data:image/png;base64,") == 2
assert "<script" not in svg and "@font-face" in svg
(OUT / "profile.svg").write_text(svg)

card_posters = []
for position, (slug, name, handle, url) in enumerate(SOCIALS):
    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    card_draw.rectangle((0, 24, 319, 111), fill=BG)
    card_draw.line((0, 24, 319, 24), fill=RULE)
    card_draw.line((0, 111, 319, 111), fill=RULE)
    card_draw.line((319, 24, 319, 111), fill=RULE)
    if position == 0:
        card_draw.line((0, 24, 0, 111), fill=RULE)
    labels = []
    for value, y, size, color in [(name, 51, 13, MUTED), (handle, 87, 20, LINK if url else INK)]:
        font = ImageFont.truetype(str(FONT), size)
        assert 24 + font.getlength(value) < CARD_WIDTH - 48
        card_draw.text((24, y), value, font=font, fill=color, anchor="ls")
        label = f'<text x="24" y="{y}" font-size="{size}" fill="{color}">{escape(value)}</text>'
        if url and value == handle:
            arrow_x = 24 + font.getlength(value) + 14
            card_draw.line((arrow_x, 86, arrow_x + 12, 74), fill=color, width=2)
            card_draw.line((arrow_x + 3, 74, arrow_x + 12, 74, arrow_x + 12, 83), fill=color, width=2)
            label = f'<a href="{url}">{label}<path d="M{arrow_x} 86l12-12m-9 0h9v9" fill="none" stroke="{color}" stroke-width="1.5"/></a>'
        labels.append(label)
    card_posters.append(card)
    card_svg = f'''<svg xmlns="{namespace}" width="320" height="120" viewBox="0 0 320 120" role="img" aria-labelledby="title desc">
  <title id="title">{name} — {handle}</title>
  <desc id="desc">{name}: {handle}{f'. Visit {url}' if url else ''}.</desc>
  <style>
    @font-face {{ font-family: CommitMono; src: url(data:font/woff2;base64,{font_data}) format('woff2'); font-weight: 400; }}
    text {{ font-family: CommitMono, monospace; font-weight: 400; }}
  </style>
  <path fill="{BG}" d="M0 24H320V112H0Z"/>
  <path d="M0 24.5H320M0 111.5H320M319.5 24V112{'M.5 24V112' if position == 0 else ''}" fill="none" stroke="{RULE}"/>
  {''.join(labels)}
</svg>
'''
    ET.fromstring(card_svg)
    (OUT / f"{slug}.svg").write_text(card_svg)

full_height = HEIGHT + CONTACT_GAP + CARD_HEIGHT
combined = Image.new("RGB", (WIDTH, full_height), PAGE_BG)
combined.paste(preview)
for position, card in enumerate(card_posters):
    combined.paste(card, (position * CARD_WIDTH, HEIGHT + CONTACT_GAP), card)
preview = combined
glowing_preview = preview.copy()
draw_name_shine(glowing_preview, 3.8)
glowing_preview.save(OUT / "preview.png")
loop_check = preview.copy()
draw_name_shine(loop_check, 8)
assert ImageChops.difference(loop_check, preview).getbbox() is None, "Name shimmer has a loop seam"
assert ImageChops.difference(glowing_preview, preview).getbbox() is not None, "Name shimmer is invisible"
preview.crop((0, HEIGHT + CONTACT_GAP, WIDTH, full_height)).save(OUT / "contacts-preview.png")

frames = []
preview_size = (720, full_height * 3 // 4)
palette = glowing_preview.resize(preview_size, Image.Resampling.LANCZOS).quantize(colors=128)
colors = palette.getpalette()
base_color, peak_color = (185, 203, 210), (244, 255, 255)
# Keep the small white highlight from being lost in GIF palette reduction.
colors[128 * 3:144 * 3] = [round(a + (b - a) * step / 15)
                          for step in range(16) for a, b in zip(base_color, peak_color)]
palette.putpalette(colors)
for index in range(0, animation.n_frames, 2):
    animation.seek(index)
    frame = preview.copy()
    frame.paste(animation.convert("RGB").resize((WIDTH, 360), Image.Resampling.NEAREST), (0, HEADER_HEIGHT))
    draw_header(frame, index / 18)
    draw_name_shine(frame, index / 18)
    frame = frame.resize(preview_size, Image.Resampling.LANCZOS)
    frames.append(frame.quantize(palette=palette, dither=Image.Dither.NONE))
frames[0].save(OUT / "preview.gif", save_all=True, append_images=frames[1:],
               duration=round(2000 / 18), loop=0, optimize=True, disposal=1)
name_frames = [frame.crop((0, NAME_BOX[1] * 3 // 4, 720, NAME_BOX[3] * 3 // 4)) for frame in frames]
name_frames[0].save(OUT / "name-preview.gif", save_all=True, append_images=name_frames[1:],
                    duration=round(2000 / 18), loop=0, optimize=True, disposal=1)
(OUT / "contacts-preview.gif").unlink(missing_ok=True)
with Image.open(OUT / "preview.gif") as check:
    assert check.n_frames == len(frames) and check.info["loop"] == 0
    check.seek(len(frames) - 1)
    check.load()

contact_links = []
for slug, name, handle, url in SOCIALS:
    image = f'<img src="./profile/{slug}.svg" width="33.333%" alt="{name}: {url or handle}">'
    contact_links.append(f'<a href="{url}">{image}</a>' if url else image)
(ROOT / "README.md").write_text(
    f'<p align="center">\n  <img src="./profile/profile.svg" width="100%" '
    f'alt="{escape(description, quote=True)}">\n</p>\n\n'
    f'<p align="center">{"".join(contact_links)}</p>\n'
)
print(f"Built README, {len(svg) / 1024:.0f} KB SVG, and still/animated previews.")
assert len(ET.fromstring(svg).findall(f'.//{{{namespace}}}animate')) == 4, "Loading animation is incomplete"
assert not any(ET.parse(OUT / f'{slug}.svg').getroot().findall(f'{{{namespace}}}image') for slug, *_ in SOCIALS), "Contact logos remain"
print("Checked: embedded fonts, reduced-motion still, text bounds, animation decoding, name shimmer loop, loading indicator, and logo-free links.")
