"""Tiny dependency-free SVG chart helpers for first-pass figures."""

from __future__ import annotations

from pathlib import Path


def write_line_chart(
    path: Path,
    title: str,
    x_label: str,
    y_label: str,
    series: list[tuple[str, list[tuple[float, float]], str]],
    width: int = 760,
    height: int = 460,
) -> None:
    """Write a simple SVG line chart.

    This avoids adding matplotlib as a dependency during the first modeling
    pass. It is enough for quick inspection and can be replaced later.
    """

    all_x = [x for _, points, _ in series for x, _ in points]
    all_y = [y for _, points, _ in series for _, y in points]
    if not all_x or not all_y:
        raise ValueError("chart series must contain points")

    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    if x_min == x_max:
        x_max = x_min + 1.0
    if y_min == y_max:
        y_max = y_min + 1.0

    pad_l, pad_r, pad_t, pad_b = 78, 24, 54, 70
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    def sx(x: float) -> float:
        return pad_l + (x - x_min) / (x_max - x_min) * plot_w

    def sy(y: float) -> float:
        return pad_t + (y_max - y) / (y_max - y_min) * plot_h

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{_esc(title)}</text>',
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height - pad_b}" stroke="#222" stroke-width="1.2"/>',
        f'<line x1="{pad_l}" y1="{height - pad_b}" x2="{width - pad_r}" y2="{height - pad_b}" stroke="#222" stroke-width="1.2"/>',
    ]

    for tick in range(6):
        frac = tick / 5
        x_val = x_min + frac * (x_max - x_min)
        x_pos = sx(x_val)
        parts.append(f'<line x1="{x_pos:.1f}" y1="{height - pad_b}" x2="{x_pos:.1f}" y2="{height - pad_b + 5}" stroke="#222"/>')
        parts.append(f'<text x="{x_pos:.1f}" y="{height - pad_b + 22}" text-anchor="middle" font-family="Arial" font-size="11">{x_val:.3g}</text>')

        y_val = y_min + frac * (y_max - y_min)
        y_pos = sy(y_val)
        parts.append(f'<line x1="{pad_l - 5}" y1="{y_pos:.1f}" x2="{pad_l}" y2="{y_pos:.1f}" stroke="#222"/>')
        parts.append(f'<text x="{pad_l - 10}" y="{y_pos + 4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{y_val:.3g}</text>')
        parts.append(f'<line x1="{pad_l}" y1="{y_pos:.1f}" x2="{width - pad_r}" y2="{y_pos:.1f}" stroke="#e6e6e6"/>')

    for name, points, color in series:
        point_text = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in points)
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.3" points="{point_text}"/>')

    legend_x = pad_l + 8
    legend_y = pad_t + 18
    for idx, (name, _, color) in enumerate(series):
        y = legend_y + idx * 20
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 24}" y2="{y}" stroke="{color}" stroke-width="2.6"/>')
        parts.append(f'<text x="{legend_x + 32}" y="{y + 4}" font-family="Arial" font-size="12">{_esc(name)}</text>')

    parts.append(f'<text x="{width / 2:.1f}" y="{height - 18}" text-anchor="middle" font-family="Arial" font-size="13">{_esc(x_label)}</text>')
    parts.append(
        f'<text transform="translate(18 {height / 2:.1f}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="13">{_esc(y_label)}</text>'
    )
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def _esc(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

