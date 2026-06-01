#!/usr/bin/env python3
import math
import os
import sys
import shutil
from PIL import Image, ImageDraw, ImageFont

# Dimension constants
VIEWPORT_SIZE = 900
SCALE = 3
CANVAS_SIZE = VIEWPORT_SIZE * SCALE

# Main layout constants (for 900x900 viewport, multiply by SCALE for Pillow)
CX = 450
CY = 510
R = 200
R_DRAW = 250
R_DAY_LABEL = 145  # Deeper inside the R=200 track to avoid overlap

# Color palette (Hex for SVG, RGBA for Pillow)
COLOR_BG_HEX = "#FFFFFF"
COLOR_BG_RGBA = (255, 255, 255, 255)

COLOR_TRACK_HEX = "#2C3E50"
COLOR_TRACK_RGBA = (44, 62, 80, 255)

COLOR_ARROW_HEX = "#FFFFFF"
COLOR_ARROW_RGBA = (255, 255, 255, 255)

COLOR_TICK_HEX = "#FFFFFF"
COLOR_TICK_RGBA = (255, 255, 255, 255)

COLOR_TEXT_MAIN_HEX = "#2C3E50"
COLOR_TEXT_MAIN_RGBA = (44, 62, 80, 255)

# Premium deep terracotta/burnt-rust for a highly professional textbook aesthetic
COLOR_TEXT_HIGHLIGHT_HEX = "#7E3517"
COLOR_TEXT_HIGHLIGHT_RGBA = (126, 53, 23, 255)

COLOR_TEXT_MUTED_HEX = "#7F8C8D"
COLOR_TEXT_MUTED_RGBA = (127, 140, 141, 255)


# --- FONT LOADING HELPER ---
def load_font(font_name, size, bold=False):
    names = []
    if bold:
        names = [
            f"{font_name}-Bold",
            f"{font_name}Bold",
            f"{font_name}_Bold",
            "Helvetica-Bold",
            "Arial-Bold",
            "Arial Bold",
        ]
    else:
        names = [
            font_name,
            "Helvetica",
            "Arial",
        ]

    font_paths = []
    for name in names:
        font_paths.extend(
            [
                f"/System/Library/Fonts/Supplemental/{name}.ttf",
                f"/System/Library/Fonts/{name}.ttc",
                f"/System/Library/Fonts/{name}.ttf",
                f"/Library/Fonts/{name}.ttf",
            ]
        )

    # Fallbacks on macOS
    if bold:
        font_paths.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        )
    else:
        font_paths.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        )

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            continue

    return ImageFont.load_default()


# --- PIL RENDERING HELPERS ---


def draw_styled_multiline_text_pillow(draw, lines_with_styles, x, y, align="center", line_spacing=1.25):
    total_height = 0
    line_heights = []

    for text, color, font in lines_with_styles:
        bbox = font.getbbox(text if text else "Tg")
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_height += h * line_spacing

    if line_heights:
        total_height -= line_heights[-1] * (line_spacing - 1)

    start_y = y - total_height / 2 if align == "center" else y

    curr_y = start_y
    for i, (text, color, font) in enumerate(lines_with_styles):
        line_bbox = font.getbbox(text)
        line_width = line_bbox[2] - line_bbox[0]

        if align == "center":
            line_x = x - line_width / 2
        elif align == "right":
            line_x = x - line_width
        else:
            line_x = x

        draw.text((int(line_x), int(curr_y)), text, fill=color, font=font)
        curr_y += line_heights[i] * line_spacing


def draw_arrowhead_pillow(draw, cx, cy, R_val, angle_deg, size=16, fill=(255, 255, 255, 255)):
    rad = math.radians(angle_deg)
    ax = cx + R_val * math.cos(rad)
    ay = cy + R_val * math.sin(rad)

    rot_rad = math.radians(angle_deg + 90)

    local_pts = [(0, -size * 0.7), (-size * 0.45, size * 0.4), (size * 0.45, size * 0.4)]

    global_pts = []
    cos_val = math.cos(rot_rad)
    sin_val = math.sin(rot_rad)
    for px, py in local_pts:
        rx = ax + cos_val * px - sin_val * py
        ry = ay + sin_val * px + cos_val * py
        global_pts.append((int(rx), int(ry)))

    draw.polygon(global_pts, fill=fill)


def draw_louse_pillow(cx, cy, size, angle_deg, is_adult=False):
    temp_w = int(size * 2)
    temp_h = int(size * 2)
    temp_img = Image.new("RGBA", (temp_w, temp_h), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)

    lx = temp_w / 2
    ly = temp_h / 2
    s = size / 100.0

    if is_adult:
        head_fill = (211, 84, 0, 255)
        head_outline = (120, 40, 0, 255)
        thorax_fill = (220, 118, 51, 255)
        thorax_outline = (120, 40, 0, 255)
        ab_fill = (253, 235, 208, 255)
        ab_outline = (120, 40, 0, 255)
        stripe_color = (93, 64, 55, 255)
        leg_color = (229, 152, 102, 255)
    else:
        head_fill = (249, 231, 159, 255)
        head_outline = (180, 140, 70, 255)
        thorax_fill = (253, 242, 233, 255)
        thorax_outline = (180, 140, 70, 255)
        ab_fill = (253, 254, 254, 255)
        ab_outline = (200, 200, 200, 255)
        stripe_color = (245, 203, 167, 255)
        leg_color = (250, 215, 160, 255)

    leg_w = max(1, int(3 * s))
    temp_draw.line(
        [int(lx - 8 * s), int(ly - 20 * s), int(lx - 22 * s), int(ly - 30 * s), int(lx - 25 * s), int(ly - 26 * s)],
        fill=leg_color,
        width=leg_w,
        joint="round",
    )
    temp_draw.line(
        [int(lx + 8 * s), int(ly - 20 * s), int(lx + 22 * s), int(ly - 30 * s), int(lx + 25 * s), int(ly - 26 * s)],
        fill=leg_color,
        width=leg_w,
        joint="round",
    )

    temp_draw.line(
        [int(lx - 10 * s), int(ly - 12 * s), int(lx - 25 * s), int(ly - 12 * s), int(lx - 27 * s), int(ly - 8 * s)],
        fill=leg_color,
        width=leg_w,
        joint="round",
    )
    temp_draw.line(
        [int(lx + 10 * s), int(ly - 12 * s), int(lx + 25 * s), int(ly - 12 * s), int(lx + 27 * s), int(ly - 8 * s)],
        fill=leg_color,
        width=leg_w,
        joint="round",
    )

    temp_draw.line(
        [int(lx - 8 * s), int(ly - 4 * s), int(lx - 24 * s), int(ly + 4 * s), int(lx - 22 * s), int(ly + 9 * s)],
        fill=leg_color,
        width=leg_w,
        joint="round",
    )
    temp_draw.line(
        [int(lx + 8 * s), int(ly - 4 * s), int(lx + 24 * s), int(ly + 4 * s), int(lx + 22 * s), int(ly + 9 * s)],
        fill=leg_color,
        width=leg_w,
        joint="round",
    )

    outline_w = max(1, int(2 * s))
    temp_draw.ellipse(
        [int(lx - 22 * s), int(ly - 15 * s), int(lx + 22 * s), int(ly + 45 * s)],
        fill=ab_fill,
        outline=ab_outline,
        width=outline_w,
    )

    stripe_w = max(1, int(3 * s))
    for dy in [-5, 5, 15, 25, 35]:
        w_factor = math.sqrt(1 - ((dy - 15) / 30) ** 2) if abs(dy - 15) < 30 else 0.5
        line_w = 20 * s * w_factor * 0.95
        temp_draw.line(
            [int(lx - line_w), int(ly + dy * s), int(lx + line_w), int(ly + dy * s)], fill=stripe_color, width=stripe_w
        )

    temp_draw.ellipse(
        [int(lx - 12 * s), int(ly - 25 * s), int(lx + 12 * s), int(ly - 13 * s)],
        fill=thorax_fill,
        outline=thorax_outline,
        width=outline_w,
    )
    temp_draw.ellipse(
        [int(lx - 18 * s), int(ly - 42 * s), int(lx + 18 * s), int(ly - 23 * s)],
        fill=head_fill,
        outline=head_outline,
        width=outline_w,
    )

    ant_w = max(1, int(2.5 * s))
    temp_draw.line(
        [int(lx - 14 * s), int(ly - 33 * s), int(lx - 22 * s), int(ly - 41 * s), int(lx - 20 * s), int(ly - 44 * s)],
        fill=head_outline,
        width=ant_w,
        joint="round",
    )
    temp_draw.line(
        [int(lx + 14 * s), int(ly - 33 * s), int(lx + 22 * s), int(ly - 41 * s), int(lx + 20 * s), int(ly - 44 * s)],
        fill=head_outline,
        width=ant_w,
        joint="round",
    )

    eye_r = max(1, int(1.5 * s))
    temp_draw.ellipse(
        [
            int(lx - 14.5 * s - eye_r),
            int(ly - 32.5 * s - eye_r),
            int(lx - 14.5 * s + eye_r),
            int(ly - 32.5 * s + eye_r),
        ],
        fill=(0, 0, 0, 255),
    )
    temp_draw.ellipse(
        [
            int(lx + 14.5 * s - eye_r),
            int(ly - 32.5 * s - eye_r),
            int(lx + 14.5 * s + eye_r),
            int(ly - 32.5 * s + eye_r),
        ],
        fill=(0, 0, 0, 255),
    )

    rot_angle = 270 - angle_deg
    rotated_img = temp_img.rotate(rot_angle, resample=Image.Resampling.BICUBIC, expand=True)

    rx = int(cx - rotated_img.width // 2)
    ry = int(cy - rotated_img.height // 2)
    return rotated_img, rx, ry


def draw_egg_pillow(cx, cy, size, angle_deg, hatched=False):
    temp_w = int(size * 2)
    temp_h = int(size * 2)
    temp_img = Image.new("RGBA", (temp_w, temp_h), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)

    lx = temp_w / 2
    ly = temp_h / 2
    s = size / 50.0

    fiber_color = (139, 110, 80, 255)
    fiber_w = max(1, int(4 * s))
    temp_draw.line(
        [int(lx - 40 * s), int(ly + 40 * s), int(lx + 40 * s), int(ly - 40 * s)], fill=fiber_color, width=fiber_w
    )

    cement_color = (189, 195, 199, 180)
    temp_draw.ellipse([int(lx - 10 * s), int(ly - 6 * s), int(lx + 2 * s), int(ly + 6 * s)], fill=cement_color)

    egg_fill = (253, 254, 254, 255)
    egg_outline = (189, 195, 199, 255)
    outline_w = max(1, int(2 * s))

    if not hatched:
        temp_draw.ellipse(
            [int(lx - 11 * s), int(ly - 22 * s), int(lx + 11 * s), int(ly + 22 * s)],
            fill=egg_fill,
            outline=egg_outline,
            width=outline_w,
        )
    else:
        points = []
        for angle in range(180, 360 + 1, 10):
            rad = math.radians(angle)
            px = lx + 11 * s * math.cos(rad)
            py = ly + 22 * s * math.sin(rad)
            points.append((int(px), int(py)))
        points.append((int(lx + 11 * s), int(ly - 5 * s)))
        points.append((int(lx - 11 * s), int(ly - 5 * s)))
        temp_draw.polygon(points, fill=egg_fill, outline=egg_outline)

        cap_img = Image.new("RGBA", (int(30 * s), int(20 * s)), (0, 0, 0, 0))
        cap_draw = ImageDraw.Draw(cap_img)
        cap_draw.ellipse(
            [int(2 * s), int(4 * s), int(18 * s), int(10 * s)], fill=egg_fill, outline=egg_outline, width=outline_w
        )
        rotated_cap = cap_img.rotate(35, expand=True)
        temp_img.alpha_composite(rotated_cap, (int(lx - 24 * s), int(ly - 22 * s)))

        temp_draw.ellipse(
            [int(lx - 5 * s), int(ly - 12 * s), int(lx + 5 * s), int(ly - 4 * s)],
            fill=(249, 231, 159, 255),
            outline=(180, 140, 70, 255),
            width=max(1, int(1 * s)),
        )
        temp_draw.line(
            [int(lx - 3 * s), int(ly - 12 * s), int(lx - 7 * s), int(ly - 18 * s)],
            fill=(180, 140, 70, 255),
            width=max(1, int(1.5 * s)),
        )
        temp_draw.line(
            [int(lx + 3 * s), int(ly - 12 * s), int(lx + 7 * s), int(ly - 18 * s)],
            fill=(180, 140, 70, 255),
            width=max(1, int(1.5 * s)),
        )

    rot_angle = 270 - angle_deg
    rotated_img = temp_img.rotate(rot_angle, resample=Image.Resampling.BICUBIC, expand=True)

    rx = int(cx - rotated_img.width // 2)
    ry = int(cy - rotated_img.height // 2)
    return rotated_img, rx, ry


# --- SVG RENDERING HELPERS ---


def svg_styled_text(x, y, lines, align="middle"):
    total_h = 0
    line_spacing = 1.3
    for i, line in enumerate(lines):
        text, color, size, weight, style = line
        total_h += size * line_spacing
    total_h -= lines[-1][2] * (line_spacing - 1)

    start_y = y - total_h / 2 + lines[0][2] * 0.7

    s = f'<text x="{x}" y="{start_y}" text-anchor="{align}" font-family="Arial, Helvetica, sans-serif">\n'
    for i, line in enumerate(lines):
        text, color, size, weight, style = line
        dy = 0 if i == 0 else size * line_spacing
        weight_attr = f' font-weight="{weight}"' if weight else ""
        style_attr = f' font-style="{style}"' if style else ""
        x_attr = f' x="{x}"' if i > 0 else ""
        s += f'  <tspan{x_attr} dy="{dy}" font-size="{size}" fill="{color}"{weight_attr}{style_attr}>{text}</tspan>\n'
    s += "</text>\n"
    return s


def svg_louse(cx, cy, size, angle_deg, is_adult=False):
    s = size / 100.0
    rot_angle = angle_deg - 270

    if is_adult:
        head_fill = "#D35400"
        head_outline = "#782800"
        thorax_fill = "#DC7633"
        thorax_outline = "#782800"
        ab_fill = "#FDEBD0"
        ab_outline = "#782800"
        stripe_color = "#5D4037"
        leg_color = "#E59866"
    else:
        head_fill = "#F9E79F"
        head_outline = "#B48C46"
        thorax_fill = "#FDF2E9"
        thorax_outline = "#B48C46"
        ab_fill = "#FDFEFE"
        ab_outline = "#C8C8C8"
        stripe_color = "#F5CBA7"
        leg_color = "#FAD7A0"

    g = f'<g transform="translate({cx:.3f}, {cy:.3f}) rotate({rot_angle:.2f}) scale({s:.3f})">\n'

    # Legs
    g += f'  <path d="M {-8} {-20} L {-22} {-30} L {-25} {-26}" fill="none" stroke="{leg_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>\n'
    g += f'  <path d="M {8} {-20} L {22} {-30} L {25} {-26}" fill="none" stroke="{leg_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>\n'
    g += f'  <path d="M {-10} {-12} L {-25} {-12} L {-27} {-8}" fill="none" stroke="{leg_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>\n'
    g += f'  <path d="M {10} {-12} L {25} {-12} L {27} {-8}" fill="none" stroke="{leg_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>\n'
    g += f'  <path d="M {-8} {-4} L {-24} {4} L {-22} {9}" fill="none" stroke="{leg_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>\n'
    g += f'  <path d="M {8} {-4} L {24} {4} L {22} {9}" fill="none" stroke="{leg_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>\n'

    # Abdomen
    g += f'  <ellipse cx="0" cy="15" rx="22" ry="30" fill="{ab_fill}" stroke="{ab_outline}" stroke-width="2"/>\n'

    # Stripes
    for dy in [-5, 5, 15, 25, 35]:
        w_factor = math.sqrt(1 - ((dy - 15) / 30) ** 2) if abs(dy - 15) < 30 else 0.5
        stripe_w = 20 * w_factor * 0.95
        g += f'  <line x1="{-stripe_w}" y1="{dy}" x2="{stripe_w}" y2="{dy}" stroke="{stripe_color}" stroke-width="3" stroke-linecap="round"/>\n'

    # Thorax
    g += (
        f'  <ellipse cx="0" cy="-19" rx="12" ry="6" fill="{thorax_fill}" stroke="{thorax_outline}" stroke-width="2"/>\n'
    )

    # Head
    g += (
        f'  <ellipse cx="0" cy="-32.5" rx="18" ry="9.5" fill="{head_fill}" stroke="{head_outline}" stroke-width="2"/>\n'
    )

    # Antennae
    g += f'  <path d="M {-14} {-33} L {-22} {-41} L {-20} {-44}" fill="none" stroke="{head_outline}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>\n'
    g += f'  <path d="M {14} {-33} L {22} {-41} L {20} {-44}" fill="none" stroke="{head_outline}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>\n'

    # Eyes
    g += f'  <circle cx="-14.5" cy="-32.5" r="1.5" fill="#000000"/>\n'
    g += f'  <circle cx="14.5" cy="-32.5" r="1.5" fill="#000000"/>\n'

    g += "</g>\n"
    return g


def svg_egg(cx, cy, size, angle_deg, hatched=False):
    s = size / 50.0
    rot_angle = angle_deg - 270

    g = f'<g transform="translate({cx:.3f}, {cy:.3f}) rotate({rot_angle:.2f}) scale({s:.3f})">\n'

    # Wool fiber
    g += f'  <line x1="{-40}" y1="{40}" x2="{40}" y2="{-40}" stroke="#8B6E50" stroke-width="4" stroke-linecap="round"/>\n'

    # Glue/cement
    g += f'  <ellipse cx="{-4}" cy="{0}" rx="6" ry="6" fill="#BDC3C7" opacity="0.7"/>\n'

    egg_fill = "#FDFEFE"
    egg_outline = "#BDC3C7"

    if not hatched:
        g += f'  <ellipse cx="0" cy="0" rx="11" ry="22" fill="{egg_fill}" stroke="{egg_outline}" stroke-width="2"/>\n'
    else:
        g += f'  <path d="M {-11} {-5} A 11 22 0 1 0 11 -5 Z" fill="{egg_fill}" stroke="{egg_outline}" stroke-width="2"/>\n'
        g += f'  <g transform="translate(-12, -14) rotate(-35)">\n'
        g += f'    <ellipse cx="0" cy="0" rx="11" ry="5" fill="{egg_fill}" stroke="{egg_outline}" stroke-width="2"/>\n'
        g += f"  </g>\n"

        # Emerging tiny nymph
        g += f'  <circle cx="0" cy="-8" r="5" fill="#F9E79F" stroke="#B48C46" stroke-width="1"/>\n'
        g += f'  <line x1="-3" y1="-12" x2="-7" y2="-18" stroke="#B48C46" stroke-width="1.5"/>\n'
        g += f'  <line x1="3" y1="-12" x2="7" y2="-18" stroke="#B48C46" stroke-width="1.5"/>\n'

    g += "</g>\n"
    return g


# --- GENERATOR EXECUTION ---


def main():
    print("Initializing Lifecycle Image Generation...")

    # 1. GENERATE THE HIGH-RES PNG VIA PILLOW (2700 x 2700)
    print("Drawing high-resolution PNG using Pillow...")
    img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), COLOR_BG_RGBA)
    draw = ImageDraw.Draw(img)

    # Load supersampled fonts
    f_title = load_font("Helvetica", 28 * SCALE, bold=True)
    f_subtitle = load_font("Helvetica", 20 * SCALE, bold=False)
    f_label_bold = load_font("Helvetica", 20 * SCALE, bold=True)
    f_label_reg = load_font("Helvetica", 18 * SCALE, bold=False)
    f_center_reg = load_font("Helvetica", 18 * SCALE, bold=False)
    f_center_bold = load_font("Helvetica", 24 * SCALE, bold=True)

    # Draw central circular track
    cx_s, cy_s, r_s = CX * SCALE, CY * SCALE, R * SCALE
    track_w = 24 * SCALE
    draw.ellipse([cx_s - r_s, cy_s - r_s, cx_s + r_s, cy_s + r_s], outline=COLOR_TRACK_RGBA, width=track_w)

    # Draw 35-day daily ticks and progress arrowheads
    special_days = {0: "Day 35 / 0", 9: "Day 9", 17: "Day 17", 22: "Day 22", 31: "Day 31"}

    for i in range(35):
        angle_deg = 180.0 + i * (360.0 / 35.0)
        if i in special_days:
            # Draw beautiful arrowheads inside track pointing clockwise
            draw_arrowhead_pillow(draw, cx_s, cy_s, r_s, angle_deg, size=16 * SCALE, fill=COLOR_ARROW_RGBA)
        else:
            # Draw daily ticks
            rad = math.radians(angle_deg)
            r_inner = r_s - track_w // 2 + 1
            r_outer = r_s + track_w // 2 - 1
            x1 = cx_s + r_inner * math.cos(rad)
            y1 = cy_s + r_inner * math.sin(rad)
            x2 = cx_s + r_outer * math.cos(rad)
            y2 = cy_s + r_outer * math.sin(rad)
            draw.line([int(x1), int(y1), int(x2), int(y2)], fill=COLOR_TICK_RGBA, width=max(1, int(1.5 * SCALE)))

    # Draw local drawings and paste them (15% larger sizes + hugging tighter!)
    # Day 0: Female Louse & Egg
    l_img, lx, ly = draw_louse_pillow(
        cx_s + (R_DRAW * SCALE) * math.cos(math.radians(180)),
        cy_s + (R_DRAW * SCALE) * math.sin(math.radians(180)),
        size=65 * SCALE,
        angle_deg=180,
        is_adult=True,
    )
    img.alpha_composite(l_img, (int(lx), int(ly)))

    # Small laid egg nearby
    egg_img, ex, ey = draw_egg_pillow(
        cx_s + (R_DRAW * SCALE) * math.cos(math.radians(185)),
        cy_s + (R_DRAW * SCALE) * math.sin(math.radians(185)) + 45 * SCALE,
        size=17 * SCALE,
        angle_deg=165,
        hatched=False,
    )
    img.alpha_composite(egg_img, (int(ex), int(ey)))

    # Egg on wool (10:30 position, 225 deg)
    egg_img, ex, ey = draw_egg_pillow(
        cx_s + (R_DRAW * SCALE) * math.cos(math.radians(225)),
        cy_s + (R_DRAW * SCALE) * math.sin(math.radians(225)),
        size=54 * SCALE,
        angle_deg=225,
        hatched=False,
    )
    img.alpha_composite(egg_img, (int(ex), int(ey)))

    # Day 9: Hatching Egg (12:00 position, 272.6 deg)
    hatch_img, hx, hy = draw_egg_pillow(
        cx_s + (R_DRAW * SCALE) * math.cos(math.radians(272.6)),
        cy_s + (R_DRAW * SCALE) * math.sin(math.radians(272.6)),
        size=54 * SCALE,
        angle_deg=272.6,
        hatched=True,
    )
    img.alpha_composite(hatch_img, (int(hx), int(hy)))

    # Day 17: Nymph 1 (2:00 position, 354.9 deg)
    l_img, lx, ly = draw_louse_pillow(
        cx_s + (R_DRAW * SCALE) * math.cos(math.radians(354.9)),
        cy_s + (R_DRAW * SCALE) * math.sin(math.radians(354.9)),
        size=44 * SCALE,
        angle_deg=354.9,
        is_adult=False,
    )
    img.alpha_composite(l_img, (int(lx), int(ly)))

    # Day 22: Nymph 2 (4:30 position, 46.3 deg)
    l_img, lx, ly = draw_louse_pillow(
        cx_s + (R_DRAW * SCALE) * math.cos(math.radians(46.3)),
        cy_s + (R_DRAW * SCALE) * math.sin(math.radians(46.3)),
        size=52 * SCALE,
        angle_deg=46.3,
        is_adult=False,
    )
    img.alpha_composite(l_img, (int(lx), int(ly)))

    # Day 31: Nymph 3 / Young Adult (7:30 position, 138.9 deg)
    l_img, lx, ly = draw_louse_pillow(
        cx_s + (R_DRAW * SCALE) * math.cos(math.radians(138.9)),
        cy_s + (R_DRAW * SCALE) * math.sin(math.radians(138.9)),
        size=60 * SCALE,
        angle_deg=138.9,
        is_adult=False,
    )
    img.alpha_composite(l_img, (int(lx), int(ly)))

    # --- TEXT DRAWING (PILLOW) ---
    # Title & Subtitle (Moved down closer to circle to eliminate top empty area)
    draw_styled_multiline_text_pillow(
        draw,
        [
            ("Lifecycle of the sheep body louse", COLOR_TEXT_MAIN_RGBA, f_title),
            ("Bovicola ovis", COLOR_TEXT_MUTED_RGBA, f_subtitle),
        ],
        CX * SCALE,
        95 * SCALE,
    )

    # Day 0 Female / Eggs text (Your custom coordinate 180*SCALE!)
    draw_styled_multiline_text_pillow(
        draw,
        [
            ("Adult female lays", COLOR_TEXT_MAIN_RGBA, f_label_reg),
            ("1 or 2 eggs", COLOR_TEXT_MAIN_RGBA, f_label_reg),
            ("every 3 days", COLOR_TEXT_MAIN_RGBA, f_label_reg),
        ],
        180 * SCALE,
        430 * SCALE,
    )

    # Egg on wool text
    draw_styled_multiline_text_pillow(
        draw,
        [("Egg attached", COLOR_TEXT_MAIN_RGBA, f_label_reg), ("to wool fiber", COLOR_TEXT_MAIN_RGBA, f_label_reg)],
        200 * SCALE,
        265 * SCALE,
    )

    # Day 9 description (Pushed down cozy against the hatching egg)
    draw_styled_multiline_text_pillow(
        draw, [("Egg hatches", COLOR_TEXT_MAIN_RGBA, f_label_reg)], 450 * SCALE, 185 * SCALE
    )

    # Day 17 description (Your custom coordinate 700*SCALE, 420*SCALE!)
    draw_styled_multiline_text_pillow(
        draw, [("First molt", COLOR_TEXT_MAIN_RGBA, f_label_reg)], 700 * SCALE, 420 * SCALE
    )

    # Day 22 description
    draw_styled_multiline_text_pillow(
        draw, [("Second molt", COLOR_TEXT_MAIN_RGBA, f_label_reg)], 700 * SCALE, 710 * SCALE
    )

    # Day 31 description
    draw_styled_multiline_text_pillow(
        draw,
        [
            ("Third molt:", COLOR_TEXT_MAIN_RGBA, f_label_reg),
            ("Young adult emerges", COLOR_TEXT_MAIN_RGBA, f_label_reg),
        ],
        200 * SCALE,
        710 * SCALE,
    )

    # Molts caption (Your custom coordinate 700*SCALE, pushed down to 615*SCALE to hug the lower-right quadrant)
    draw_styled_multiline_text_pillow(
        draw,
        [
            ("Nymph molts", COLOR_TEXT_MUTED_RGBA, f_label_reg),
            ("three times", COLOR_TEXT_MUTED_RGBA, f_label_reg),
            ("as it grows", COLOR_TEXT_MUTED_RGBA, f_label_reg),
        ],
        700 * SCALE,
        622 * SCALE,
    )

    # --- "DAY X" LABELS INSIDE THE CIRCLE ---
    # Day 35 (at 9 o'clock) - shifted right to 315 to clear track
    draw_styled_multiline_text_pillow(
        draw, [("Day 35", COLOR_TEXT_HIGHLIGHT_RGBA, f_label_bold)], 315 * SCALE, 510 * SCALE
    )

    # Day 9 (at 12 o'clock)
    draw_styled_multiline_text_pillow(
        draw, [("Day 9", COLOR_TEXT_HIGHLIGHT_RGBA, f_label_bold)], 450 * SCALE, 345 * SCALE
    )

    # Day 17 (at 3 o'clock) - shifted left to 585 to clear track
    draw_styled_multiline_text_pillow(
        draw, [("Day 17", COLOR_TEXT_HIGHLIGHT_RGBA, f_label_bold)], 585 * SCALE, 510 * SCALE
    )

    # Day 22 (at bottom-right)
    draw_styled_multiline_text_pillow(
        draw, [("Day 22", COLOR_TEXT_HIGHLIGHT_RGBA, f_label_bold)], 545 * SCALE, 615 * SCALE
    )

    # Day 31 (at bottom-left)
    draw_styled_multiline_text_pillow(
        draw, [("Day 31", COLOR_TEXT_HIGHLIGHT_RGBA, f_label_bold)], 355 * SCALE, 615 * SCALE
    )

    # Center text
    draw_styled_multiline_text_pillow(
        draw,
        [
            ("Females live an", COLOR_TEXT_MAIN_RGBA, f_center_reg),
            ("average of 4 weeks", COLOR_TEXT_MAIN_RGBA, f_center_reg),
        ],
        CX * SCALE,
        460 * SCALE,
    )

    draw_styled_multiline_text_pillow(
        draw,
        [("35 days", COLOR_TEXT_HIGHLIGHT_RGBA, f_center_bold), ("to maturity", COLOR_TEXT_MAIN_RGBA, f_center_reg)],
        CX * SCALE,
        550 * SCALE,
    )

    # Downsample high-resolution canvas to the 900x900 viewport size using LANCZOS
    final_img = img.resize((VIEWPORT_SIZE, VIEWPORT_SIZE), resample=Image.Resampling.LANCZOS)

    # Crop the PNG to the exact content box (100, 60, 800, 740) to match SVG viewBox, removing empty alleys
    final_img = final_img.crop((100, 60, 800, 740))

    # Save the PNG file
    os.makedirs("resources/other", exist_ok=True)
    png_path = "resources/other/bovicola_ovis_lifecycle.png"
    final_img.save(png_path, "PNG")
    print(f"Saved PNG to {png_path}")

    # Also save a copy for the artifact embedding
    artifact_dir = "/Users/snowfire/.gemini/antigravity-cli/brain/f9ebd508-51d1-4111-ab3c-5599c0d1d4c8"
    os.makedirs(artifact_dir, exist_ok=True)
    artifact_png_path = os.path.join(artifact_dir, "bovicola_ovis_lifecycle.png")
    shutil.copy2(png_path, artifact_png_path)
    print(f"Saved artifact copy of PNG to {artifact_png_path}")

    # 2. GENERATE THE SCALABLE VECTOR SVG (Tightly Cropped Viewport)
    print("Generating vector SVG XML with tight crop...")

    svg = f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg += f'<svg width="700" height="680" viewBox="100 60 700 680" xmlns="http://www.w3.org/2000/svg">\n'
    svg += f"  <!-- Background -->\n"
    svg += f'  <rect x="100" y="60" width="700" height="680" fill="{COLOR_BG_HEX}"/>\n\n'

    svg += f"  <!-- Central Circular Track -->\n"
    svg += f'  <circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="{COLOR_TRACK_HEX}" stroke-width="24"/>\n\n'

    svg += f"  <!-- Daily Ticks and Progress Arrows -->\n"
    svg += "  <defs>\n"
    svg += f'    <polygon id="arrow" points="0,-11 -7,6 7,6" fill="{COLOR_ARROW_HEX}"/>\n'
    svg += "  </defs>\n"

    for i in range(35):
        angle_deg = 180.0 + i * (360.0 / 35.0)
        if i in special_days:
            # Position arrowhead on the track pointing clockwise (rotated by angle_deg + 90)
            rad = math.radians(angle_deg)
            ax = CX + R * math.cos(rad)
            ay = CY + R * math.sin(rad)
            rot_deg = angle_deg + 90
            svg += (
                f'  <use href="#arrow" transform="translate({ax:.3f}, {ay:.3f}) rotate({rot_deg:.2f}) scale(1.4)"/>\n'
            )
        else:
            # Position regular daily ticks
            rad = math.radians(angle_deg)
            r_inner = R - 12
            r_outer = R + 12
            x1 = CX + r_inner * math.cos(rad)
            y1 = CY + r_inner * math.sin(rad)
            x2 = CX + r_outer * math.cos(rad)
            y2 = CY + r_outer * math.sin(rad)
            svg += f'  <line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{COLOR_TICK_HEX}" stroke-width="1.5" stroke-linecap="round"/>\n'

    svg += "\n  <!-- Lifecycle Stage Drawings -->\n"
    # Day 0: Female Adult Louse
    cx_draw = CX + R_DRAW * math.cos(math.radians(180))
    cy_draw = CY + R_DRAW * math.sin(math.radians(180))
    svg += f"  <!-- Day 0: Adult Female -->\n"
    svg += svg_louse(cx_draw, cy_draw, size=65, angle_deg=180, is_adult=True)
    # Day 0: Laid Egg
    egg_cx = CX + R_DRAW * math.cos(math.radians(185))
    egg_cy = CY + R_DRAW * math.sin(math.radians(185)) + 45
    svg += svg_egg(egg_cx, egg_cy, size=17, angle_deg=165, hatched=False)

    # Egg on wool (10:30 position, 225 deg)
    cx_draw = CX + R_DRAW * math.cos(math.radians(225))
    cy_draw = CY + R_DRAW * math.sin(math.radians(225))
    svg += f"  <!-- Egg on wool -->\n"
    svg += svg_egg(cx_draw, cy_draw, size=54, angle_deg=225, hatched=False)

    # Day 9: Hatching Egg (12:00 position, 272.6 deg)
    cx_draw = CX + R_DRAW * math.cos(math.radians(272.6))
    cy_draw = CY + R_DRAW * math.sin(math.radians(272.6))
    svg += f"  <!-- Day 9: Hatching Egg -->\n"
    svg += svg_egg(cx_draw, cy_draw, size=54, angle_deg=272.6, hatched=True)

    # Day 17: Nymph 1 (2:00 position, 354.9 deg)
    cx_draw = CX + R_DRAW * math.cos(math.radians(354.9))
    cy_draw = CY + R_DRAW * math.sin(math.radians(354.9))
    svg += f"  <!-- Day 17: Nymph 1 -->\n"
    svg += svg_louse(cx_draw, cy_draw, size=44, angle_deg=354.9, is_adult=False)

    # Day 22: Nymph 2 (4:30 position, 46.3 deg)
    cx_draw = CX + R_DRAW * math.cos(math.radians(46.3))
    cy_draw = CY + R_DRAW * math.sin(math.radians(46.3))
    svg += f"  <!-- Day 22: Nymph 2 -->\n"
    svg += svg_louse(cx_draw, cy_draw, size=52, angle_deg=46.3, is_adult=False)

    # Day 31: Nymph 3 / Young Adult (7:30 position, 138.9 deg)
    cx_draw = CX + R_DRAW * math.cos(math.radians(138.9))
    cy_draw = CY + R_DRAW * math.sin(math.radians(138.9))
    svg += f"  <!-- Day 31: Nymph 3 / Young Adult -->\n"
    svg += svg_louse(cx_draw, cy_draw, size=60, angle_deg=138.9, is_adult=False)

    svg += "\n  <!-- Styled Labels and Captions (Tightly Aligned) -->\n"
    # Title & Subtitle (Moved down closer to circle)
    svg += svg_styled_text(
        CX,
        95,
        [
            ("Lifecycle of the sheep body louse", COLOR_TEXT_MAIN_HEX, 28, "bold", "normal"),
            ("Bovicola ovis", COLOR_TEXT_MUTED_HEX, 20, "normal", "italic"),
        ],
    )

    # Day 0 Female / Eggs text (Mirrored X=180!)
    svg += svg_styled_text(
        180,
        430,
        [
            ("Adult female lays", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
            ("1 or 2 eggs", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
            ("every 3 days", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
        ],
    )

    # Egg on wool text
    svg += svg_styled_text(
        200,
        265,
        [
            ("Egg attached", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
            ("to wool fiber", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
        ],
    )

    # Day 9 description (Brought closer to drawing)
    svg += svg_styled_text(450, 185, [("Egg hatches", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal")])

    # Day 17 description (Mirrored X=700, Y=420!)
    svg += svg_styled_text(700, 420, [("First molt", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal")])

    # Day 22 description
    svg += svg_styled_text(700, 710, [("Second molt", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal")])

    # Day 31 description
    svg += svg_styled_text(
        200,
        710,
        [
            ("Third molt:", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
            ("Young adult emerges", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
        ],
    )

    # Molts caption (Pushed down to Y=622 and tightened to X=700)
    svg += svg_styled_text(
        700,
        622,
        [
            ("Nymph molts", COLOR_TEXT_MUTED_HEX, 18, "normal", "normal"),
            ("three times", COLOR_TEXT_MUTED_HEX, 18, "normal", "normal"),
            ("as it grows", COLOR_TEXT_MUTED_HEX, 18, "normal", "normal"),
        ],
    )

    # --- "DAY X" LABELS INSIDE THE CIRCLE ---
    # Day 35 (at 180 degrees)
    svg += svg_styled_text(315, 510 + 5, [("Day 35", COLOR_TEXT_HIGHLIGHT_HEX, 18, "bold", "normal")])

    # Day 9 (at 272.6 degrees)
    svg += svg_styled_text(450, 345 + 5, [("Day 9", COLOR_TEXT_HIGHLIGHT_HEX, 18, "bold", "normal")])

    # Day 17 (at 354.9 degrees)
    svg += svg_styled_text(585, 510 + 5, [("Day 17", COLOR_TEXT_HIGHLIGHT_HEX, 18, "bold", "normal")])

    # Day 22 (at 46.3 degrees)
    svg += svg_styled_text(545, 615 + 5, [("Day 22", COLOR_TEXT_HIGHLIGHT_HEX, 18, "bold", "normal")])

    # Day 31 (at 138.9 degrees)
    svg += svg_styled_text(355, 615 + 5, [("Day 31", COLOR_TEXT_HIGHLIGHT_HEX, 18, "bold", "normal")])

    # Center text
    svg += svg_styled_text(
        CX,
        460,
        [
            ("Females live an", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
            ("average of 4 weeks", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
        ],
    )

    svg += svg_styled_text(
        CX,
        550,
        [
            ("35 days", COLOR_TEXT_HIGHLIGHT_HEX, 24, "bold", "normal"),
            ("to maturity", COLOR_TEXT_MAIN_HEX, 18, "normal", "normal"),
        ],
    )

    svg += "</svg>\n"

    svg_path = "resources/other/bovicola_ovis_lifecycle.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Saved SVG to {svg_path}")

    print("\nGeneration completed successfully!")


if __name__ == "__main__":
    main()
