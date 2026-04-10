(function () {
  function normalizeId(value) {
    return String(value || "").trim().toLowerCase();
  }

  function resolveUserId() {
    return String(localStorage.getItem("user_id") || "").trim();
  }

  function redirectTo(path) {
    window.location.href = path;
  }

  function requireLogin(options) {
    var cfg = options || {};
    var loginPath = cfg.loginPath || "/CriptoBendicion/login";
    var userId = resolveUserId();
    if (!userId) {
      redirectTo(loginPath);
      return "";
    }
    return userId;
  }

  function requireAdmin(options) {
    var cfg = options || {};
    var adminLoginPath = cfg.adminLoginPath || "/CriptoBendicion/admin/login";
    var userLoginPath = cfg.userLoginPath || "/CriptoBendicion/login";
    var allowedAdminIds = (cfg.allowedAdminIds || ["001", "jonatan salazar"]).map(normalizeId);

    var userId = requireLogin({ loginPath: userLoginPath });
    if (!userId) {
      return "";
    }

    if (!allowedAdminIds.includes(normalizeId(userId))) {
      redirectTo(adminLoginPath);
      return "";
    }

    return userId;
  }

  window.SEGURIDAD_GUARD = {
    requireLogin: requireLogin,
    requireAdmin: requireAdmin,
  };
})();
