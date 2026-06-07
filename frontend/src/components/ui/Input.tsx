import { InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`w-full px-4 py-2 border ${error ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent bg-gray-900 text-white placeholder-gray-400 ${className}`}
          {...props}
        />
        {error && (
          <p className="text-red-500 text-xs mt-1">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
