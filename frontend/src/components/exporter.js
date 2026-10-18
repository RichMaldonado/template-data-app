// Modulo unificado de exportacion de widgets a PNG en alta resolucion (HiDPI 2x)
// Incluye: Grafico/Contenido + Titulo del Widget + Subtitulo + Nombre de la Data App Origen + Filtros Activos + Fecha

function loadImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = (e) => reject(e);
    img.src = dataUrl;
  });
}

function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight) {
  if (!text) return y;
  const words = text.split(' ');
  let line = '';
  let currentY = y;

  for (let i = 0; i < words.length; i++) {
    const testLine = line ? `${line} ${words[i]}` : words[i];
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && i > 0) {
      ctx.fillText(line, x, currentY);
      line = words[i];
      currentY += lineHeight;
    } else {
      line = testLine;
    }
  }
  if (line) {
    ctx.fillText(line, x, currentY);
    currentY += lineHeight;
  }
  return currentY;
}

/**
 * Compone un canvas en alta resolucion (2x) combinando:
 * 1. Nombre de la Data App Origen y Fecha
 * 2. Titulo del Widget y Subtitulo/Metrica
 * 3. Imagen del Grafico ECharts (o contenido)
 * 4. Contexto de filtros activos en el pie
 * 
 * @param {object} chartInstance Instancia activa de ECharts
 * @param {object} meta { appName, widgetTitle, widgetSubtitle, filtersContext }
 */
export async function exportWidgetToPng(chartInstance, meta = {}) {
  if (!chartInstance || typeof chartInstance.getDataURL !== 'function') {
    console.error('Instancia ECharts no valida para exportar');
    return;
  }

  const pixelRatio = 2;
  const scale = pixelRatio;
  const appName = meta.appName || 'Data App';
  const widgetTitle = meta.widgetTitle || 'Métrica Analítica';
  const widgetSubtitle = meta.widgetSubtitle || '';
  const filtersContext = meta.filtersContext || '';

  const isDark = document.documentElement.classList.contains('dark');
  const colors = isDark ? {
    bg: '#0f172a',
    cardBg: '#1e293b',
    textMain: '#f8fafc',
    textMuted: '#94a3b8',
    brand: '#22c55e',
    line: '#334155'
  } : {
    bg: '#f8fafc',
    cardBg: '#ffffff',
    textMain: '#0f172a',
    textMuted: '#64748b',
    brand: '#16a34a',
    line: '#e2e8f0'
  };

  // 1. Extraer imagen del grafico con pixelRatio 2x
  const chartDataUrl = chartInstance.getDataURL({
    type: 'png',
    pixelRatio: pixelRatio,
    backgroundColor: colors.cardBg,
    excludeComponents: ['toolbox']
  });

  const chartImg = await loadImage(chartDataUrl);

  const paddingX = 28 * scale;
  const canvasWidth = chartImg.width + (paddingX * 2);

  const appFontSize = Math.round(11 * scale);
  const titleFontSize = Math.round(18 * scale);
  const subtitleFontSize = Math.round(12 * scale);
  const footerFontSize = Math.round(10 * scale);

  let headerHeight = 24 * scale;
  headerHeight += appFontSize + (10 * scale);
  headerHeight += titleFontSize * 1.3;
  if (widgetSubtitle) headerHeight += subtitleFontSize * 1.4;
  headerHeight += 16 * scale; // margen inferior del header

  const footerHeight = 40 * scale;
  const canvasHeight = Math.round(headerHeight + chartImg.height + footerHeight);

  // Crear canvas offscreen
  const canvas = document.createElement('canvas');
  canvas.width = canvasWidth;
  canvas.height = canvasHeight;
  const ctx = canvas.getContext('2d');

  // Fondo
  ctx.fillStyle = colors.cardBg;
  ctx.fillRect(0, 0, canvasWidth, canvasHeight);

  // Borde exterior estilizado
  ctx.strokeStyle = colors.line;
  ctx.lineWidth = 2 * scale;
  ctx.strokeRect(1 * scale, 1 * scale, canvasWidth - 2 * scale, canvasHeight - 2 * scale);

  // Header: Nombre de la Data App Origen (arriba a la izquierda)
  let currentY = 24 * scale;
  ctx.font = `700 ${appFontSize}px Inter, sans-serif`;
  ctx.fillStyle = colors.brand;
  ctx.fillText(appName.toUpperCase(), paddingX, currentY);

  // Fecha actual (arriba a la derecha)
  const fechaStr = new Date().toLocaleDateString('es-MX', {
    year: 'numeric',
    month: 'short',
    day: '2-digit'
  });
  ctx.font = `400 ${appFontSize}px Inter, sans-serif`;
  ctx.fillStyle = colors.textMuted;
  ctx.textAlign = 'right';
  ctx.fillText(fechaStr, canvasWidth - paddingX, currentY);
  ctx.textAlign = 'left';

  currentY += 18 * scale;

  // Titulo del Widget
  const maxTextWidth = canvasWidth - (paddingX * 2);
  ctx.font = `700 ${titleFontSize}px Inter, sans-serif`;
  ctx.fillStyle = colors.textMain;
  currentY = drawWrappedText(ctx, widgetTitle, paddingX, currentY, maxTextWidth, titleFontSize * 1.3);

  // Subtitulo opcional
  if (widgetSubtitle) {
    currentY += 2 * scale;
    ctx.font = `400 ${subtitleFontSize}px Inter, sans-serif`;
    ctx.fillStyle = colors.textMuted;
    currentY = drawWrappedText(ctx, widgetSubtitle, paddingX, currentY, maxTextWidth, subtitleFontSize * 1.3);
  }

  currentY += 10 * scale;

  // Linea divisoria superior
  ctx.strokeStyle = colors.line;
  ctx.lineWidth = 1 * scale;
  ctx.beginPath();
  ctx.moveTo(paddingX, currentY);
  ctx.lineTo(canvasWidth - paddingX, currentY);
  ctx.stroke();

  currentY += 12 * scale;

  // Dibujar el grafico
  ctx.drawImage(chartImg, paddingX, currentY);

  // Footer: Contexto de filtros activos
  const footerY = canvasHeight - (16 * scale);
  ctx.font = `500 ${footerFontSize}px Inter, sans-serif`;
  ctx.fillStyle = colors.textMuted;
  const footerText = filtersContext ? `Filtros: ${filtersContext}` : 'Reporte Analitico Generado';
  ctx.fillText(footerText, paddingX, footerY);

  // Descarga automatica del PNG
  const safeTitle = widgetTitle.toLowerCase().replace(/[^a-z0-9]/gi, '_').substring(0, 40);
  const downloadLink = document.createElement('a');
  downloadLink.download = `${appName.toLowerCase().replace(/\s+/g, '_')}_${safeTitle}.png`;
  downloadLink.href = canvas.toDataURL('image/png');
  document.body.appendChild(downloadLink);
  downloadLink.click();
  document.body.removeChild(downloadLink);
}
