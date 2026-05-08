"""Generate paper-ready enhanced SVG figures for the lunar launch project.

The first-pass figures in ``run_baseline.py`` are intentionally simple.  This
module builds a second figure layer for a competition paper: multi-panel,
self-contained SVGs that combine geometry, numerical anchors, and the decision
logic behind the recommended architecture.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
TRAJECTORIES = ROOT / "results" / "trajectories"
FIGURES = ROOT / "results" / "figures"
PAPER_FIGURES = ROOT / "paper_draft_v0" / "figures"


COLORS = {
    "ink": "#17212b",
    "muted": "#5e6b76",
    "grid": "#d9e1e8",
    "soft": "#f6f8fb",
    "blue": "#2468b4",
    "cyan": "#22a3a8",
    "green": "#2e8b57",
    "orange": "#d9822b",
    "red": "#c84630",
    "purple": "#6f4aa8",
    "gold": "#c9a227",
}


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    PAPER_FIGURES.mkdir(parents=True, exist_ok=True)

    summary = read_json(TABLES / "baseline_summary.json")
    architecture = read_csv(TABLES / "architecture_summary.csv")
    mass_budget = read_csv(TABLES / "tli_mass_budget.csv")
    rendezvous = read_csv(TABLES / "rendezvous_plan.csv")
    reliability = read_csv(TABLES / "reliability_sweep.csv")
    chain = read_csv(TABLES / "mission_chain_reliability.csv")
    sensitivity = read_csv(TABLES / "mission_chain_sensitivity.csv")
    transfer = read_csv(TABLES / "delta_v_budget.csv")
    ascent = read_csv(TRAJECTORIES / "ascent_eci_baseline.csv")

    write_architecture_figure(summary, rendezvous)
    write_trade_matrix_figure(summary, architecture)
    write_mass_sankey_figure(summary)
    write_reliability_chain_figure(summary, reliability, chain, sensitivity)
    write_orbit_figure(summary, rendezvous, transfer)
    write_ascent_dashboard_figure(summary, ascent)

    print(f"Wrote enhanced figures to {FIGURES} and {PAPER_FIGURES}")


def write_architecture_figure(summary: dict[str, object], rendezvous: list[dict[str, str]]) -> None:
    arch = summary["recommended_architecture"]
    chain = summary["mission_chain_reliability_at_launch_095"]
    mass = summary["nominal_tli_mass_budget"]
    tli = summary["tli_estimate_at_300_km"]
    rv = summary["leo_rendezvous_recommended"]

    metrics = [
        ("Cargo split", "20 t + 20 t", "Modular base materials"),
        ("LEO stack", f"{float(mass['initial_leo_stack_t']):.1f} t", "Cargo + docking + TLI stage"),
        ("Rendezvous", f"{float(rv['wait_time_hours']):.1f} h", f"Delta-v {float(rv['total_rendezvous_delta_v_m_s']):.1f} m/s"),
        ("TLI impulse", f"{float(tli['delta_v_tli_km_s']):.3f} km/s", f"TOF {float(tli['time_of_flight_days']):.2f} d"),
        ("Chain reliability", f"{float(chain['two_launch_leo_rendezvous_tli']):.3f}", "R_launch=0.95 baseline"),
    ]

    parts = [
        svg_header(1600, 960),
        title_block(
            800,
            52,
            "Enhanced Fig. 2: Two-Launch Long March 10 LEO Assembly Architecture",
            "Competition-ready architecture graphic: payload split, rendezvous operation, TLI burn, mass budget, and reliability chain.",
        ),
    ]

    # Metric strip.
    card_w = 282
    for idx, (label, value, note) in enumerate(metrics):
        x = 62 + idx * (card_w + 22)
        parts.extend(metric_card(x, 104, card_w, 94, label, value, note, list(COLORS.values())[idx + 5]))

    # Earth, Wenchang, and launches.
    parts.append('<rect x="56" y="244" width="305" height="372" rx="18" class="panel"/>')
    parts.append(text(82, 280, "Launch segment", "section"))
    parts.append(text(82, 305, "Wenchang eastward launch: ~438 m/s gain.", "small"))
    parts.append(earth_icon(208, 448, 104))
    parts.append(text(208, 588, "Wenchang", "label", anchor="middle"))
    parts.append(rocket_icon(91, 346, 0.74, COLORS["blue"], "CZ-10 A"))
    parts.append(rocket_icon(285, 346, 0.74, COLORS["cyan"], "CZ-10 B"))
    parts.append(text(80, 635, "Each launch carries a ~20 t cargo module plus LEO assembly support.", "small"))

    # LEO assembly panel.
    parts.append('<rect x="402" y="244" width="578" height="372" rx="18" class="panel"/>')
    parts.append(text(430, 280, "LEO parking, phasing, and docking", "section"))
    parts.append(text(430, 305, "Target orbit 300 km; example phasing orbit 260 km.", "small"))
    parts.append('<ellipse cx="690" cy="430" rx="222" ry="94" fill="none" stroke="#7e93a4" stroke-width="2.0" stroke-dasharray="8 7"/>')
    parts.append('<ellipse cx="690" cy="430" rx="184" ry="78" fill="none" stroke="#b8c6d0" stroke-width="1.6" stroke-dasharray="5 6"/>')
    parts.append('<circle cx="690" cy="430" r="64" fill="#e8f2ff" stroke="#2468b4" stroke-width="1.5"/>')
    parts.append(text(690, 425, "Earth", "label", anchor="middle"))
    parts.append(text(690, 446, "LEO frame", "small", anchor="middle"))
    parts.append(module_icon(526, 324, COLORS["blue"], "Module A", "target 300 km"))
    parts.append(module_icon(808, 514, COLORS["cyan"], "Module B", "phasing 260 km"))
    parts.append('<circle cx="799" cy="396" r="16" fill="#fff7e8" stroke="#d9822b" stroke-width="3"/>')
    parts.append(text(799, 372, "Dock", "label", anchor="middle"))
    parts.append(curved_arrow(586, 344, 650, 374, 782, 396, COLORS["blue"], 2.4))
    parts.append(curved_arrow(838, 497, 870, 436, 816, 400, COLORS["cyan"], 2.4))
    parts.append('<rect x="445" y="548" width="488" height="42" rx="10" fill="#f6f8fb" stroke="#d9e1e8"/>')
    parts.append(text(462, 573, "R_total = R_L^2 * R_rendezvous * R_TLI = 0.95^2 * 0.98 * 0.985 = 0.871", "mono"))

    # Translunar injection panel.
    parts.append('<rect x="1021" y="244" width="523" height="372" rx="18" class="panel"/>')
    parts.append(text(1049, 280, "Combined translunar injection", "section"))
    parts.append(text(1049, 305, "The docked stack performs one TLI burn after LEO checkout.", "small"))
    parts.append('<circle cx="1126" cy="435" r="54" fill="#e8f2ff" stroke="#2468b4" stroke-width="1.5"/>')
    parts.append('<circle cx="1428" cy="334" r="42" fill="#f3f0e8" stroke="#9a8f7a" stroke-width="1.5"/>')
    parts.append(text(1126, 505, "Earth", "small", anchor="middle"))
    parts.append(text(1428, 393, "Moon", "small", anchor="middle"))
    parts.append('<path d="M 1181 424 C 1260 252, 1356 236, 1402 308" fill="none" stroke="#6f4aa8" stroke-width="3.4" marker-end="url(#arrow-purple)"/>')
    parts.append('<path d="M 1190 450 C 1280 535, 1388 517, 1442 381" fill="none" stroke="#d9e1e8" stroke-width="1.4" stroke-dasharray="7 7"/>')
    parts.append(stack_icon(1082, 374))
    parts.append('<rect x="1228" y="326" width="184" height="78" rx="12" fill="#ffffff" stroke="#d9e1e8"/>')
    parts.append(text(1320, 352, "TLI burn", "label", anchor="middle"))
    parts.append(text(1320, 376, f"Delta-v {float(tli['delta_v_tli_km_s']):.3f} km/s", "small", anchor="middle"))
    parts.append(text(1320, 394, f"Stack {float(mass['initial_leo_stack_t']):.1f} t", "tiny", anchor="middle"))

    # Timeline.
    parts.append('<rect x="56" y="672" width="1488" height="210" rx="18" class="panel"/>')
    parts.append(text(86, 710, "Operational timeline and competition logic", "section"))
    timeline = [
        ("1", "Launch A", "CZ-10 places module A in target LEO"),
        ("2", "Launch B", "module B injected into phasing orbit"),
        ("3", "Phasing", "relative drift closes 40 deg phase angle"),
        ("4", "Docking", "two modules form cargo/TLI stack"),
        ("5", "Checkout", "stack mass and guidance verified"),
        ("6", "TLI", "single combined burn to Earth-Moon transfer"),
        ("7", "Compare", "3-launch case kept as reliability extension"),
    ]
    x0, gap = 112, 205
    for idx, (num, head, note) in enumerate(timeline):
        x = x0 + idx * gap
        color = [COLORS["blue"], COLORS["cyan"], COLORS["orange"], COLORS["green"], COLORS["purple"], COLORS["red"], COLORS["gold"]][idx]
        parts.append(f'<circle cx="{x}" cy="770" r="24" fill="{color}"/>')
        parts.append(text(x, 778, num, "step", anchor="middle"))
        if idx < len(timeline) - 1:
            parts.append(f'<line x1="{x + 32}" y1="770" x2="{x + gap - 32}" y2="770" stroke="#9fb0bf" stroke-width="2.2" marker-end="url(#arrow-muted)"/>')
        parts.append(text(x, 823, head, "label", anchor="middle"))
        parts.append(wrapped_text(x - 74, 846, note, 148, 13, "small"))

    parts.append(svg_footer())
    write_svg(PAPER_FIGURES / "fig2_architecture_enhanced.svg", parts)


def write_trade_matrix_figure(summary: dict[str, object], architecture: list[dict[str, str]]) -> None:
    chain = summary["mission_chain_reliability_at_launch_095"]
    rows = [
        (
            "A. Single direct TLI",
            "Reject",
            "40 t exceeds public 27 t TLI capability",
            1,
            -13.0,
            0.950,
            COLORS["red"],
        ),
        (
            "B. Two-launch LEO assembly",
            "Baseline",
            "Minimum launches; modular 40 t cargo assembled in LEO",
            2,
            7.0,
            float(chain["two_launch_leo_rendezvous_tli"]),
            COLORS["green"],
        ),
        (
            "C. Three-launch 2-of-3",
            "Reliability extension",
            "Higher reliability but extra launch and logistics burden",
            3,
            7.0,
            0.99275,
            COLORS["orange"],
        ),
        (
            "D. Single-body LEO assembly",
            "Backup",
            "Use only if 40 t cargo cannot be split",
            3,
            0.0,
            0.857,
            COLORS["purple"],
        ),
    ]

    parts = [
        svg_header(1500, 900),
        title_block(
            750,
            54,
            "Enhanced Fig. 1: Architecture Trade Matrix",
            "A UPC-style figure should show not only the selected answer but also why competing interpretations were rejected or retained.",
        ),
        '<rect x="54" y="116" width="1392" height="650" rx="18" class="panel"/>',
    ]
    headers = ["Architecture", "Role", "Launches", "Mass margin", "Reliability metric", "Decision reason"]
    xs = [86, 386, 580, 740, 950, 1140]
    for x, head in zip(xs, headers):
        parts.append(text(x, 160, head, "table-head"))
    parts.append('<line x1="82" y1="184" x2="1418" y2="184" stroke="#b9c5cf" stroke-width="1.4"/>')

    for idx, (name, role, reason, launches, margin, rel, color) in enumerate(rows):
        y = 232 + idx * 128
        parts.append(f'<rect x="78" y="{y - 42}" width="1340" height="104" rx="14" fill="#ffffff" stroke="#d9e1e8"/>')
        parts.append(f'<rect x="78" y="{y - 42}" width="8" height="104" rx="4" fill="{color}"/>')
        parts.append(text(102, y - 10, name, "label"))
        parts.append(text(102, y + 18, role, "small"))
        parts.append(status_badge(386, y - 30, role, color))
        for k in range(launches):
            parts.append(rocket_icon(584 + k * 25, y - 29, 0.22, COLORS["muted"], ""))
        margin_color = COLORS["green"] if margin > 0 else COLORS["red"] if margin < 0 else COLORS["orange"]
        parts.append(progress_bar(740, y - 22, 150, 18, max(0.0, min(1.0, (margin + 13.0) / 22.0)), margin_color))
        parts.append(text(748, y + 20, f"{margin:+.1f} t per launch", "small"))
        parts.append(progress_bar(950, y - 22, 150, 18, rel, color))
        parts.append(text(958, y + 20, f"{rel:.3f}", "small"))
        parts.append(wrapped_text(1140, y - 29, reason, 258, 14, "small"))

    parts.append('<rect x="54" y="792" width="1392" height="58" rx="16" fill="#f6f8fb" stroke="#d9e1e8"/>')
    parts.append(text(82, 827, "Decision", "section"))
    parts.append(text(176, 827, "Use the two-launch LEO assembly as the baseline; keep the three-launch case as a sensitivity/reliability extension instead of the main solution.", "body"))
    parts.append(svg_footer())
    write_svg(FIGURES / "architecture_trade_matrix_enhanced.svg", parts)


def write_mass_sankey_figure(summary: dict[str, object]) -> None:
    mass = summary["nominal_tli_mass_budget"]
    cargo = float(mass["delivered_cargo_t"])
    adapter = float(mass["adapter_and_docking_t"])
    prop = float(mass["tli_propellant_t"])
    dry = float(mass["tli_stage_dry_t"])
    stack = float(mass["initial_leo_stack_t"])
    per_launch = float(mass["leo_wet_mass_per_launch_t"])
    margin = float(mass["simulated_margin_per_launch_t"])
    dv = float(mass["tli_delta_v_km_s"])

    scale = 0.92
    parts = [
        svg_header(1500, 900),
        title_block(
            750,
            54,
            "Enhanced Fig. 5: LEO Stack Mass Flow for Combined TLI",
            "Sankey-style mass accounting links the two launch requirement to the TLI rocket equation result.",
        ),
    ]

    parts.append('<rect x="58" y="116" width="1384" height="664" rx="18" class="panel"/>')
    parts.extend(metric_card(92, 142, 250, 92, "Per-launch LEO wet mass", f"{per_launch:.1f} t", f"simulated margin {margin:.1f} t", COLORS["blue"]))
    parts.extend(metric_card(374, 142, 250, 92, "Initial LEO stack", f"{stack:.1f} t", "two launches docked", COLORS["green"]))
    parts.extend(metric_card(656, 142, 250, 92, "TLI propellant", f"{prop:.1f} t", f"Isp 450 s, dv {dv:.3f} km/s", COLORS["orange"]))
    parts.extend(metric_card(938, 142, 250, 92, "Delivered cargo", f"{cargo:.1f} t", "meets problem requirement", COLORS["purple"]))
    parts.extend(metric_card(1220, 142, 178, 92, "Dry/support", f"{dry + adapter:.1f} t", "stage dry + docking", COLORS["cyan"]))

    # Source launch boxes.
    parts.append(mass_node(132, 328, "Launch A", f"{per_launch:.1f} t", COLORS["blue"]))
    parts.append(mass_node(132, 514, "Launch B", f"{per_launch:.1f} t", COLORS["cyan"]))
    parts.append(mass_node(448, 420, "LEO assembly stack", f"{stack:.1f} t", COLORS["green"]))
    parts.append(mass_node(780, 420, "TLI stage + cargo", f"MR={float(mass['mass_ratio']):.3f}", COLORS["purple"]))
    parts.append(mass_node(1115, 310, "Propellant spent", f"{prop:.1f} t", COLORS["orange"]))
    parts.append(mass_node(1115, 444, "Cargo on TLI", f"{cargo:.1f} t", COLORS["purple"]))
    parts.append(mass_node(1115, 578, "Adapter + dry stage", f"{adapter + dry:.1f} t", COLORS["cyan"]))

    parts.append(flow_path(284, 362, 448, 444, per_launch * scale, COLORS["blue"]))
    parts.append(flow_path(284, 548, 448, 454, per_launch * scale, COLORS["cyan"]))
    parts.append(flow_path(604, 450, 780, 450, stack * scale, COLORS["green"]))
    parts.append(flow_path(936, 438, 1115, 344, prop * scale, COLORS["orange"]))
    parts.append(flow_path(936, 454, 1115, 478, cargo * scale, COLORS["purple"]))
    parts.append(flow_path(936, 470, 1115, 612, (adapter + dry) * scale, COLORS["cyan"]))

    parts.append('<rect x="96" y="708" width="1306" height="42" rx="12" fill="#f6f8fb" stroke="#d9e1e8"/>')
    parts.append(text(118, 735, "Interpretation", "label"))
    parts.append(text(236, 735, "The 40 t payload is not a single launch load: two ~48.5 t LEO wet-mass insertions assemble a ~96.9 t TLI stack, of which ~49.0 t is propellant.", "body"))
    parts.append(svg_footer())
    write_svg(FIGURES / "tli_mass_sankey_enhanced.svg", parts)


def write_reliability_chain_figure(
    summary: dict[str, object],
    reliability: list[dict[str, str]],
    chain: list[dict[str, str]],
    sensitivity: list[dict[str, str]],
) -> None:
    base = summary["mission_chain_reliability_at_launch_095"]
    r_launch = float(base["single_launch_reliability"])
    r_rv = float(base["rendezvous_reliability"])
    r_tli = float(base["tli_reliability"])
    r_two = float(base["two_launch_only"])
    r_full = float(base["two_launch_leo_rendezvous_tli"])
    r_three = 3 * r_launch**2 * (1 - r_launch) + r_launch**3

    parts = [
        svg_header(1500, 940),
        title_block(
            750,
            54,
            "Enhanced Fig. 10: Reliability Chain and Sensitivity",
            "The baseline is not only two launches; LEO rendezvous and TLI are explicit serial reliability factors.",
        ),
    ]
    parts.append('<rect x="58" y="116" width="1384" height="336" rx="18" class="panel"/>')
    parts.append(text(92, 154, "Serial mission chain", "section"))
    blocks = [
        ("Launch A", r_launch, COLORS["blue"]),
        ("Launch B", r_launch, COLORS["cyan"]),
        ("LEO rendezvous", r_rv, COLORS["orange"]),
        ("TLI burn", r_tli, COLORS["purple"]),
        ("Mission success", r_full, COLORS["green"]),
    ]
    x0 = 112
    for idx, (name, value, color) in enumerate(blocks):
        x = x0 + idx * 260
        parts.append(f'<rect x="{x}" y="214" width="188" height="108" rx="14" fill="#ffffff" stroke="{color}" stroke-width="2.4"/>')
        parts.append(text(x + 94, 248, name, "label", anchor="middle"))
        parts.append(text(x + 94, 287, f"{value:.3f}", "metric", anchor="middle"))
        if idx < len(blocks) - 1:
            parts.append(f'<line x1="{x + 198}" y1="268" x2="{x + 246}" y2="268" stroke="#9fb0bf" stroke-width="2.4" marker-end="url(#arrow-muted)"/>')
    parts.append('<rect x="180" y="370" width="1140" height="42" rx="12" fill="#f6f8fb" stroke="#d9e1e8"/>')
    parts.append(text(214, 397, f"R = {r_launch:.2f}^2 x {r_rv:.2f} x {r_tli:.3f} = {r_full:.3f}", "mono"))
    parts.append(text(680, 397, f"Launch-only two-CZ10 reliability would be {r_two:.3f}; in-orbit operations reduce it by {r_two - r_full:.3f}.", "body"))

    parts.append('<rect x="58" y="490" width="652" height="330" rx="18" class="panel"/>')
    parts.append(text(92, 528, "Architecture reliability comparison", "section"))
    bars = [
        ("Two launch only", r_two, COLORS["blue"]),
        ("Two launch + LEO/TLI chain", r_full, COLORS["green"]),
        ("Three launch 2-of-3 extension", r_three, COLORS["orange"]),
    ]
    for idx, (name, value, color) in enumerate(bars):
        y = 584 + idx * 72
        parts.append(text(96, y + 5, name, "label"))
        parts.append(progress_bar(338, y - 17, 250, 22, value, color))
        parts.append(text(608, y + 5, f"{value:.3f}", "label"))
    parts.append(wrapped_text(96, 772, "The third launch is useful as a sensitivity option, but the baseline remains the two-launch plan requested by the project decision.", 560, 13, "small"))

    parts.append('<rect x="790" y="490" width="652" height="330" rx="18" class="panel"/>')
    parts.append(text(824, 528, "Rendezvous/TLI operation sensitivity", "section"))
    rv_values = sorted({float(row["rendezvous_reliability"]) for row in sensitivity})
    tli_values = sorted({float(row["tli_reliability"]) for row in sensitivity})
    x_grid, y_grid, cell = 848, 574, 48
    for i, rv in enumerate(rv_values):
        parts.append(text(x_grid + i * cell + 18, y_grid - 16, f"{rv:.3f}", "tiny", anchor="middle"))
    for j, tli in enumerate(tli_values):
        parts.append(text(x_grid - 12, y_grid + j * cell + 29, f"{tli:.3f}", "tiny", anchor="end"))
    values = {(float(row["rendezvous_reliability"]), float(row["tli_reliability"])): float(row["mission_reliability"]) for row in sensitivity}
    vmin, vmax = min(values.values()), max(values.values())
    for i, rv in enumerate(rv_values):
        for j, tli in enumerate(tli_values):
            v = values[(rv, tli)]
            fill = blend(COLORS["red"], COLORS["green"], (v - vmin) / (vmax - vmin))
            x, y = x_grid + i * cell, y_grid + j * cell
            parts.append(f'<rect x="{x}" y="{y}" width="42" height="42" rx="7" fill="{fill}" stroke="#ffffff" stroke-width="1.4"/>')
            parts.append(text(x + 21, y + 27, f"{v:.2f}", "tiny-white", anchor="middle"))
    parts.append(text(1120, 576, "Columns: R_rendezvous", "small"))
    parts.append(text(1120, 604, "Rows: R_TLI", "small"))
    parts.append(text(1120, 650, f"Range: {vmin:.3f} - {vmax:.3f}", "label"))
    parts.append(wrapped_text(1120, 688, "This panel makes clear which in-orbit operations need better evidence in the final paper.", 260, 13, "small"))

    parts.append(svg_footer())
    write_svg(FIGURES / "reliability_chain_enhanced.svg", parts)


def write_orbit_figure(
    summary: dict[str, object],
    rendezvous: list[dict[str, str]],
    transfer: list[dict[str, str]],
) -> None:
    rv = summary["leo_rendezvous_recommended"]
    tli = summary["tli_estimate_at_300_km"]
    parts = [
        svg_header(1500, 900),
        title_block(
            750,
            54,
            "Enhanced Fig. 3/4: LEO Rendezvous and TLI Geometry",
            "A single orbit-mechanics figure links phasing, docking, and the Hohmann-style TLI estimate.",
        ),
    ]
    parts.append('<rect x="58" y="116" width="1008" height="704" rx="18" class="panel"/>')
    parts.append('<rect x="1100" y="116" width="342" height="704" rx="18" class="panel"/>')

    cx, cy = 462, 470
    parts.append('<circle cx="462" cy="470" r="92" fill="#e8f2ff" stroke="#2468b4" stroke-width="2"/>')
    parts.append('<path d="M 392 448 C 420 430, 457 445, 493 421 C 521 402, 550 426, 535 459 C 515 500, 462 502, 433 492 C 401 482, 370 472, 392 448" fill="#b7d7ef" opacity="0.65"/>')
    parts.append(text(cx, cy + 8, "Earth", "label", anchor="middle"))
    parts.append('<circle cx="928" cy="268" r="50" fill="#f3f0e8" stroke="#9a8f7a" stroke-width="1.8"/>')
    parts.append(text(928, 336, "Moon", "label", anchor="middle"))

    # Parking/phasing orbits and TLI arc.
    parts.append('<ellipse cx="462" cy="470" rx="202" ry="88" fill="none" stroke="#2468b4" stroke-width="2.4"/>')
    parts.append('<ellipse cx="462" cy="470" rx="171" ry="74" fill="none" stroke="#22a3a8" stroke-width="2.0" stroke-dasharray="7 7"/>')
    parts.append('<path d="M 658 448 C 736 248, 850 188, 902 244" fill="none" stroke="#6f4aa8" stroke-width="3.4" marker-end="url(#arrow-purple)"/>')
    parts.append('<path d="M 646 494 C 750 620, 900 548, 978 326" fill="none" stroke="#d9e1e8" stroke-width="1.5" stroke-dasharray="8 8"/>')

    parts.append(module_icon(640, 386, COLORS["blue"], "Target", "300 km"))
    parts.append(module_icon(296, 556, COLORS["cyan"], "Phasing", "260 km"))
    parts.append('<circle cx="610" cy="430" r="15" fill="#fff7e8" stroke="#d9822b" stroke-width="3"/>')
    parts.append(text(610, 404, "rendezvous", "small", anchor="middle"))
    parts.append(curved_arrow(342, 540, 456, 586, 600, 438, COLORS["cyan"], 2.4))
    parts.append(curved_arrow(650, 408, 646, 380, 660, 350, COLORS["purple"], 2.4))

    # Delta-v curve inset.
    tli_points = [(float(row["leo_altitude_km"]), float(row["delta_v_tli_km_s"])) for row in transfer]
    parts.extend(
        line_chart(
            112,
            662,
            392,
            116,
            [("TLI Delta-v", tli_points, COLORS["purple"])],
            "Parking altitude (km)",
            "km/s",
            "TLI sensitivity",
            y_min=min(y for _, y in tli_points) - 0.01,
            y_max=max(y for _, y in tli_points) + 0.01,
        )
    )
    rv_points = [(float(row["phasing_altitude_km"]), float(row["wait_time_hours"])) for row in rendezvous]
    parts.extend(
        line_chart(
            574,
            662,
            392,
            116,
            [("Wait time", rv_points, COLORS["orange"])],
            "Phasing altitude (km)",
            "hours",
            "Phasing sensitivity",
        )
    )

    facts = [
        ("Target LEO", "300 km"),
        ("Phasing LEO", "260 km example"),
        ("Phase angle", f"{float(rv['phase_angle_deg']):.0f} deg"),
        ("Wait time", f"{float(rv['wait_time_hours']):.1f} h"),
        ("Rendezvous Delta-v", f"{float(rv['total_rendezvous_delta_v_m_s']):.1f} m/s"),
        ("TLI Delta-v", f"{float(tli['delta_v_tli_km_s']):.3f} km/s"),
        ("Transfer time", f"{float(tli['time_of_flight_days']):.2f} d"),
    ]
    parts.append(text(1132, 160, "Numerical anchors", "section"))
    for idx, (k, v) in enumerate(facts):
        y = 206 + idx * 66
        parts.append(f'<rect x="1130" y="{y - 31}" width="276" height="48" rx="12" fill="#ffffff" stroke="#d9e1e8"/>')
        parts.append(text(1150, y - 5, k, "small"))
        parts.append(text(1400, y - 5, v, "label", anchor="end"))
    parts.append('<rect x="1130" y="710" width="276" height="70" rx="12" fill="#f6f8fb" stroke="#d9e1e8"/>')
    parts.append(wrapped_text(1150, 735, "The figure separates small rendezvous impulses from the much larger TLI burn, which is the main mass-budget driver.", 238, 14, "small"))

    parts.append(svg_footer())
    write_svg(FIGURES / "leo_tli_orbit_diagram_enhanced.svg", parts)


def write_ascent_dashboard_figure(summary: dict[str, object], ascent: list[dict[str, str]]) -> None:
    final = summary["ascent_eci_terminal"]
    max_q = max(ascent, key=lambda row: float(row["dynamic_pressure_kpa"]))
    times = [float(row["time_s"]) for row in ascent]
    t_min, t_max = min(times), max(times)
    stage_changes = stage_change_times(ascent)

    altitude = [(float(row["time_s"]), float(row["altitude_km"])) for row in ascent]
    speed = [(float(row["time_s"]), float(row["inertial_speed_m_s"]) / 1000.0) for row in ascent]
    q = [(float(row["time_s"]), float(row["dynamic_pressure_kpa"])) for row in ascent]
    mass = [(float(row["time_s"]), float(row["mass_t"])) for row in ascent]

    parts = [
        svg_header(1500, 980),
        title_block(
            750,
            54,
            "Enhanced Fig. 6/7: ECI Ascent Dashboard",
            "A four-panel diagnostic figure is more useful for a competition paper than separate single-line plots.",
        ),
    ]
    parts.append('<rect x="58" y="116" width="1384" height="744" rx="18" class="panel"/>')

    panels = [
        (96, 160, "Altitude profile", altitude, "Altitude (km)", COLORS["blue"], 0, 350, [(300, 320, "#e8f5ed")]),
        (786, 160, "Inertial speed", speed, "Speed (km/s)", COLORS["red"], 0, 8.2, [(7.65, 7.85, "#f7ece8")]),
        (96, 504, "Dynamic pressure", q, "q (kPa)", COLORS["orange"], 0, 24, None),
        (786, 504, "Vehicle mass", mass, "Mass (t)", COLORS["green"], 0, 2250, None),
    ]
    for x, y, title, points, y_label, color, y_min, y_max, bands in panels:
        parts.extend(
            line_chart(
                x,
                y,
                590,
                258,
                [(title, points, color)],
                "Time (s)",
                y_label,
                title,
                x_min=t_min,
                x_max=t_max,
                y_min=y_min,
                y_max=y_max,
                verticals=stage_changes,
                bands=bands,
            )
        )

    # Mark max-Q on dynamic pressure panel.
    q_x, q_y, q_w, q_h = 96, 504, 590, 258
    max_q_time = float(max_q["time_s"])
    max_q_value = float(max_q["dynamic_pressure_kpa"])
    px = chart_x(q_x, q_w, max_q_time, t_min, t_max)
    py = chart_y(q_y, q_h, max_q_value, 0, 24)
    parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="{COLORS["red"]}" stroke="#ffffff" stroke-width="2"/>')
    parts.append(text(px + 14, py - 8, f"max-Q {max_q_value:.1f} kPa", "small"))

    # Stage legend and final-state summary.
    parts.append('<rect x="92" y="794" width="1316" height="54" rx="14" fill="#f6f8fb" stroke="#d9e1e8"/>')
    stage_text = "Stage transitions: " + ", ".join(f"{name} at {time:.0f} s" for time, name in stage_changes[1:])
    final_text = (
        f"Terminal state: altitude {float(final['altitude_km']):.1f} km, "
        f"inertial speed {float(final['inertial_speed_m_s']) / 1000.0:.3f} km/s, "
        f"flight-path angle {float(final['flight_path_angle_deg']):+.2f} deg."
    )
    parts.append(text(120, 826, stage_text, "small"))
    parts.append(text(760, 826, final_text, "small"))
    parts.append(svg_footer())
    write_svg(FIGURES / "ascent_dashboard_enhanced.svg", parts)


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_svg(path: Path, parts: Iterable[str]) -> None:
    path.write_text("\n".join(parts), encoding="utf-8")


def svg_header(width: int, height: int) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <marker id="arrow-muted" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 12 6 L 0 12 z" fill="#738391"/>
    </marker>
    <marker id="arrow-purple" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 12 6 L 0 12 z" fill="#6f4aa8"/>
    </marker>
    <filter id="soft-shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#17212b" flood-opacity="0.10"/>
    </filter>
    <style>
      text {{ font-family: Arial, Helvetica, sans-serif; fill: {COLORS["ink"]}; }}
      .title {{ font-size: 28px; font-weight: 700; }}
      .subtitle {{ font-size: 15px; fill: {COLORS["muted"]}; }}
      .section {{ font-size: 18px; font-weight: 700; }}
      .label {{ font-size: 15px; font-weight: 700; }}
      .body {{ font-size: 15px; fill: #31404c; }}
      .small {{ font-size: 13px; fill: {COLORS["muted"]}; }}
      .tiny {{ font-size: 11px; fill: {COLORS["muted"]}; }}
      .tiny-white {{ font-size: 10px; fill: #ffffff; font-weight: 700; }}
      .metric {{ font-size: 30px; font-weight: 700; }}
      .mono {{ font-size: 14px; font-family: Consolas, Menlo, monospace; fill: #31404c; }}
      .step {{ font-size: 18px; font-weight: 700; fill: #ffffff; }}
      .table-head {{ font-size: 14px; font-weight: 700; fill: #44525e; }}
      .panel {{ fill: #ffffff; stroke: #d5dee7; stroke-width: 1.3; filter: url(#soft-shadow); }}
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#f3f6fa"/>"""


def svg_footer() -> str:
    return "</svg>"


def title_block(x: float, y: float, title: str, subtitle: str) -> str:
    return "\n".join(
        [
            text(x, y, title, "title", anchor="middle"),
            text(x, y + 28, subtitle, "subtitle", anchor="middle"),
        ]
    )


def text(x: float, y: float, value: str, css: str = "body", anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{css}" text-anchor="{anchor}">{esc(value)}</text>'


def wrapped_text(x: float, y: float, value: str, width: float, size: int, css: str) -> str:
    words = value.split()
    lines: list[str] = []
    current = ""
    max_chars = max(16, int(width / (size * 0.55)))
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return "\n".join(text(x, y + i * (size + 4), line, css) for i, line in enumerate(lines))


def metric_card(x: float, y: float, w: float, h: float, label: str, value: str, note: str, color: str) -> list[str]:
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#ffffff" stroke="#d9e1e8" filter="url(#soft-shadow)"/>',
        f'<rect x="{x}" y="{y}" width="7" height="{h}" rx="3.5" fill="{color}"/>',
        text(x + 22, y + 29, label, "small"),
        text(x + 22, y + 61, value, "metric"),
        text(x + 22, y + 82, note, "tiny"),
    ]


def earth_icon(cx: float, cy: float, r: float) -> str:
    return "\n".join(
        [
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#e8f2ff" stroke="#2468b4" stroke-width="2"/>',
            f'<path d="M {cx - 70} {cy - 14} C {cx - 35} {cy - 48}, {cx + 4} {cy - 26}, {cx + 40} {cy - 54} C {cx + 80} {cy - 26}, {cx + 55} {cy + 24}, {cx + 18} {cy + 28} C {cx - 22} {cy + 34}, {cx - 52} {cy + 18}, {cx - 70} {cy - 14}" fill="#b7d7ef"/>',
            f'<path d="M {cx - 42} {cy + 44} C {cx - 10} {cy + 28}, {cx + 30} {cy + 42}, {cx + 58} {cy + 14}" fill="none" stroke="#7fb3d7" stroke-width="10" stroke-linecap="round" opacity="0.7"/>',
        ]
    )


def rocket_icon(x: float, y: float, scale: float, color: str, label: str) -> str:
    w = 46 * scale
    h = 118 * scale
    flame = 28 * scale
    parts = [
        f'<path d="M {x + w / 2:.1f} {y:.1f} C {x + w:.1f} {y + 22 * scale:.1f}, {x + w:.1f} {y + 52 * scale:.1f}, {x + w * 0.76:.1f} {y + h:.1f} L {x + w * 0.24:.1f} {y + h:.1f} C {x:.1f} {y + 52 * scale:.1f}, {x:.1f} {y + 22 * scale:.1f}, {x + w / 2:.1f} {y:.1f} Z" fill="#ffffff" stroke="{color}" stroke-width="{2.2 * scale:.1f}"/>',
        f'<rect x="{x + w * 0.24:.1f}" y="{y + h * 0.48:.1f}" width="{w * 0.52:.1f}" height="{h * 0.28:.1f}" fill="{color}" opacity="0.18"/>',
        f'<circle cx="{x + w / 2:.1f}" cy="{y + h * 0.33:.1f}" r="{8 * scale:.1f}" fill="{color}" opacity="0.85"/>',
        f'<path d="M {x + w * 0.22:.1f} {y + h:.1f} L {x + w * 0.03:.1f} {y + h + 25 * scale:.1f} L {x + w * 0.38:.1f} {y + h:.1f} Z" fill="{color}"/>',
        f'<path d="M {x + w * 0.78:.1f} {y + h:.1f} L {x + w * 0.97:.1f} {y + h + 25 * scale:.1f} L {x + w * 0.62:.1f} {y + h:.1f} Z" fill="{color}"/>',
        f'<path d="M {x + w * 0.36:.1f} {y + h + 4 * scale:.1f} C {x + w * 0.5:.1f} {y + h + flame:.1f}, {x + w * 0.64:.1f} {y + h + 4 * scale:.1f}, {x + w * 0.5:.1f} {y + h + flame * 1.35:.1f} Z" fill="#f4a340" opacity="0.8"/>',
    ]
    if label:
        parts.append(text(x + w / 2, y + h + flame * 1.65, label, "tiny", anchor="middle"))
    return "\n".join(parts)


def module_icon(x: float, y: float, color: str, label: str, note: str) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="118" height="54" rx="10" fill="#ffffff" stroke="{color}" stroke-width="2.2"/>',
            f'<rect x="{x + 14}" y="{y + 14}" width="90" height="26" rx="5" fill="{color}" opacity="0.16"/>',
            f'<line x1="{x - 28}" y1="{y + 27}" x2="{x}" y2="{y + 27}" stroke="{color}" stroke-width="3"/>',
            f'<line x1="{x + 118}" y1="{y + 27}" x2="{x + 146}" y2="{y + 27}" stroke="{color}" stroke-width="3"/>',
            text(x + 59, y + 22, label, "label", anchor="middle"),
            text(x + 59, y + 42, note, "tiny", anchor="middle"),
        ]
    )


def stack_icon(x: float, y: float) -> str:
    return "\n".join(
        [
            module_icon(x, y, COLORS["green"], "Stack", "40 t cargo"),
            f'<rect x="{x + 30}" y="{y + 62}" width="58" height="40" rx="8" fill="#ffffff" stroke="{COLORS["purple"]}" stroke-width="2.0"/>',
            text(x + 59, y + 88, "TLI", "small", anchor="middle"),
        ]
    )


def curved_arrow(x1: float, y1: float, cx: float, cy: float, x2: float, y2: float, color: str, width: float) -> str:
    marker = "arrow-purple" if color == COLORS["purple"] else "arrow-muted"
    return f'<path d="M {x1:.1f} {y1:.1f} Q {cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}" fill="none" stroke="{color}" stroke-width="{width:.1f}" marker-end="url(#{marker})"/>'


def status_badge(x: float, y: float, label: str, color: str) -> str:
    w = max(110, len(label) * 8 + 28)
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{color}" opacity="0.13" stroke="{color}"/>',
            text(x + w / 2, y + 22, label, "small", anchor="middle"),
        ]
    )


def progress_bar(x: float, y: float, w: float, h: float, fraction: float, color: str) -> str:
    fraction = max(0.0, min(1.0, fraction))
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="#eef2f6"/>',
            f'<rect x="{x}" y="{y}" width="{w * fraction:.1f}" height="{h}" rx="{h / 2}" fill="{color}"/>',
        ]
    )


def mass_node(x: float, y: float, label: str, value: str, color: str) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="156" height="68" rx="14" fill="#ffffff" stroke="{color}" stroke-width="2.2"/>',
            text(x + 78, y + 28, label, "label", anchor="middle"),
            text(x + 78, y + 52, value, "small", anchor="middle"),
        ]
    )


def flow_path(x1: float, y1: float, x2: float, y2: float, width: float, color: str) -> str:
    width = max(8.0, min(74.0, width))
    c1 = x1 + (x2 - x1) * 0.45
    c2 = x1 + (x2 - x1) * 0.55
    return f'<path d="M {x1:.1f} {y1:.1f} C {c1:.1f} {y1:.1f}, {c2:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}" fill="none" stroke="{color}" stroke-width="{width:.1f}" stroke-linecap="round" opacity="0.54"/>'


def line_chart(
    x: float,
    y: float,
    w: float,
    h: float,
    series: list[tuple[str, list[tuple[float, float]], str]],
    x_label: str,
    y_label: str,
    title: str,
    x_min: float | None = None,
    x_max: float | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
    verticals: list[tuple[float, str]] | None = None,
    bands: list[tuple[float, float, str]] | None = None,
) -> list[str]:
    all_x = [px for _, points, _ in series for px, _ in points]
    all_y = [py for _, points, _ in series for _, py in points]
    x_min = min(all_x) if x_min is None else x_min
    x_max = max(all_x) if x_max is None else x_max
    y_min = min(all_y) if y_min is None else y_min
    y_max = max(all_y) if y_max is None else y_max
    if abs(x_max - x_min) < 1e-12:
        x_max += 1
    if abs(y_max - y_min) < 1e-12:
        y_max += 1

    pad_l, pad_r, pad_t, pad_b = 58, 18, 38, 48
    gx, gy = x + pad_l, y + pad_t
    gw, gh = w - pad_l - pad_r, h - pad_t - pad_b
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#ffffff" stroke="#d9e1e8"/>',
        text(x + 20, y + 26, title, "label"),
    ]
    if bands:
        for low, high, fill in bands:
            y1 = chart_y_with_area(gy, gh, high, y_min, y_max)
            y2 = chart_y_with_area(gy, gh, low, y_min, y_max)
            parts.append(f'<rect x="{gx}" y="{y1}" width="{gw}" height="{y2 - y1}" fill="{fill}" opacity="0.9"/>')

    for tick in range(5):
        frac = tick / 4
        x_pos = gx + frac * gw
        y_pos = gy + frac * gh
        parts.append(f'<line x1="{gx}" y1="{y_pos:.1f}" x2="{gx + gw}" y2="{y_pos:.1f}" stroke="#edf1f4"/>')
        xv = x_min + frac * (x_max - x_min)
        yv = y_max - frac * (y_max - y_min)
        parts.append(text(x_pos, gy + gh + 20, nice_number(xv), "tiny", anchor="middle"))
        parts.append(text(gx - 8, y_pos + 4, nice_number(yv), "tiny", anchor="end"))

    parts.append(f'<line x1="{gx}" y1="{gy}" x2="{gx}" y2="{gy + gh}" stroke="#798996"/>')
    parts.append(f'<line x1="{gx}" y1="{gy + gh}" x2="{gx + gw}" y2="{gy + gh}" stroke="#798996"/>')

    if verticals:
        for vx, label in verticals[1:]:
            px = chart_x_with_area(gx, gw, vx, x_min, x_max)
            parts.append(f'<line x1="{px:.1f}" y1="{gy}" x2="{px:.1f}" y2="{gy + gh}" stroke="#bcc8d2" stroke-dasharray="5 5"/>')
            parts.append(text(px + 4, gy + 14, label.replace("_", " "), "tiny"))

    for name, points, color in series:
        pts = " ".join(
            f"{chart_x_with_area(gx, gw, px, x_min, x_max):.1f},{chart_y_with_area(gy, gh, py, y_min, y_max):.1f}"
            for px, py in points
        )
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.6" points="{pts}"/>')
        parts.append(f'<circle cx="{chart_x_with_area(gx, gw, points[-1][0], x_min, x_max):.1f}" cy="{chart_y_with_area(gy, gh, points[-1][1], y_min, y_max):.1f}" r="4.5" fill="{color}"/>')

    parts.append(text(x + w / 2, y + h - 12, x_label, "tiny", anchor="middle"))
    parts.append(
        f'<text transform="translate({x + 18:.1f} {y + h / 2:.1f}) rotate(-90)" '
        f'class="tiny" text-anchor="middle">{esc(y_label)}</text>'
    )
    return parts


def chart_x(x: float, w: float, value: float, v_min: float, v_max: float) -> float:
    pad_l, pad_r = 58, 18
    return chart_x_with_area(x + pad_l, w - pad_l - pad_r, value, v_min, v_max)


def chart_y(y: float, h: float, value: float, v_min: float, v_max: float) -> float:
    pad_t, pad_b = 38, 48
    return chart_y_with_area(y + pad_t, h - pad_t - pad_b, value, v_min, v_max)


def chart_x_with_area(x: float, w: float, value: float, v_min: float, v_max: float) -> float:
    return x + (value - v_min) / (v_max - v_min) * w


def chart_y_with_area(y: float, h: float, value: float, v_min: float, v_max: float) -> float:
    return y + (v_max - value) / (v_max - v_min) * h


def stage_change_times(rows: list[dict[str, str]]) -> list[tuple[float, str]]:
    changes: list[tuple[float, str]] = []
    last = ""
    for row in rows:
        stage = row["stage"]
        if stage != last:
            changes.append((float(row["time_s"]), stage))
            last = stage
    return changes


def nice_number(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def blend(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return f"#{round(r1 + (r2 - r1) * t):02x}{round(g1 + (g2 - g1) * t):02x}{round(b1 + (b2 - b1) * t):02x}"


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def esc(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    main()
