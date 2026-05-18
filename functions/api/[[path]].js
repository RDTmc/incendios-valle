export async function onRequest({ request, params }) {
  const url = new URL(request.url);
  const backend = 'http://3.227.186.158';

  // Keep path exactly as is (/api/login) - NO stripping
  // Nginx already handles the /api/ prefix stripping
  const targetPath = url.pathname;
  const targetUrl = `${backend}${targetPath}${url.search}`;

  const headers = new Headers(request.headers);
  headers.set('Host', '3.227.186.158');

  const options = {
    method: request.method,
    headers: headers,
    redirect: 'follow'
  };

  if (!['GET', 'HEAD'].includes(request.method)) {
    options.body = request.body;
  }

  try {
    const response = await fetch(targetUrl, options);

    const newHeaders = new Headers(response.headers);
    newHeaders.set('Access-Control-Allow-Origin', '*');
    newHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    newHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: newHeaders });
    }

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders
    });

  } catch (err) {
    return new Response(`Backend error: ${err.message}`, { status: 502 });
  }
}