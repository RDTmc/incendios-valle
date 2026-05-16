export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Only proxy /api/* requests
    if (!url.pathname.startsWith('/api/')) {
      return new Response('Not Found', { status: 404 });
    }

    // Forward to EC2 backend
    const backendUrl = `http://3.227.186.158${url.pathname}${url.search}`;

    const headers = new Headers(request.headers);
    headers.set('Host', '3.227.186.158');

    try {
      const response = await fetch(backendUrl, {
        method: request.method,
        headers: headers,
        body: request.body,
        redirect: 'follow'
      });

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers
      });
    } catch (err) {
      return new Response('Backend unavailable', { status: 502 });
    }
  }
};