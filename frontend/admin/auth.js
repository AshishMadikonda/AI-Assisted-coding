
const ADMIN_KEY_STORAGE = "civic_admin_key";

// Read the saved key when an admin page makes an API request.
function getAdminKey() {
  return sessionStorage.getItem(ADMIN_KEY_STORAGE) || "";
}

// Save the key for this browser tab/session.
function setAdminKey(key) {
  if (key && key.trim()) {
    sessionStorage.setItem(ADMIN_KEY_STORAGE, key.trim());
  }
}

// Remove the saved key when logging out.
function clearAdminKey() {
  sessionStorage.removeItem(ADMIN_KEY_STORAGE);
}

// Add the authentication header to requests sent to the API.
function adminHeaders(extraHeaders = {}) {
  return {
    ...extraHeaders,
    "X-Admin-Key": getAdminKey(),
  };
}


async function adminFetch(url, options = {}) {
  const headers = adminHeaders(options.headers || {});

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearAdminKey();
  }

  return response;
}
