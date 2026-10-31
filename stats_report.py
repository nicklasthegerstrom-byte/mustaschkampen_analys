"""
Genererar en snygg PDF per månad med statistik från mustasch_log.
Hoppar över månader som redan har en rapport i rapporter/.
Kör med: python stats_report.py
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import psycopg2.extras
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.image import imread
from collections import defaultdict

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("Sätt DATABASE_URL i .env-filen.")

os.makedirs("rapporter", exist_ok=True)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

cur.execute("""
    SELECT TO_CHAR(created_at, 'YYYY-MM') AS manad, event, COUNT(*) AS antal
    FROM mustasch_log
    WHERE created_at >= '2024-09-30'
    GROUP BY manad, event
    ORDER BY manad
""")
rows = cur.fetchall()

cur.execute("""
    SELECT TO_CHAR(created_at, 'YYYY-MM') AS manad, ROUND(AVG(score)::numeric, 1) AS snitt_score
    FROM mustasch_log
    WHERE created_at >= '2024-09-30'
      AND event = 'analysis'
      AND score IS NOT NULL
    GROUP BY manad
    ORDER BY manad
""")
score_rows = cur.fetchall()
conn.close()

avg_score_by_month = {r["manad"]: float(r["snitt_score"]) for r in score_rows}

by_month_event = defaultdict(lambda: defaultdict(int))
for r in rows:
    by_month_event[r["manad"]][r["event"]] += r["antal"]

months = sorted(by_month_event.keys())

BLUE      = "#1b46b4"
BLUE_DARK = "#1640a0"
BLUE_PALE = "#e8edf8"
AMBER     = "#f5a623"
GREEN     = "#2e9e5b"
RED       = "#cc3333"
GRAY      = "#888888"
LIGHT     = "#f7f8fc"
TEXT      = "#1a1a1a"
TEXT_MUTE = "#666666"

MONTH_NAMES = {
    "01": "Januari", "02": "Februari", "03": "Mars",    "04": "April",
    "05": "Maj",     "06": "Juni",     "07": "Juli",    "08": "Augusti",
    "09": "September","10": "Oktober", "11": "November","12": "December",
}

def score_color(score):
    if score >= 80: return GREEN
    if score >= 50: return AMBER
    return RED

def draw_kpi(ax, value, label, color=BLUE, unit=""):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(mpatches.FancyBboxPatch(
        (0.05, 0.1), 0.9, 0.8,
        boxstyle="round,pad=0.02", linewidth=0,
        facecolor=BLUE_PALE, zorder=0
    ))
    ax.text(0.5, 0.62, f"{value}{unit}", ha="center", va="center",
            fontsize=28, fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.28, label, ha="center", va="center",
            fontsize=9, color=TEXT_MUTE, transform=ax.transAxes)

def draw_donut(ax, pct, label, color):
    size = pct / 100
    wedge_kw = dict(width=0.35, edgecolor="white", linewidth=2)
    ax.pie(
        [size, 1 - size],
        colors=[color, "#e0e4f0"],
        startangle=90,
        counterclock=False,
        wedgeprops=wedge_kw,
    )
    ax.text(0, 0.08, f"{pct}%", ha="center", va="center",
            fontsize=20, fontweight="bold", color=color)
    ax.text(0, -0.22, label, ha="center", va="center",
            fontsize=9, color=TEXT_MUTE)

def draw_score_arc(ax, score, avg_label):
    color = score_color(score)
    size = score / 100
    wedge_kw = dict(width=0.35, edgecolor="white", linewidth=2)
    ax.pie(
        [size, 1 - size],
        colors=[color, "#e0e4f0"],
        startangle=90,
        counterclock=False,
        wedgeprops=wedge_kw,
    )
    ax.text(0, 0.08, f"{score}", ha="center", va="center",
            fontsize=20, fontweight="bold", color=color)
    ax.text(0, -0.22, avg_label, ha="center", va="center",
            fontsize=9, color=TEXT_MUTE)

def draw_event_bars(ax, data):
    labels = ["Analyser", "Swish-klick", "Inget ansikte", "Blockerade", "Fel"]
    values = [
        data.get("analysis", 0),
        data.get("swish_click", 0),
        data.get("no_face", 0),
        data.get("blocked", 0),
        data.get("predict_error", 0) + data.get("upload_error", 0),
    ]
    colors = [BLUE, AMBER, GRAY, RED, RED]
    y = np.arange(len(labels))
    max_v = max(values) or 1

    ax.set_xlim(0, max_v * 1.18)
    ax.set_ylim(-0.5, len(labels) - 0.5)
    ax.axis("off")

    for i, (lbl, val, col) in enumerate(zip(labels, values, colors)):
        bar_w = val / max_v * max_v * 1.0
        ax.barh(i, val, color=col, height=0.5, zorder=2)
        ax.text(-max_v * 0.01, i, lbl, ha="right", va="center",
                fontsize=9, color=TEXT)
        ax.text(val + max_v * 0.02, i, str(val), ha="left", va="center",
                fontsize=9, fontweight="bold", color=col)

    ax.set_facecolor(LIGHT)


generated = []
skipped = []

for m in months:
    output = f"rapporter/mustasch_rapport_{m}.pdf"
    if os.path.exists(output):
        skipped.append(m)
        continue

    d = by_month_event[m]
    analyses  = d.get("analysis", 0)
    swishes   = d.get("swish_click", 0)
    no_face   = d.get("no_face", 0)
    blocked   = d.get("blocked", 0)
    errors    = d.get("predict_error", 0) + d.get("upload_error", 0)
    conv      = round(swishes / analyses * 100, 1) if analyses else 0
    avg_score = avg_score_by_month.get(m, 0)

    year, mon = m.split("-")
    month_label = f"{MONTH_NAMES.get(mon, mon)} {year}"

    with PdfPages(output) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")
        fig.patch.set_facecolor("white")

        # Header
        header = fig.add_axes([0, 0.88, 1, 0.12])
        header.set_facecolor(BLUE)
        header.axis("off")

        # Logga i headern
        logo_path = "assets/images/logo1.png"
        if os.path.exists(logo_path):
            logo_img = imread(logo_path)
            logo_ax = fig.add_axes([0.02, 0.895, 0.18, 0.09])
            logo_ax.imshow(logo_img)
            logo_ax.axis("off")

        header.text(0.26, 0.62, "MUSTASCHKAMPENS MUSTASCHANALYS",
                    color="white", fontsize=12, fontweight="bold",
                    transform=header.transAxes, va="center")
        header.text(0.26, 0.25, f"Månadsrapport — {month_label}",
                    color="#aabbdd", fontsize=9,
                    transform=header.transAxes, va="center")

        gs = gridspec.GridSpec(
            2, 4,
            left=0.04, right=0.97,
            top=0.84, bottom=0.08,
            hspace=0.45, wspace=0.35
        )

        # KPI-rutor rad 1
        ax_a = fig.add_subplot(gs[0, 0])
        draw_kpi(ax_a, analyses, "Analyser gjorda", BLUE)

        ax_s = fig.add_subplot(gs[0, 1])
        draw_kpi(ax_s, swishes, "Swish-klick", AMBER)

        # Donut konvertering
        ax_d = fig.add_subplot(gs[0, 2])
        draw_donut(ax_d, conv, "Konvertering", AMBER)

        # Score-arc
        ax_sc = fig.add_subplot(gs[0, 3])
        draw_score_arc(ax_sc, avg_score, "Medelscore")

        # Event-staplar rad 2 (spänner 3 kolumner)
        ax_bars = fig.add_subplot(gs[1, :3])
        ax_bars.set_facecolor(LIGHT)
        draw_event_bars(ax_bars, d)
        ax_bars.set_title("Händelsefördelning", fontsize=10,
                          color=TEXT_MUTE, loc="left", pad=6)

        # Fotnot
        ax_note = fig.add_subplot(gs[1, 3])
        ax_note.axis("off")
        ax_note.set_facecolor(BLUE_PALE)
        note = (
            f"Rapport: {m}\n"
            f"Källa: mustasch_log\n\n"
            f"Avvisade bilder:\n"
            f"  Inget ansikte  {no_face}\n"
            f"  Blockerade      {blocked}\n\n"
            f"Serverfel:  {errors}"
        )
        ax_note.text(0.08, 0.88, note, transform=ax_note.transAxes,
                     fontsize=8.5, va="top", color=TEXT,
                     fontfamily="monospace",
                     linespacing=1.6)

        pdf.savefig(fig, bbox_inches="tight")
        plt.close()

    generated.append(m)

if generated:
    print(f"Genererade: {', '.join(generated)}")
if skipped:
    print(f"Hoppade över (finns redan): {', '.join(skipped)}")
if not generated and not skipped:
    print("Ingen data hittades.")
