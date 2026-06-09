import { describe, it, expect, vi, beforeEach } from 'vitest'

const STORAGE_KEY = 'incendios_device_id'

beforeEach(() => {
  localStorage.clear()
})

describe('getDeviceId', () => {
  it('should generate and store a new device id', async () => {
    const { getDeviceId } = await import('../util/device')
    const id = getDeviceId()
    expect(id).toMatch(/^[0-9a-f-]+$/)
    expect(localStorage.getItem(STORAGE_KEY)).toBe(id)
  })

  it('should return existing device id from storage', async () => {
    const existingId = crypto.randomUUID()
    localStorage.setItem(STORAGE_KEY, existingId)
    const { getDeviceId } = await import('../util/device')
    const id = getDeviceId()
    expect(id).toBe(existingId)
  })

  it('should return same id on multiple calls', async () => {
    const { getDeviceId } = await import('../util/device')
    const first = getDeviceId()
    const second = getDeviceId()
    expect(first).toBe(second)
  })

  it('falls back to manual UUID when crypto.randomUUID is undefined', async () => {
    const originalRandomUUID = crypto.randomUUID
    ;(crypto as any).randomUUID = undefined
    const { getDeviceId } = await import('../util/device')
    const id = getDeviceId()
    expect(id).toMatch(/^[0-9a-f-]+$/)
    expect(id.length).toBeGreaterThan(30)
    ;(crypto as any).randomUUID = originalRandomUUID
  })
})
