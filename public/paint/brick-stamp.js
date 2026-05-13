/* CSS Houdini paint worklet — brick-red textured stamp.
   Registered as paint(brick-stamp). Browser support: Chrome, Edge, Safari 17+.
   Fallback (Firefox + older Safari): see Stamp.astro @supports rule. */

class BrickStamp {
  static get inputProperties() {
    return ['--stamp-rotation', '--stamp-opacity'];
  }

  paint(ctx, geom, props) {
    const w = geom.width;
    const h = geom.height;
    const rotation = parseFloat(props.get('--stamp-rotation').toString()) || 0;
    const opacity = parseFloat(props.get('--stamp-opacity').toString()) || 0.85;

    ctx.save();
    ctx.translate(w / 2, h / 2);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.translate(-w / 2, -h / 2);

    // Solid brick-red base
    ctx.fillStyle = `rgba(155, 74, 63, ${opacity})`;
    ctx.fillRect(0, 0, w, h);

    // Texture noise: scatter darker dots
    ctx.fillStyle = `rgba(120, 50, 40, 0.18)`;
    const dots = Math.floor((w * h) / 240);
    for (let i = 0; i < dots; i++) {
      const x = Math.random() * w;
      const y = Math.random() * h;
      const r = Math.random() * 1.6;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Subtle ink-edge darkening at corners
    const grad = ctx.createRadialGradient(w / 2, h / 2, w * 0.2, w / 2, h / 2, w * 0.6);
    grad.addColorStop(0, 'rgba(0, 0, 0, 0)');
    grad.addColorStop(1, 'rgba(40, 18, 14, 0.15)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    ctx.restore();
  }
}

registerPaint('brick-stamp', BrickStamp);
