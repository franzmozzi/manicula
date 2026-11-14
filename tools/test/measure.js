// Injected by check.py / sweep.py. Reports, per block, how far the fingertip sits from the
// centre of the target line, plus lines leaving the column or touching the figure's ink.
window.set = (id, v) => { const el = document.getElementById(id); el.value = v; el.dispatchEvent(new Event('input')); };
window.measure = () => ({ vw: innerWidth, sw: document.documentElement.scrollWidth, blocks: maniculae.map((b) => {
  const ir = b.img.getBoundingClientRect(), fr = b.flow.getBoundingClientRect();
  const hit = b.flow.querySelector('mark') || b.flow.querySelector('.line.is-pointed');
  const lr = hit && (hit.closest('.line') || hit).getBoundingClientRect();
  const n = b.profile.rows.length;
  let outOfCol = 0, overlaps = 0;
  for (const s of b.flow.querySelectorAll('.line')) {
    const r = s.getBoundingClientRect();
    if (r.right > fr.right + 0.5 || r.left < fr.left - 0.5) outOfCol++;
    for (let y = Math.max(r.top, ir.top); y < Math.min(r.bottom, ir.bottom); y++) {
      const reach = b.profile.rows[Math.floor((y - ir.top) / ir.height * n)] * ir.width;
      if (!reach) continue;
      const inkX = b.side === 'left' ? ir.left + reach : ir.right - reach;
      // list markers hang ~0.7 indent to the left of the line box
      const left = r.left - (s.classList.contains('has-marker') ? 20 : 0);
      if (b.side === 'left' ? left < inkX : r.right > inkX) { overlaps++; break; }
    }
  }
  const segOk = b.items.every((it) => it.prepared.segments.join('') === it.text);
  return { id: b.el.id, status: b.status?.textContent ?? "", gap: lr ? +(ir.top + b.tip.y * ir.height - (lr.top + lr.bottom) / 2).toFixed(2) : null,
    lines: b.flow.children.length, outOfCol, overlaps, segOk, imgW: Math.round(ir.width), imgL: Math.round(ir.left), imgR: Math.round(ir.right) };
}) });
