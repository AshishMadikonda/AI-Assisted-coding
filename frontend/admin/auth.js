// Shared admin login for the admin pages.
// Add it to a page with: <script src="auth.js"></script> (inside <head>)

const ADMIN_API = "http://127.0.0.1:8000";
const ADMIN_KEY_NAME = "civicAdminKey";

function getAdminKey() {
  return sessionStorage.getItem(ADMIN_KEY_NAME) || "";
}

function adminLogout() {
  sessionStorage.removeItem(ADMIN_KEY_NAME);
  location.reload();
}

// Works like fetch, but also sends the admin key. If the server rejects the key, log out.
async function adminFetch(url, options) {
  const settings = Object.assign({}, options);
  settings.headers = Object.assign({}, settings.headers, { "X-Admin-Key": getAdminKey() });
  const response = await fetch(url, settings);
  if (response.status === 401) {
    sessionStorage.removeItem(ADMIN_KEY_NAME);
    location.reload();
  }
  return response;
}

// Asks the backend whether a key is correct
async function checkAdminKey(key) {
  try {
    const response = await fetch(ADMIN_API + "/admin/check", {
      headers: { "X-Admin-Key": key },
    });
    if (response.ok) return "ok";
    if (response.status === 401) return "wrong";
    if (response.status === 503) return "not-configured";
    return "error";
  } catch (error) {
    return "offline";
  }
}

const LOGIN_MESSAGES = {
  wrong: "Wrong admin key. Try again.",
  "not-configured": "The server has no admin key. Add ADMIN_KEY to the .env file and restart the backend.",
  offline: "Cannot reach the backend. Check that it is running.",
  error: "Something went wrong. Try again.",
};

function showLoginOverlay(firstMessage) {
  if (document.getElementById("adminLogin")) return; // never show two login boxes
  const overlay = document.createElement("div");
  overlay.id = "adminLogin";
  overlay.style.cssText =
    "position:fixed;inset:0;z-index:1000;background:rgba(32,41,31,0.94);" +
    "display:flex;align-items:center;justify-content:center;padding:20px;" +
    "font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;";

  const box = document.createElement("form");
  box.style.cssText =
    "background:#fff;border-radius:10px;padding:26px;max-width:380px;width:100%;color:#20291f;";

  const heading = document.createElement("h2");
  heading.textContent = "Admin login";
  heading.style.cssText = "margin:0 0 6px;font-size:22px;";

  const hint = document.createElement("p");
  hint.textContent = "Enter the admin key to manage issues and projects.";
  hint.style.cssText = "margin:0 0 16px;color:#5c6656;font-size:14px;";

  const input = document.createElement("input");
  input.type = "password";
  input.placeholder = "Admin key";
  input.autocomplete = "off";
  input.style.cssText =
    "width:100%;padding:10px;border:1px solid #c9bfa3;border-radius:6px;font:inherit;box-sizing:border-box;";

  const message = document.createElement("p");
  message.style.cssText = "min-height:20px;margin:10px 0;color:#a8412b;font-size:14px;font-weight:600;";
  message.textContent = firstMessage || "";

  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = "Log in";
  button.style.cssText =
    "width:100%;padding:11px;border:none;border-radius:6px;background:#2f6e5b;" +
    "color:#fff;font:inherit;font-weight:600;cursor:pointer;";

  box.append(heading, hint, input, message, button);
  overlay.appendChild(box);
  document.body.appendChild(overlay);
  input.focus();

  box.addEventListener("submit", async (event) => {
    event.preventDefault();
    const key = input.value.trim();
    if (!key) return;
    button.disabled = true;
    message.style.color = "#5c6656";
    message.textContent = "Checking...";

    const result = await checkAdminKey(key);
    if (result === "ok") {
      sessionStorage.setItem(ADMIN_KEY_NAME, key);
      overlay.remove();
      return;
    }
    message.style.color = "#a8412b";
    message.textContent = LOGIN_MESSAGES[result] || LOGIN_MESSAGES.error;
    button.disabled = false;
    input.select();
  });
}

// When the page opens: keep the saved key if it still works, otherwise ask for it
document.addEventListener("DOMContentLoaded", async () => {
  const saved = getAdminKey();
  if (saved) {
    const result = await checkAdminKey(saved);
    if (result === "ok") return;
    sessionStorage.removeItem(ADMIN_KEY_NAME);
    showLoginOverlay(result === "wrong" ? "Your session ended. Please log in again." : LOGIN_MESSAGES[result]);
    return;
  }
  showLoginOverlay("");
});