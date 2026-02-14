"use strict";

// Lightweight Matrix digital rain background
(function () {
  const canvas = document.getElementById('matrix');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let w, h, fontSize, columns, drops, animId;
  const glyphs = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const glyphArr = glyphs.split('');

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    // pick font size relative to DPI and width
    fontSize = Math.max(12, Math.min(22, Math.floor(w / 90)));
    columns = Math.floor(w / fontSize);
    drops = new Array(columns).fill(0).map(()=> (Math.random() * h / fontSize) | 0);
    ctx.font = `${fontSize}px monospace`;
  }

  function draw() {
    // translucent background to create trail
    ctx.fillStyle = 'rgba(11, 15, 16, 0.10)';
    ctx.fillRect(0, 0, w, h);

    for (let i = 0; i < columns; i++) {
      const char = glyphArr[(Math.random() * glyphArr.length) | 0];
      // tail color: lighter green at head, dim trails behind by alpha blending above
      ctx.fillStyle = Math.random() < 0.02 ? 'rgba(255, 255, 255, 0.8)' : 'rgba(35, 209, 139, 0.85)';
      const x = i * fontSize;
      const y = drops[i] * fontSize;
      ctx.fillText(char, x, y);

      if (y > h && Math.random() > 0.975) drops[i] = 0; // reset occasionally
      else drops[i]++;
    }
    animId = requestAnimationFrame(draw);
  }

  function start() {
    stop();
    resize();
    animId = requestAnimationFrame(draw);
  }

  function stop() { if (animId) cancelAnimationFrame(animId); }

  window.addEventListener('resize', () => {
    // debounce a bit
    stop();
    clearTimeout(start._t);
    start._t = setTimeout(start, 120);
  });

  start();
})();
