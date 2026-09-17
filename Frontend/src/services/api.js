import { supabase } from './supabase';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

async function getAuthHeader() {
  if (!supabase) return {};
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      return { Authorization: `Bearer ${session.access_token}` };
    }
  } catch (err) {
    console.warn('Could not fetch auth token:', err);
  }
  return {};
}

export const api = {
  async get(endpoint, params = {}) {
    const url = new URL(`${API_BASE_URL}${endpoint}`, window.location.origin);
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null) {
        url.searchParams.append(key, params[key]);
      }
    });

    const headers = {
      'Content-Type': 'application/json',
      ...(await getAuthHeader()),
    };

    const res = await fetch(url.toString(), { method: 'GET', headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  async post(endpoint, body = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(await getAuthHeader()),
    };

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  async patch(endpoint, body = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(await getAuthHeader()),
    };

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  async delete(endpoint) {
    const headers = {
      'Content-Type': 'application/json',
      ...(await getAuthHeader()),
    };

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  async upload(endpoint, formData) {
    const authHeaders = await getAuthHeader();
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        ...authHeaders,
      },
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },
};
