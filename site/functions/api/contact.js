/**
 * POST /api/contact · formulario de frame28.app (Cloudflare Pages Function).
 *
 * Recibe JSON (fetch desde la página) o un formulario normal (sin JS), valida, corta el spam básico (honeypot,
 * tamaño) y envía un email a MAIL_TO con el binding `send_email` de Cloudflare (Email Workers / Email Service):
 *   - wrangler.toml: [[send_email]] name = "SEND_EMAIL"  (ver site/wrangler.toml y site/README.md)
 *   - variables: MAIL_FROM (remitente verificado en el dominio frame28.app), MAIL_TO (buzón que recibe)
 * Si el binding no existe (previsualización local sin email), responde ok y escribe el mensaje en el log, para
 * poder probar la página sin desplegar el correo.
 *
 * [[verificar en el despliegue]]: el API de Email Service de Cloudflare está en evolución; si el binding cambia de
 * forma, solo hay que tocar `sendMail`.
 */
import { EmailMessage } from "cloudflare:email";

const MAX = { name: 120, email: 200, brand: 200, video: 500, message: 4000 };

export async function onRequestPost({ request, env }) {
  const wantsJson = (request.headers.get("accept") || "").includes("application/json");
  let data;
  try {
    data = (request.headers.get("content-type") || "").includes("application/json")
      ? await request.json()
      : Object.fromEntries((await request.formData()).entries());
  } catch {
    return reply(wantsJson, 400, { ok: false, error: "bad_request" }, data);
  }
  const lang = data.lang === "en" ? "en" : "es";
  // honeypot: un humano no rellena "website"
  if (data.website) return reply(wantsJson, 200, { ok: true }, data, lang);
  const clean = {};
  for (const [k, max] of Object.entries(MAX)) clean[k] = String(data[k] || "").trim().slice(0, max);
  clean.interest = String(data.interest || "").slice(0, 20);
  clean.page = String(data.page || "").slice(0, 200);
  if (!clean.name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(clean.email)) {
    return reply(wantsJson, 422, { ok: false, error: "invalid" }, data, lang);
  }
  const ip = request.headers.get("cf-connecting-ip") || "";
  const country = request.headers.get("cf-ipcountry") || "";
  const subject = `[frame28.app] ${clean.interest || "contacto"} · ${clean.brand || clean.name}`;
  const text = [
    `Nombre: ${clean.name}`, `Email: ${clean.email}`, `Marca/web: ${clean.brand}`, `Interés: ${clean.interest}`,
    `Vídeo: ${clean.video}`, `Idioma: ${lang}`, `Página: ${clean.page}`, `País: ${country} · IP: ${ip}`, "",
    clean.message || "(sin mensaje)",
  ].join("\n");
  try {
    await sendMail(env, { subject, text, replyTo: clean.email });
  } catch (err) {
    console.error("contact: no se pudo enviar", err);
    return reply(wantsJson, 502, { ok: false, error: "send_failed" }, data, lang);
  }
  return reply(wantsJson, 200, { ok: true }, data, lang);
}

export function onRequestGet() {
  return new Response("Method not allowed", { status: 405, headers: { allow: "POST" } });
}

async function sendMail(env, { subject, text, replyTo }) {
  const from = env.MAIL_FROM || "hola@frame28.app";
  const to = env.MAIL_TO || "hola@frame28.app";
  if (!env.SEND_EMAIL) {
    console.log("contact (sin binding SEND_EMAIL):", subject, "\n" + text);
    return;
  }
  const raw = [
    `From: Frame28 <${from}>`, `To: ${to}`, `Reply-To: ${replyTo}`, `Subject: ${encodeSubject(subject)}`,
    `Date: ${new Date().toUTCString()}`, `Message-ID: <${crypto.randomUUID()}@frame28.app>`,
    "MIME-Version: 1.0", "Content-Type: text/plain; charset=utf-8", "Content-Transfer-Encoding: base64", "",
    base64(text),
  ].join("\r\n");
  await env.SEND_EMAIL.send(new EmailMessage(from, to, raw));
}

function encodeSubject(s) {
  return /^[\x20-\x7e]*$/.test(s) ? s : `=?utf-8?B?${base64(s)}?=`;
}

function base64(s) {
  const bytes = new TextEncoder().encode(s);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin);
}

function reply(wantsJson, status, body, data, lang = "es") {
  if (wantsJson) {
    return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8" } });
  }
  // sin JS: volver a la página de contacto con el resultado en la URL (la página lo muestra)
  const back = lang === "en" ? "/en/contact/" : "/contacto/";
  const q = body.ok ? "ok=1" : "error=1";
  return Response.redirect(new URL(`${back}?${q}`, "https://frame28.app").toString(), 303);
}
