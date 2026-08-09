// TTM stack configuration. The %...% placeholders are replaced at build time
// (build.sh) from Vercel environment variables SUPABASE_URL and
// SUPABASE_ANON_KEY. Unreplaced or empty values → the stack runs in local-only
// mode: the gate stores the visitor in localStorage, telemetry logs to console,
// and the admin panel says so. Nothing breaks without Supabase.
window.TTM_CONFIG = (function () {
  var url = '%SUPABASE_URL%';
  var key = '%SUPABASE_ANON_KEY%';
  var unset = function (v) { return !v || v.indexOf('%') === 0; };
  return {
    supabaseUrl: unset(url) ? '' : url,
    supabaseAnonKey: unset(key) ? '' : key,
    defaultTheme: 'ttm', // site default: 'ttm' | 'terminal' | '' (zine)
  };
})();
