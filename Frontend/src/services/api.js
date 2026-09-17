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

function formatNetworkError(err) {
  const isLocalHostTarget = !API_BASE_URL || API_BASE_URL.includes('localhost') || API_BASE_URL.includes('127.0.0.1');
  const isDeployedClient = typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

  if (isDeployedClient && isLocalHostTarget) {
    return new Error(
      `Cannot connect to backend: The frontend is deployed on ${window.location.hostname}, but is configured to connect to "${API_BASE_URL || 'http://localhost:8000'}". Please deploy your backend service (e.g. on Render or Railway) and set VITE_API_URL in your Vercel project environment variables.`
    );
  }

  if (err instanceof TypeError && err.message.toLowerCase().includes('fetch')) {
    return new Error(
      `Failed to connect to backend server at ${API_BASE_URL || 'http://localhost:8000'}. Please ensure the backend server is running and accessible.`
    );
  }

  return err;
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

    let res;
    try {
      res = await fetch(url.toString(), { method: 'GET', headers });
    } catch (err) {
      throw formatNetworkError(err);
    }

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

    let res;
    try {
      res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });
    } catch (err) {
      throw formatNetworkError(err);
    }

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

    let res;
    try {
      res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(body),
      });
    } catch (err) {
      throw formatNetworkError(err);
    }

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

    let res;
    try {
      res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
        headers,
      });
    } catch (err) {
      throw formatNetworkError(err);
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  async upload(endpoint, formData) {
    const authHeaders = await getAuthHeader();
    let res;
    try {
      res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          ...authHeaders,
        },
        body: formData,
      });
    } catch (err) {
      throw formatNetworkError(err);
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },
};
