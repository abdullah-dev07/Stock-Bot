import API_BASE_URL from '../config';

function getToken() {
  return localStorage.getItem('stockbot_token');
}

function getRefreshToken() {
  return localStorage.getItem('stockbot_refresh_token');
}

export function setTokens(accessToken, refreshToken) {
  localStorage.setItem('stockbot_token', accessToken);
  if (refreshToken) {
    localStorage.setItem('stockbot_refresh_token', refreshToken);
  }
}

export function clearTokens() {
  localStorage.removeItem('stockbot_token');
  localStorage.removeItem('stockbot_refresh_token');
}

export function hasAuthTokens() {
  return !!(getToken() || getRefreshToken());
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

export async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let response = await fetch(`${API_BASE_URL}${url}`, { ...options, headers });

  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${getToken()}`;
      response = await fetch(`${API_BASE_URL}${url}`, { ...options, headers });
    }
    if (response.status === 401) {
      clearTokens();
      window.location.href = '/login';
    }
  }

  return response;
}
