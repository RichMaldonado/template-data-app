import Alpine from 'alpinejs';
import { createDashboardStore } from './store.js';
import { renderTendenciaChart } from './components/charts.js';
import './styles/main.css';

window.Alpine = Alpine;
Alpine.data('dashboard', createDashboardStore);

Alpine.start();

// Listener global para inicializar o redibujar charts cuando los datos cambian
window.addEventListener('data-updated', (event) => {
  const { tendencia } = event.detail;
  if (tendencia && tendencia.length > 0) {
    setTimeout(() => {
      renderTendenciaChart('chart-tendencia', tendencia);
    }, 50);
  }
});
