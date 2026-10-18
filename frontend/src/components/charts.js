import * as echarts from 'echarts';

const chartInstances = {};

export function getChartInstance(id) {
  return chartInstances[id] || null;
}

export function renderTendenciaChart(elementId, data) {
  const dom = document.getElementById(elementId);
  if (!dom) return null;

  let instance = chartInstances[elementId];
  if (!instance) {
    instance = echarts.init(dom);
    chartInstances[elementId] = instance;
    window.addEventListener('resize', () => instance.resize());
  }

  const ciclos = data.map(d => d.ciclo);
  const ventas = data.map(d => d.venta);

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ciclos,
      axisLine: { lineStyle: { color: '#94a3b8' } }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#94a3b8' } },
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } }
    },
    series: [
      {
        name: 'Venta',
        type: 'line',
        smooth: true,
        data: ventas,
        itemStyle: { color: '#22c55e' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34, 197, 94, 0.4)' },
            { offset: 1, color: 'rgba(34, 197, 94, 0.0)' }
          ])
        }
      }
    ]
  };

  instance.setOption(option);
  return instance;
}

export function resizeAllCharts() {
  Object.values(chartInstances).forEach(inst => inst && inst.resize());
}
