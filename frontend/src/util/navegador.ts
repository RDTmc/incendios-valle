// Detector de navegador embebido (in-app browser)
// Identifica visores internos de escáneres QR, Facebook, Instagram, etc.

const AGENTES_EMBEBIDOS = [
  { nombre: 'Facebook',    pat: /FBAN|FBAV|MESSENGER/i },
  { nombre: 'Instagram',   pat: /Instagram/i },
  { nombre: 'Twitter/X',   pat: /Twitter|Tweetbot/i },
  { nombre: 'LinkedIn',    pat: /LinkedIn/i },
  { nombre: 'TikTok',      pat: /TikTok|musical_ly/i },
  { nombre: 'Snapchat',    pat: /Snapchat/i },
  { nombre: 'Gmail',       pat: /com\.google\.android\.gm/i },
  { nombre: 'WebView',     pat: /wv|WebView/i },
  { nombre: 'Escáner QR',  pat: /QRScanner|Scan|BarCode/i },
]

function obtenerUa(): string {
  return navigator.userAgent || ''
}

export function detectarNavegadorEmbebido(): string | null {
  const ua = obtenerUa()
  for (const agente of AGENTES_EMBEBIDOS) {
    if (agente.pat.test(ua)) return agente.nombre
  }
  return null
}

export function esNavegadorInstalable(): boolean {
  // Ya instalada como PWA
  if (globalThis.matchMedia('(display-mode: standalone)').matches) return true
  if ((navigator as any).standalone) return true
  return false
}
