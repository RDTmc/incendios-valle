export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);

  // 1. Validar que la ruta comience con /api/
  if (!url.pathname.startsWith('/api/')) {
    return new Response('Not Found', { status: 404 });
  }

  // 2. Construir la URL destino hacia la EC2 de AWS
  const backendUrl = `http://3.227.186.158${url.pathname}${url.search}`;

  // 3. Clonar y ajustar las cabeceras
  const headers = new Headers(request.headers);
  headers.set('Host', '3.227.186.158');

  // 4. Configurar las opciones de la petición de forma segura
  const fetchOptions = {
    method: request.method,
    headers: headers,
    redirect: 'follow'
  };

  // Solo añade el cuerpo si NO es un método GET o HEAD
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    fetchOptions.body = request.body;
  }

  try {
    // 5. Realizar la petición real al backend en AWS
    const response = await fetch(backendUrl, fetchOptions);

    // 6. Clonar la respuesta para poder modificar cabeceras de CORS
    const newHeaders = new Headers(response.headers);
    
    newHeaders.set('Access-Control-Allow-Origin', '*');
    newHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, POST, PUT, DELETE, OPTIONS');
    newHeaders.set('Access-Control-Allow-Headers', '*');

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders
    });

  } catch (err) {
    return new Response(`Backend unavailable: ${err.message}`, { status: 502 });
  }
}