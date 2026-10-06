/* Frame28 · /instalar: qué sistema usa el visitante, solo en su navegador (nada se envía a ningún servidor, sin cookies).
   detectOS(ua, platform, uaDataPlatform, uaDataMobile) → { os: "win" | "mac" | "linux" | null, name, mobile }
   - os: la pestaña que se abre por defecto; null si no se reconoce.
   - mobile: true en un teléfono o una tableta (Frame28 se instala en un ordenador). */
(function (root) {
  function detectOS(ua, platform, uaDataPlatform, uaDataMobile) {
    ua = ua || ""; platform = platform || ""; var p = (uaDataPlatform || "").toLowerCase();
    var iPadOS = /Macintosh/.test(ua) && /Mobile\//.test(ua);           // el iPad se presenta como Mac
    var mobile = !!uaDataMobile || /Android|iPhone|iPod|iPad|Mobile Safari|Windows Phone/.test(ua) || iPadOS;
    if (p === "android" || /Android/.test(ua)) return { os: null, name: "Android", mobile: true };
    if (p === "ios" || /iPhone|iPod|iPad/.test(ua) || iPadOS) return { os: null, name: "iOS", mobile: true };
    if (p === "windows" || /Win/.test(platform) || /Windows NT/.test(ua)) return { os: "win", name: "Windows", mobile: mobile };
    if (p === "macos" || /Mac/.test(platform) || /Macintosh|Mac OS X/.test(ua)) return { os: "mac", name: "macOS", mobile: mobile };
    if (p === "chrome os" || p === "chromeos" || /CrOS/.test(ua)) return { os: "linux", name: "ChromeOS (Linux)", mobile: mobile };
    if (p === "linux" || /Linux|X11/.test(platform + " " + ua)) return { os: "linux", name: "Linux", mobile: mobile };
    return { os: null, name: "", mobile: mobile };
  }
  root.F28detectOS = detectOS;
  if (typeof module !== "undefined") module.exports = { detectOS: detectOS };
})(typeof window !== "undefined" ? window : globalThis);
