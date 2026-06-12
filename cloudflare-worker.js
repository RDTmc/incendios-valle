export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    // cloudflared tunnel: apunte a api.keogh.lat en lugar de IP pública
    const backend = 'https://api.keogh.lat';
    const targetPath = url.pathname;
    const targetUrl = `${backend}${targetPath}${url.search}`;

    // CORS estricto
    const ALLOWED_ORIGIN = 'https://incendios-valle.pages.dev';
    const requestOrigin = request.headers.get('Origin');
    const isAllowed = requestOrigin === ALLOWED_ORIGIN;

    const corsHeaders = new Headers();
    corsHeaders.set('Access-Control-Allow-Origin', isAllowed ? ALLOWED_ORIGIN : 'null');
    corsHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS');
    corsHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    corsHeaders.set('Vary', 'Origin');

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // Rate Limiting: 10 requests/minuto por IP en /api/login
    if (request.method === 'POST' && targetPath === '/api/login') {
      const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
      const rateKey = `rate:${clientIP}:login`;
      const current = await env.RATE_LIMITER.get(rateKey);
      const count = current ? parseInt(current) : 0;

      if (count >= 10) {
        const errorHeaders = new Headers(corsHeaders);
        errorHeaders.set('Content-Type', 'application/json');
        errorHeaders.set('Retry-After', '60');

        return new Response(JSON.stringify({ error: 'Rate limit exceeded. Try again later.' }), {
          status: 429,
          headers: errorHeaders
        });
      }

      ctx.waitUntil(env.RATE_LIMITER.put(rateKey, (count + 1).toString(), { expirationTtl: 60 }));
    }

    // Cloudflare bloquea peticiones con IP en header Host
    // No seteamos Host explícitamente; dejamos el original de la request
    const headers = new Headers(request.headers);
    // Eliminar headers que Cloudflare no permite reenviar
    headers.delete('cf-connecting-ip');
    headers.delete('cf-ray');
    headers.delete('cf-visitor');

    const fetchOptions = {
      method: request.method,
      headers: headers,
      redirect: 'follow'
    };

    if (!['GET', 'HEAD'].includes(request.method)) {
      fetchOptions.body = request.body;
    }

    try {
      const response = await fetch(targetUrl, fetchOptions);
      const responseHeaders = new Headers(response.headers);
      responseHeaders.set('Access-Control-Allow-Origin', isAllowed ? ALLOWED_ORIGIN : 'null');
      responseHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS');
      responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      responseHeaders.set('Vary', 'Origin');

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders
      });
    } catch (err) {
      return new Response(`Backend error via Worker: ${err.message}`, {
        status: 502,
        headers: corsHeaders
      });
    }
  }
};
