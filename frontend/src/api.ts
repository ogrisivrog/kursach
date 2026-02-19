const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.headers.get('content-type')?.includes('application/json')) return res.json();
  return res.text() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; db: string }>('/health'),
  stats: () => request<{
    items: number;
    locations: number;
    inventory_rows: number;
    qty_sum: number;
    requirements_rows: number;
    requirements_sum: number;
  }>('/stats'),
  inventory: (params?: { item?: string; location?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.item) q.set('item', params.item);
    if (params?.location) q.set('location', params.location);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));
    return request<{ total: number; limit: number; offset: number; rows: { item_name: string; location: string; qty_available: number }[] }>(`/inventory?${q}`);
  },
  inventorySummary: () =>
    request<{ rows: { item_name: string; qty_total: number }[] }>('/inventory/summary'),
  requirements: (params?: { discipline?: string; item?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.discipline) q.set('discipline', params.discipline);
    if (params?.item) q.set('item', params.item);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));
    return request<{ total: number; limit: number; offset: number; rows: { discipline: string | null; lab: string | null; item_name: string; qty_required: number }[] }>(`/requirements?${q}`);
  },
  requirementsSummary: (by: 'item' | 'discipline' = 'item') =>
    request<{ by: string; rows: { item_name?: string; discipline?: string; qty_required: number }[] }>(`/requirements/summary?by=${by}`),
  coverage: (params?: { only_deficit?: boolean; mode?: 'sum' | 'max_per_lab' }) => {
    const q = new URLSearchParams();
    if (params?.only_deficit !== undefined) q.set('only_deficit', String(params.only_deficit));
    if (params?.mode) q.set('mode', params.mode);
    return request<{ only_deficit: boolean; mode: string; rows: { item_name: string; qty_required: number; qty_available: number; deficit: number }[] }>(`/calc/coverage?${q}`);
  },
  softwareCoverage: (params?: { only_deficit?: boolean; mode?: 'sum' | 'max_per_lab' }) => {
    const q = new URLSearchParams();
    if (params?.only_deficit !== undefined) q.set('only_deficit', String(params.only_deficit));
    if (params?.mode) q.set('mode', params.mode);
    return request<{ only_deficit: boolean; mode: string; rows: { software_name: string; seats_required: number; seats_available: number; deficit: number }[] }>(`/calc/software-coverage?${q}`);
  },
  reportProcurementCsv: (params?: { mode?: string; only_deficit?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.mode) q.set('mode', params.mode);
    if (params?.only_deficit !== undefined) q.set('only_deficit', String(params.only_deficit));
    return `${API_BASE}/reports/procurement.csv?${q}`;
  },
  reportSoftwareCsv: (params?: { mode?: string; only_deficit?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.mode) q.set('mode', params.mode);
    if (params?.only_deficit !== undefined) q.set('only_deficit', String(params.only_deficit));
    return `${API_BASE}/reports/software_coverage.csv?${q}`;
  },
  aiReport: (params?: { mode?: string; include_software?: boolean; students_factor?: number }) => {
    const q = new URLSearchParams();
    if (params?.mode) q.set('mode', params.mode);
    if (params?.include_software !== undefined) q.set('include_software', String(params.include_software));
    if (params?.students_factor !== undefined) q.set('students_factor', String(params.students_factor));
    return request<{ ok: boolean; report: string; data_used?: unknown }>(`/ai/report/explain?${q}`);
  },
  importInventory: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/import/inventory`, { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    return res.json();
  },
  importRequirements: async (file: File, replace: boolean) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/import/requirements?replace=${replace}`, { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    return res.json();
  },
};
