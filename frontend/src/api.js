/**
 * Cliente HTTP unificado.
 * Soporta peticiones GET con descarte de nulos y mutaciones CRUD (POST, DELETE, PUT).
 */
export async function request(endpoint, params = {}, options = {}) {
  const url = new URL(endpoint, window.location.origin);
  
  if (options.method === 'GET' || !options.method) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        if (Array.isArray(value)) {
          if (value.length > 0) url.searchParams.append(key, value.join(','));
        } else {
          url.searchParams.append(key, value);
        }
      }
    });
  }

  const fetchOptions = {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  };

  if (options.body) {
    fetchOptions.body = JSON.stringify(options.body);
  }

  const response = await fetch(url.toString(), fetchOptions);
  if (!response.ok) {
    throw new Error(`Error ${response.status} en ${endpoint}: ${response.statusText}`);
  }
  return await response.json();
}

// Consultas Analiticas (OLAP - DuckDB)
export async function fetchGeneralKpis(filtros) {
  return request('/api/v1/panel-general/kpis', filtros);
}

export async function fetchTendencia(filtros) {
  return request('/api/v1/panel-general/tendencia', filtros);
}

// Operaciones CRUD (OLTP - SQLite)
export async function fetchMetas(filtros = {}) {
  return request('/api/v1/crud/metas', filtros);
}

export async function saveMeta(metaData) {
  return request('/api/v1/crud/metas', {}, {
    method: 'POST',
    body: metaData
  });
}

export async function deleteMeta(metaId) {
  return request(`/api/v1/crud/metas/${metaId}`, {}, {
    method: 'DELETE'
  });
}
