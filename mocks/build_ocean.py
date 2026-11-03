"""Build three self-contained moonlit beach SVGs and their preview images.

Run: python3 mocks/build_ocean.py (requires NumPy and Pillow).
"""

import base64
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent
W, H, SCALE = 240, 90, 4
FRAMES, FPS = 144, 18
TAU = np.pi * 2
Y, X = np.mgrid[:H, :W].astype(float)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])
THRESHOLD = (np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W] + 0.5) / 16

MOCKS = [
    {
        "slug": "moonwash", "name": "Moonwash",
        "caption": "A full moon, twinkling stars, and softly drifting curls above the rolling tide.",
        "water": ["#050e17", "#091923", "#102a35", "#1b404b", "#365e67", "#698b90", "#a7bebb", "#d3ded5"],
        "sand": ["#24282b", "#383b37", "#505044", "#66614e"],
        "light": 0.76,
        "moon": (0.69, 0.14, 5.5),
    },
    {
        "slug": "ink-tide", "name": "Ink tide",
        "caption": "A small moon, deep blue water, and a quiet stretch of beach.",
        "water": ["#060c16", "#0b1422", "#142235", "#22374a", "#3f556a", "#77899b", "#b3bdc9", "#d7dce0"],
        "sand": ["#232630", "#30323c", "#41414a", "#54515a"],
        "light": 0.56,
        "moon": (0.29, 0.15, 4.5),
    },
    {
        "slug": "silver-edge", "name": "Silver edge",
        "caption": "A low silver moon. A broken trail of light reaching toward the shore.",
        "water": ["#070f15", "#0d1d24", "#173039", "#29464c", "#4d6b6d", "#839e9a", "#b8cac0", "#e0e4d4"],
        "sand": ["#292f2d", "#3b423a", "#505646", "#656952"],
        "light": 0.86,
        "moon": (0.54, 0.19, 6.0),
    },
]


def noise(x, y, seed=0):
    """Smooth, repeatable spatial noise; animation moves through it continuously."""
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def hashed(a, b):
        return np.mod(np.sin(a * 127.1 + b * 311.7 + seed * 19.3) * 43758.5453, 1)

    a, b = hashed(ix, iy), hashed(ix + 1, iy)
    c, d = hashed(ix, iy + 1), hashed(ix + 1, iy + 1)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


HORIZON = 31


def spiral_clouds():
    clouds = np.zeros_like(X)
    for cx, cy, radius, tail in [(77, 11, 4.8, 17), (208, 21, 3.8, 13)]:
        theta = np.linspace(np.pi / 2, np.pi / 2 + TAU * 1.1, 100)
        r = np.linspace(radius, 0.25, len(theta))
        points = list(zip(cx + np.cos(theta) * r * 1.25, cy + np.sin(theta) * r * 0.75))
        points += [(cx - tail * t, cy + radius * 0.75 - np.sin(t * np.pi) * 0.45)
                   for t in np.linspace(0, 1, 70)]
        distance = np.full_like(X, np.inf)
        for px, py in points:
            distance = np.minimum(distance, np.hypot(X - px, Y - py))
        clouds = np.maximum(clouds, np.exp(-(distance / 0.8) ** 2))
    return clouds


CURLS = Image.fromarray(spiral_clouds().astype(np.float32))


def shoreline(index):
    slope = [0.045, -0.015, 0.02][index]
    return H * (0.88 + slope * (X / W - 0.5)) + 0.65 * np.sin(X / 29)


def quantize(tone, count):
    value = np.clip(tone, 0, 1) * (count - 1)
    return np.minimum(count - 1, np.floor(value) + ((value % 1) > THRESHOLD)).astype(np.uint8)


def render(index, time):
    settings = MOCKS[index]
    shore = shoreline(index)
    ocean_height = shore - HORIZON
    depth = np.clip((Y - HORIZON) / ocean_height, 0, 1.2)
    angle = TAU * (time % 1)
    st, ct = np.sin(angle), np.cos(angle)
    warp = noise(X / 24 + ct * 0.24, Y / 12 + st * 0.24, 3) - 0.5
    grain = noise(X / 1.6, Y / 1.4, 8)
    fine = noise(X / 3.4 + ct * 0.6, Y / 2.1 + st * 0.6, 12)
    lace = noise(X / 1.2 + ct * 0.5, Y / 1.1 + st * 0.5, 7)
    holes = np.clip((lace * 0.6 + fine * 0.4 - 0.3) * 2.5, 0, 1)

    # Perspective packs distant waves together; increasing phase brings them closer.
    distance = 3 * (1 / (depth + 0.22) - 1 / 1.22)
    phase = distance + 2 * time + warp * 0.23 + np.sin(X / 19 + angle) * depth * 0.03
    derivative = 3 / ((depth + 0.22) ** 2 * ocean_height)
    crest_distance = ((phase + 0.5) % 1 - 0.5) / derivative
    crest = np.exp(-((crest_distance + (fine - 0.5) * depth) / (0.22 + depth * 0.65)) ** 2)
    wake = np.exp(-np.maximum(crest_distance, 0) / (0.5 + depth * 2.0)) * (crest_distance > 0)
    breaker_zone = np.clip((depth - 0.3) / 0.7, 0, 1) ** 1.5
    foam = (crest * (0.5 + fine * 0.5) + wake * holes * 0.48) * breaker_zone

    runup = 1.2 + 1.8 * np.sin(2 * angle + X / 47) + warp * 1.1
    edge_distance = shore + runup - Y
    water_mask = edge_distance >= 0
    shore_foam = np.exp(-(edge_distance / 0.75) ** 2) * (0.45 + holes * 0.55)
    foam = np.maximum(foam, shore_foam * 0.85)

    mx, my, radius = settings["moon"]
    mx, my = mx * W, my * H
    reflection_center = mx + np.sin(depth * 8 + angle) * (0.4 + depth * 2.2)
    beam = np.exp(-((X - reflection_center) / (1.8 + depth * 14)) ** 2)
    facets = np.sin(distance * TAU * 2 + angle * 4 + warp * 8 + X * 0.17) * 0.5 + 0.5
    shimmer = beam * np.clip((facets + grain * 0.38 - 0.66) * 2.2, 0, 1)
    drift = noise(X / 18 + ct * 0.2, Y / 7 + st * 0.2, 21)
    tone = 0.085 + drift * 0.105 + depth * 0.035
    tone += shimmer * (0.48 + depth * 0.12) + foam * settings["light"]
    water = quantize(tone, 8)

    sand_tone = 0.40 + grain * 0.23 + noise(X / 12, Y / 8, 51) * 0.1
    sand_tone -= np.exp(-np.maximum(Y - shore, 0) / 2.8) * 0.3
    sand = 8 + quantize(sand_tone, 4)
    pixels = np.where(water_mask, water, sand).astype(np.uint8)

    moon_distance = np.hypot(X - mx, Y - my)
    halo = np.exp(-(moon_distance / (radius * 2.8)) ** 2)
    clouds = noise(X / 29, Y / 2.4, 81) * noise(X / 50, Y / 7, 82)
    sky_tone = 0.01 + halo * 0.11 + clouds * 0.035
    if index == 0:
        moving_clouds = CURLS.transform((W, H), Image.Transform.AFFINE,
                                       (1, 0, -4 * st, 0, 1, -0.6 * (1 - ct)),
                                       Image.Resampling.BILINEAR)
        sky_tone += np.asarray(moving_clouds) * 0.44
    sky = quantize(sky_tone, 8)
    pixels = np.where(Y < HORIZON, sky, pixels)
    for sx, sy in [(16, 8), (39, 18), (62, 6), (91, 21), (115, 10), (145, 5), (189, 23), (213, 12), (226, 4)]:
        if np.hypot(sx - mx, sy - my) > radius * 2.5:
            if index == 0:
                shine = (np.sin(angle * (1 + sx % 2) + sx * 0.73) + 1) / 2
                pixels[sy, sx] = 3 + int(shine * 3)
                if shine > 0.75 and sx in (39, 115, 213):
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        pixels[sy + dy, sx + dx] = max(pixels[sy + dy, sx + dx], 3)
            else:
                pixels[sy, sx] = 3 if sx % 2 else 4
    moon = moon_distance <= radius
    craters = np.exp(-((X - mx + 1.7) ** 2 + (Y - my + 1.2) ** 2) / 3)
    craters += np.exp(-((X - mx - 1.8) ** 2 + (Y - my - 1.5) ** 2) / 1.8) * 0.6
    moon_tone = 0.99 - craters * 0.18 - np.clip((X - mx) / radius, 0, 1) * 0.05
    pixels = np.where(moon, quantize(moon_tone, 8), pixels).astype(np.uint8)
    return pixels


def indexed(pixels, settings):
    colors = settings["water"] + settings["sand"]
    palette = [int(color[i:i + 2], 16) for color in colors for i in (1, 3, 5)]
    image = Image.fromarray(pixels).convert("P")
    image.putpalette(palette + [0] * (768 - len(palette)))
    return image


def png_bytes(image):
    stream = BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def build(index):
    settings = MOCKS[index]
    frames = [indexed(render(index, t / FRAMES), settings) for t in range(FRAMES)]
    stream = BytesIO()
    frames[0].save(stream, format="PNG", save_all=True, append_images=frames[1:],
                   duration=1000 / FPS, loop=0, disposal=0, blend=0, optimize=True)
    animation = stream.getvalue()
    still = png_bytes(frames[0])
    encode = lambda content: base64.b64encode(content).decode("ascii")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" viewBox="0 0 960 360" role="img" aria-labelledby="title desc">
  <title id="title">{settings['name']} — dithered night ocean</title>
  <desc id="desc">{settings['caption']} Seen from the beach, looking out to the horizon. Waves roll toward the viewer in an eight-second loop.</desc>
  <style>
    image {{ image-rendering: pixelated; }}
    .still {{ display: none; }}
    @media (prefers-reduced-motion: reduce) {{ .motion {{ display: none; }} .still {{ display: inline; }} }}
  </style>
  <image class="motion" width="960" height="360" href="data:image/png;base64,{encode(animation)}"/>
  <image class="still" width="960" height="360" href="data:image/png;base64,{encode(still)}"/>
</svg>
'''
    target = OUT / settings["slug"]
    target.with_suffix(".svg").write_text(svg)
    preview = frames[0].convert("RGB").resize((960, 360), Image.Resampling.NEAREST)
    preview.save(target.with_suffix(".png"))
    gif_frames = [frame.resize((720, 270), Image.Resampling.NEAREST) for frame in frames[::2]]
    gif_frames[0].save(target.with_suffix(".gif"), save_all=True, append_images=gif_frames[1:],
                       duration=round(2000 / FPS), loop=0, optimize=True, disposal=1)

    # Check the actual artifact, including animation metadata and the loop boundary.
    root = ET.fromstring(svg)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert np.array_equal(render(index, 0), render(index, 1)), "loop has a seam"
    assert np.mean(render(index, 0) != render(index, 0.25)) > 0.05, "waves are not moving"
    assert 0.03 < np.mean(Y > shoreline(index)) < 0.2, "too much beach in the crop"
    sky_changes = np.count_nonzero(render(index, 0)[:HORIZON] != render(index, 0.25)[:HORIZON])
    if index == 0:
        assert 30 < sky_changes < 400, "sky motion should stay subtle"
        assert np.count_nonzero(render(index, 0)[5:17, 50:90] != render(index, 0.25)[5:17, 50:90]) > 20, "clouds should drift"
        assert 0 < np.mean(np.asarray(CURLS)[:HORIZON] > 0.1) < 0.06, "clouds should stay small"
    else:
        assert sky_changes == 0, "sky should stay still"
    mx, my, _ = settings["moon"]
    assert render(index, 0)[round(my * H), round(mx * W)] >= 6, "moon is not visible"
    with Image.open(BytesIO(animation)) as check:
        assert check.n_frames == FRAMES and check.info["loop"] == 0
        check.seek(FRAMES - 1)
        check.load()
    print(f"{settings['slug']}: {len(svg) / 1024:.0f} KB, {FRAMES} frames, loop checked")
    return preview


def comparison(previews):
    sheet = Image.new("RGB", (1024, 1374), "#080f16")
    draw = ImageDraw.Draw(sheet)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        title = ImageFont.truetype(font_path, 24)
        body = ImageFont.truetype(font_path, 15)
    except OSError:
        title = ImageFont.load_default(size=24)
        body = ImageFont.load_default(size=15)
    for i, (settings, preview) in enumerate(zip(MOCKS, previews)):
        y = 24 + i * 450
        draw.text((32, y), settings["name"], font=title, fill="#d5e1e3")
        draw.text((32, y + 36), settings["caption"], font=body, fill="#8a9da6")
        sheet.paste(preview, (32, y + 68))
    sheet.save(OUT / "comparison.png")


if __name__ == "__main__":
    comparison([build(index) for index in range(len(MOCKS))])
