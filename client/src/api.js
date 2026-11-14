/**
 * Клієнтський модуль взаємодії з HTTP API сервісу оренди обладнання (Варіант 12).
 * Побудований на обгортці XMLHttpRequest з підтримкою сесійних заголовків,
 * контролю тайм-ауту та розбору помилок у форматі Problem Details (RFC 9457).
 */

let currentSessionToken = localStorage.getItem("equiprent_session_token") || "";
let currentDemoUserId = localStorage.getItem("equiprent_demo_user_id") || "";

export function setAuthSession(token, userId) {
  currentSessionToken = token || "";
  currentDemoUserId = userId || "";
  if (currentSessionToken) {
    localStorage.setItem("equiprent_session_token", currentSessionToken);
  } else {
    localStorage.removeItem("equiprent_session_token");
  }
  if (currentDemoUserId) {
    localStorage.setItem("equiprent_demo_user_id", currentDemoUserId);
  } else {
    localStorage.removeItem("equiprent_demo_user_id");
  }
}

export function requestJson(method, url, body = null) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.timeout = 10000;
    xhr.withCredentials = true;
    xhr.setRequestHeader("Accept", "application/json");

    if (currentSessionToken) {
      xhr.setRequestHeader("X-Session-Token", currentSessionToken);
    }
    if (currentDemoUserId) {
      xhr.setRequestHeader("X-Demo-User-Id", currentDemoUserId);
    }
    if (body !== null) {
      xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    }

    xhr.onload = () => {
      let parsed = null;
      if (xhr.responseText) {
        try {
          parsed = JSON.parse(xhr.responseText);
        } catch {
          parsed = null;
        }
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(parsed);
        return;
      }

      const errorObj = {
        status: xhr.status,
        code: parsed?.code || `HTTP_${xhr.status}`,
        title: parsed?.title || "Помилка обробки запиту",
        detail: parsed?.detail || `Сервер повернув код відповіді ${xhr.status}.`,
        fieldErrors: parsed?.fieldErrors || []
      };
      reject(errorObj);
    };

    xhr.onerror = () => {
      reject({
        status: 0,
        code: "NETWORK_ERROR",
        title: "Мережева помилка",
        detail: "Не вдалося з’єднатися із сервером API. Перевірте, чи запущено бекенд.",
        fieldErrors: []
      });
    };

    xhr.ontimeout = () => {
      reject({
        status: 0,
        code: "TIMEOUT",
        title: "Перевищено час очікування",
        detail: "Сервер не відповів упродовж 10 секунд.",
        fieldErrors: []
      });
    };

    xhr.send(body !== null ? JSON.stringify(body) : null);
  });
}
