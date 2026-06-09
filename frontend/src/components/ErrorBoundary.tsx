import { Component, ReactNode } from 'react'
import { Button } from './ui/Button'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
          <div className="text-center max-w-md">
            <div className="text-6xl mb-4">⚠️</div>
            <h1 className="text-xl font-bold text-gray-800 mb-2">Algo salió mal</h1>
            <p className="text-gray-600 mb-6">
              Ocurrió un error inesperado. Por favor intenta de nuevo.
            </p>
            <Button
              variant="primary"
              size="lg"
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.reload()
              }}
            >
              Reintentar
            </Button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
