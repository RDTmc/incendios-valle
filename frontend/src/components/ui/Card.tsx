import { ReactNode } from 'react'

interface CardProps {
  readonly children: ReactNode
  readonly className?: string
  readonly padding?: 'none' | 'sm' | 'md' | 'lg'
  readonly shadow?: boolean
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}

export function Card({ children, className = '', padding = 'md', shadow = true }: CardProps) {
  return (
    <div
      className={`bg-white rounded-lg ${paddingStyles[padding]} ${shadow ? 'shadow' : ''} ${className}`}
    >
      {children}
    </div>
  )
}

export function CardHeader({ children, className = '' }: { readonly children: ReactNode; readonly className?: string }) {
  return <div className={`mb-3 ${className}`}>{children}</div>
}

export function CardBody({ children, className = '' }: { readonly children: ReactNode; readonly className?: string }) {
  return <div className={className}>{children}</div>
}

export function CardTitle({ children, className = '' }: { readonly children: ReactNode; readonly className?: string }) {
  return <h3 className={`font-semibold text-gray-800 ${className}`}>{children}</h3>
}
