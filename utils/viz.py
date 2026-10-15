"""
utils/viz.py — Lightweight HTML charts for dashboard cards.

Plain flex/div markup that stretches to fill its card, follows the theme variables and
renders instantly (no Plotly round-trip). Each function returns an HTML string.
"""

CSS = """
<style>
.vz-bars{display:flex;align-items:flex-end;gap:2px;flex:1 1 auto;min-height:60px;position:relative;padding-top:14px}
.vz-bars .b{flex:1;background:var(--acc);opacity:.28;border-radius:2px 2px 0 0;position:relative;transition:opacity .2s}
.vz-bars .b:hover{opacity:.7}
.vz-bars .b.hi{background:var(--pk);opacity:1}
.vz-bars .b.hi::after{content:attr(data-v);position:absolute;bottom:100%;left:50%;transform:translateX(-50%);
  font:700 .62rem 'Inter';color:var(--pk);white-space:nowrap;margin-bottom:2px}
.vz-bars .avg{position:absolute;left:0;right:0;border-top:1px dashed var(--mute);pointer-events:none}
.vz-bars .avg span{position:absolute;right:0;bottom:2px;font:600 .58rem 'Inter';color:var(--mute);background:var(--card);padding:0 3px}
.vz-axis{display:flex;justify-content:space-between;font:600 .58rem 'Inter';color:var(--faint);margin-top:4px;letter-spacing:.06em}
.vz-rows{display:flex;flex-direction:column;gap:7px}
.vz-row{display:grid;grid-template-columns:minmax(0,1.3fr) 2fr auto;align-items:center;gap:10px;font-size:.74rem}
.vz-row span{color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vz-row i{display:block;height:6px;border-radius:3px;background:var(--chip);overflow:hidden}
.vz-row i b{display:block;height:100%;background:var(--acc);border-radius:3px}
.vz-row em{font-style:normal;font-family:'Anton';color:var(--ink);font-size:.9rem;text-align:right;min-width:52px}
.vz-stack{display:flex;height:28px;border-radius:3px;overflow:hidden;font:700 .66rem 'Inter';color:#fff}
.vz-stack div{display:flex;align-items:center;justify-content:center;min-width:30px}
.vz-legend{display:flex;justify-content:space-between;margin-top:6px;font-size:.66rem;color:var(--mute)}
.vz-legend b{color:var(--ink);font-family:'Anton';font-weight:400;font-size:.95rem;display:block}
</style>
"""


def bars(values, labels, hi=None, avg=None, fmt="{:.2f}", avg_label="avg", base=None):
    """Vertical bars filling the parent; `hi` index is highlighted with its value shown.
    `base` fixes the baseline (e.g. 0 for counts); by default it sits below the minimum so differences stay visible."""
    lo, top = min(values), max(values)
    if base is None:
        base = lo - (top - lo) * 0.6
    span = (top - base) or 1
    h = lambda v: max(2, (v - base) / span * 100)
    out = "".join(
        f'<div class="b{" hi" if i == hi else ""}" style="height:{h(v):.1f}%" data-v="{fmt.format(v)}" title="{l}: {fmt.format(v)}"></div>'
        for i, (v, l) in enumerate(zip(values, labels)))
    if avg is not None:
        out += f'<div class="avg" style="bottom:{h(avg):.1f}%"><span>{avg_label} {fmt.format(avg)}</span></div>'
    return f'<div class="vz-bars">{out}</div><div class="vz-axis"><span>{labels[0]}</span><span>{labels[-1]}</span></div>'


def hrows(rows, fmt="{:,}", color=None, sqrt=False):
    """Label · bar · value rows. rows = [(label, value)]. `sqrt` keeps small values visible next to big ones."""
    f = (lambda x: x ** 0.5) if sqrt else (lambda x: x)
    top = f(max(v for _, v in rows)) or 1
    c = f";background:{color}" if color else ""
    return '<div class="vz-rows">' + "".join(
        f'<div class="vz-row"><span title="{l}">{l}</span><i><b style="width:{f(v) / top * 100:.1f}%{c}"></b></i><em>{fmt.format(v)}</em></div>'
        for l, v in rows) + "</div>"


def stack(parts, fmt="{:,}"):
    """Stacked share bar. parts = [(label, value, colour)]."""
    tot = sum(v for _, v, _ in parts) or 1
    bar = "".join(f'<div style="flex:{v / tot:.4f};background:{c}">{v / tot:.0%}</div>' for _, v, c in parts)
    leg = "".join(f'<div><b>{fmt.format(v)}</b>{l}</div>' for l, v, _ in parts)
    return f'<div class="vz-stack">{bar}</div><div class="vz-legend">{leg}</div>'
