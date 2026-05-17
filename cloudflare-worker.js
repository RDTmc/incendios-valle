export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 1. Definir la IP de tu AWS EC2 backend (Puerto 80 de Nginx)
    const backend = 'http://3.227.186.158';
    
    // 2. Mantener el prefijo /api intacto porque Nginx lo requiere para redirigir a FastAPI
    const targetPath = url.pathname;
    const targetUrl = `${backend}${targetPath}${url.search}`;

    // 3. Configurar cabeceras base para CORS global
    const corsHeaders = new Headers();
    corsHeaders.set('Access-Control-Allow-Origin', '*');
    corsHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, POST, PUT, DELETE, OPTIONS');
    corsHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    // 4. INTERCEPTACIÓN CRÍTICA: Manejar el Preflight OPTIONS de inmediato sin tocar AWS
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }
    
    // 5. Clonar las cabeceras originales de la petición y ajustar el Host para AWS
    const headers = new Headers(request.headers);
    headers.set('Host', '3.227.186.158');
    
    // 6. Configurar las opciones del fetch de forma segura
    const fetchOptions = {
      method: request.method,
      headers: headers,
      redirect: 'follow'
    };
    
    // Evitar adjuntar body en métodos que la especificación de red prohíbe (GET/HEAD)
    if (!['GET', 'HEAD'].includes(request.method)) {
      fetchOptions.body = request.body;
    }
    
    try {
      // 7. Enviar la petición real al backend en AWS
      const response = await fetch(targetUrl, fetchOptions);
      
      // 8. Clonar las cabeceras que vengan de AWS y fusionar las de CORS
      const responseHeaders = new Headers(response.headers);
      responseHeaders.set('Access-Control-Allow-Origin', '*');
      responseHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, POST, PUT, DELETE, OPTIONS');
      responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders
      });
      
    } catch (err) {
      // Retornar error de pasarela con cabeceras CORS activas para que el frontend pueda leer el texto
      return new Response(`Backend error via Worker: ${err.message}`, { 
        status: 502,
        headers: corsHeaders
      });
    }
  }
};