import { ReactNode } from 'react'

export interface FocoData {
  id: string
  lat: number
  lng: number
  estado: string
  tipo: string
  descripcion?: string
  foto_url?: string
  created_at: string
}

export interface MapStrategy {
  id: string
  label: string
  renderMap(props: MapRenderProps): ReactNode
}

export interface MapRenderProps {
  focos: FocoData[]
  highlightId: string | null
  centerTo: [number, number] | null
  selectedFoco: FocoData | null
  onSelectFoco: (foco: FocoData | null) => void
  onMapReady: (ref: any) => void
}
