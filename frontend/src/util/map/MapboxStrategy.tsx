import { useRef, useEffect } from 'react'
import Map, { Marker, Popup, GeolocateControl, useMap } from 'react-map-gl/mapbox'
import type { MapRef } from 'react-map-gl/mapbox'
import 'mapbox-gl/dist/mapbox-gl.css'
import type { MapStrategy, MapRenderProps, FocoData } from './MapStrategy'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN

const estadoDot = (estado: string) => {
  switch (estado.toUpperCase()) {
    case 'ACTIVO':     return '#dc2626'
    case 'PENDIENTE':  return '#d97706'
    case 'CONTROLADO': return '#f97316'
    case 'EXTINGUIDO': return '#16a34a'
    default:           return '#9ca3af'
  }
}

const tipoLabel = (tipo: string) =>
  tipo.toLowerCase() === 'forestal' ? 'Forestal' : 'Urbano'

const estadoColor = (estado: string) => {
  switch (estado.toUpperCase()) {
    case 'ACTIVO':     return 'bg-red-100 text-red-700'
    case 'PENDIENTE':  return 'bg-amber-100 text-amber-700'
    case 'CONTROLADO': return 'bg-orange-100 text-orange-700'
    case 'EXTINGUIDO': return 'bg-green-100 text-green-700'
    default:           return 'bg-gray-100 text-gray-700'
  }
}

const VALLE_DEL_SOL: [number, number] = [-33.4489, -70.6693]

function FlyToCenter({ target }: { target: [number, number] | null }) {
  const { current: map } = useMap()
  useEffect(() => {
    if (target && map) {
      map.flyTo({ center: [target[1], target[0]], zoom: 14, duration: 1500 })
    }
  }, [map, target])
  return null
}

function FocoMarker({ foco, highlight, onClick }: { foco: FocoData; highlight: boolean; onClick: () => void }) {
  if (highlight && foco.foto_url) {
    return (
      <Marker longitude={foco.lng} latitude={foco.lat} anchor="bottom" onClick={onClick}>
        <div className="relative" style={{ cursor: 'pointer' }}>
          <div className="absolute -inset-3 rounded-full bg-blue-500/30 animate-ping" />
          <div className="relative w-14 h-14 rounded-full ring-4 ring-blue-500 shadow-lg overflow-hidden bg-white">
            <img src={foco.foto_url} alt="" className="w-full h-full object-cover" />
          </div>
        </div>
      </Marker>
    )
  }
  const color = estadoDot(foco.estado)
  const size = highlight ? 44 : 32
  return (
    <Marker longitude={foco.lng} latitude={foco.lat} anchor="bottom" onClick={onClick}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        width: size, height: size, background: color, borderRadius: '50%',
        border: highlight ? '4px solid #fff' : '3px solid #fff',
        boxShadow: highlight ? '0 0 0 3px rgba(37,99,235,0.5), 0 2px 6px rgba(0,0,0,0.3)' : '0 2px 6px rgba(0,0,0,0.3)',
        cursor: 'pointer', transition: 'all 0.2s',
      }}>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width={highlight ? 20 : 16} height={highlight ? 20 : 16}>
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
        </svg>
      </div>
    </Marker>
  )
}

export class MapboxStrategy implements MapStrategy {
  id = 'mapbox'
  label = 'Mapbox'

  renderMap = (props: MapRenderProps) => {
    const MapInner = () => {
      const mapRef = useRef<MapRef>(null)

      useEffect(() => {
        if (mapRef.current) {
          props.onMapReady(mapRef.current)
        }
      }, [])

      return (
        <Map
          ref={mapRef}
          mapboxAccessToken={MAPBOX_TOKEN}
          style={{ width: '100%', height: '100%' }}
          mapStyle="mapbox://styles/mapbox/streets-v12"
          initialViewState={{
            latitude: props.centerTo ? props.centerTo[0] : VALLE_DEL_SOL[0],
            longitude: props.centerTo ? props.centerTo[1] : VALLE_DEL_SOL[1],
            zoom: props.centerTo ? 14 : 12,
          }}
          onClick={() => props.onSelectFoco(null)}
        >
          <GeolocateControl position="top-right" trackUserLocation />
          <FlyToCenter target={props.centerTo} />
          {props.focos.map((foco) => (
            <FocoMarker
              key={foco.id}
              foco={foco}
              highlight={foco.id === props.highlightId}
              onClick={() => props.onSelectFoco(foco)}
            />
          ))}
          {props.selectedFoco && (
            <Popup
              longitude={props.selectedFoco.lng}
              latitude={props.selectedFoco.lat}
              anchor="bottom"
              onClose={() => props.onSelectFoco(null)}
              closeButton={true}
              closeOnClick={false}
              offset={[0, -8]}
            >
              <div className="min-w-[180px] text-sm">
                <p className="font-semibold text-base mb-1">{tipoLabel(props.selectedFoco.tipo)}</p>
                {props.selectedFoco.descripcion && (
                  <p className="text-gray-700 mb-1 leading-tight">{props.selectedFoco.descripcion}</p>
                )}
                {props.selectedFoco.foto_url && (
                  <img src={props.selectedFoco.foto_url} alt="Foto del incendio" className="w-full h-28 object-cover rounded mt-1" loading="lazy" />
                )}
                <span className={`inline-block mt-1.5 px-2 py-0.5 rounded text-xs font-medium ${estadoColor(props.selectedFoco.estado)}`}>
                  {props.selectedFoco.estado}
                </span>
              </div>
            </Popup>
          )}
        </Map>
      )
    }
    return <MapInner />
  }
}
