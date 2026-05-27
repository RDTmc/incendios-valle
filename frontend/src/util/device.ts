const STORAGE_KEY = 'incendios_device_id'

function generateUUID(): string {
  return crypto.randomUUID
    ? crypto.randomUUID()
    : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0
        const v = c === 'x' ? r : (r & 0x3) | 0x8
        return v.toString(16)
      })
}

export function getDeviceId(): string {
  let id = localStorage.getItem(STORAGE_KEY)
  if (id) return id
  id = generateUUID()
  localStorage.setItem(STORAGE_KEY, id)
  return id
}
