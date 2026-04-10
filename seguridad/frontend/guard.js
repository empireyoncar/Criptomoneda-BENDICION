(function () {
  var SEGURIDAD_API = "/CriptoBendicion/seguridad_api";

  // ── Utilidades ──────────────────────────────────────────────────────────
  function normalizeId(value) {
    return String(value || "").trim().toLowerCase();
  }

  function redirectTo(path) {
    window.location.href = path;
  }

  // Caché en memoria (dura lo que dura la pestaña abierta)
  var _meCache = null;

  // ── Leer user_id desde localStorage (legado Fase 1) ────────────────────
  function resolveUserIdLegacy() {
    return String(localStorage.getItem("user_id") || "").trim();
  }

  // ── /me con cookie HttpOnly (Fase 2) ────────────────────────────────────
  // Devuelve Promise<{user_id, fullname, email, role} | null>
  function fetchMe() {
    if (_meCache) return Promise.resolve(_meCache);
    return fetch(SEGURIDAD_API + "/me", {
      method: "GET",
      credentials: "include",
    })
      .then(function (res) {
        if (!res.ok) return null;
        return res.json();
      })
      .then(function (data) {
        if (data && data.user_id) {
          _meCache = data;
          // Sincronizar localStorage para código legado que lo lea
          localStorage.setItem("user_id", data.user_id);
          return data;
        }
        return null;
      })
      .catch(function () { return null; });
  }

  // ── requireLogin (síncrono: comprueba localStorage; también inicia /me) ─
  // La comprobación síncrona usa el localStorage ya poblado por login o por
  // una llamada previa a fetchMe().  Para una comprobación asíncrona
  // completa llama a requireLoginAsync().
  function requireLogin(options) {
    var cfg = options || {};
    var loginPath = cfg.loginPath || "/CriptoBendicion/login";
    var userId = resolveUserIdLegacy();
    if (!userId) {
      redirectTo(loginPath);
      return "";
    }
    // Disparar /me en background para refrescar el caché y la cookie
    fetchMe();
    return userId;
  }

  // requireLoginAsync – espera la verificación real con la cookie
  function requireLoginAsync(options) {
    var cfg = options || {};
    var loginPath = cfg.loginPath || "/CriptoBendicion/login";
    return fetchMe().then(function (data) {
      if (!data) {
        // Cookie expirada/ausente: limpiar localStorage y redirigir
        localStorage.removeItem("user_id");
        redirectTo(loginPath);
        return "";
      }
      return data.user_id;
    });
  }

  // ── requireAdmin ────────────────────────────────────────────────────────
  function requireAdmin(options) {
    var cfg = options || {};
    var adminLoginPath = cfg.adminLoginPath || "/CriptoBendicion/admin/login";
    var userLoginPath = cfg.userLoginPath || "/CriptoBendicion/login";
    var allowedAdminIds = (cfg.allowedAdminIds || ["001", "jonatan salazar"]).map(normalizeId);

    var userId = requireLogin({ loginPath: userLoginPath });
    if (!userId) return "";

    if (!allowedAdminIds.includes(normalizeId(userId))) {
      redirectTo(adminLoginPath);
      return "";
    }
    return userId;
  }

  function requireAdminAsync(options) {
    var cfg = options || {};
    var adminLoginPath = cfg.adminLoginPath || "/CriptoBendicion/admin/login";
    var userLoginPath = cfg.userLoginPath || "/CriptoBendicion/login";
    var allowedAdminIds = (cfg.allowedAdminIds || ["001", "jonatan salazar"]).map(normalizeId);

    return requireLoginAsync({ loginPath: userLoginPath }).then(function (userId) {
      if (!userId) return "";
      if (!allowedAdminIds.includes(normalizeId(userId))) {
        redirectTo(adminLoginPath);
        return "";
      }
      return userId;
    });
  }

  // ── Logout ──────────────────────────────────────────────────────────────
  function logout(redirectPath) {
    _meCache = null;
    localStorage.removeItem("user_id");
    return fetch(SEGURIDAD_API + "/logout", {
      method: "POST",
      credentials: "include",
    }).finally(function () {
      redirectTo(redirectPath || "/CriptoBendicion/login");
    });
  }

  // ── Login programático (para la página de login) ─────────────────────
  // Llama a seguridad_api/login y luego a usuarios_api/login para
  // mantener compatibilidad con el flujo legado mientras migra.
  function login(email, password) {
    _meCache = null;
    return fetch(SEGURIDAD_API + "/login", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email, password: password }),
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) throw new Error(data.error || "Error de autenticación");
        // Almacenar en localStorage para compatibilidad con Fase 1
        localStorage.setItem("user_id", data.user_id);
        _meCache = data;
        return data;
      });
    });
  }

  window.SEGURIDAD_GUARD = {
    requireLogin: requireLogin,
    requireLoginAsync: requireLoginAsync,
    requireAdmin: requireAdmin,
    requireAdminAsync: requireAdminAsync,
    logout: logout,
    login: login,
    me: fetchMe,
  };
})();
