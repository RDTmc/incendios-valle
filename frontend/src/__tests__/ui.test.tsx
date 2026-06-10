import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardHeader, CardBody, CardTitle } from '../components/ui/Card'

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeDefined()
  })

  it('applies variant classes', () => {
    const { container } = render(<Button variant="danger">Delete</Button>)
    const btn = container.querySelector('button')
    expect(btn?.className).toContain('bg-red-600')
  })

  it('applies size classes', () => {
    const { container } = render(<Button size="lg">Large</Button>)
    const btn = container.querySelector('button')
    expect(btn?.className).toContain('text-base')
  })

  it('shows loading spinner when loading', () => {
    const { container } = render(<Button loading>Loading</Button>)
    expect(container.querySelector('.animate-spin')).toBeDefined()
  })

  it('is disabled when loading', () => {
    const { container } = render(<Button loading>Loading</Button>)
    const btn = container.querySelector('button')
    expect(btn?.disabled).toBe(true)
  })

  it('is disabled when disabled prop is set', () => {
    const { container } = render(<Button disabled>Disabled</Button>)
    const btn = container.querySelector('button')
    expect(btn?.disabled).toBe(true)
  })

  it('renders icon when not loading', () => {
    render(<Button icon={<span data-testid="icon">🔥</span>}>Icon</Button>)
    expect(screen.getByTestId('icon')).toBeDefined()
  })

  it('hides icon when loading', () => {
    const { container } = render(<Button loading icon={<span data-testid="icon">🔥</span>}>Load</Button>)
    expect(container.querySelector('.animate-spin')).toBeDefined()
    expect(screen.queryByTestId('icon')).toBeNull()
  })
})

describe('Input', () => {
  it('renders input element', () => {
    const { container } = render(<Input />)
    expect(container.querySelector('input')).toBeDefined()
  })

  it('renders label when provided', () => {
    render(<Input label="Email" />)
    expect(screen.getByText('Email')).toBeDefined()
  })

  it('does not render label by default', () => {
    const { container } = render(<Input />)
    expect(container.querySelector('label')).toBeNull()
  })

  it('renders error message when provided', () => {
    render(<Input error="Campo requerido" />)
    expect(screen.getByText('Campo requerido')).toBeDefined()
  })

  it('applies error border style', () => {
    const { container } = render(<Input error="Error" />)
    const input = container.querySelector('input')
    expect(input?.className).toContain('border-red-500')
  })

  it('forwards ref', () => {
    const ref = { current: null }
    render(<Input ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })

  it('passes placeholder prop', () => {
    render(<Input placeholder="test@test.cl" />)
    expect(screen.getByPlaceholderText('test@test.cl')).toBeDefined()
  })
})

describe('Card', () => {
  it('renders children', () => {
    render(<Card><p>content</p></Card>)
    expect(screen.getByText('content')).toBeDefined()
  })

  it('applies padding styles', () => {
    const { container } = render(<Card padding="sm">Small</Card>)
    const div = container.querySelector('.rounded-lg')
    expect(div?.className).toContain('p-3')
  })

  it('applies shadow by default', () => {
    const { container } = render(<Card>Shadow</Card>)
    const div = container.querySelector('.rounded-lg')
    expect(div?.className).toContain('shadow')
  })

  it('removes shadow when shadow=false', () => {
    const { container } = render(<Card shadow={false}>No shadow</Card>)
    const div = container.querySelector('.rounded-lg')
    expect(div?.className).not.toContain('shadow')
  })
})

describe('CardHeader', () => {
  it('renders children', () => {
    render(<CardHeader><h2>Header</h2></CardHeader>)
    expect(screen.getByText('Header')).toBeDefined()
  })
})

describe('CardBody', () => {
  it('renders children', () => {
    render(<CardBody><p>Body</p></CardBody>)
    expect(screen.getByText('Body')).toBeDefined()
  })
})

describe('CardTitle', () => {
  it('renders children', () => {
    render(<CardTitle>Title</CardTitle>)
    expect(screen.getByText('Title')).toBeDefined()
  })
})
