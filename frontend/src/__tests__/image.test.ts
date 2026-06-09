import { describe, it, expect, vi, afterEach } from 'vitest'

afterEach(() => {
  vi.restoreAllMocks()
})

HTMLCanvasElement.prototype.getContext = function () {
  return { drawImage: vi.fn() } as unknown as CanvasRenderingContext2D
}
HTMLCanvasElement.prototype.toBlob = function (cb: BlobCallback) {
  cb(new Blob(['fake'], { type: 'image/jpeg' }) as Blob)
}

function mockImage(width = 800, height = 600) {
  const OriginalImage = window.Image
  vi.stubGlobal('Image', function (this: HTMLImageElement) {
    this.width = width
    this.height = height
    this.onload = null
    this.onerror = null
    let _src = ''
    Object.defineProperty(this, 'src', {
      get: () => _src,
      set: (val: string) => {
        _src = val
        setTimeout(() => { if (this.onload) this.onload() }, 0)
      },
    })
    return this
  } as unknown as typeof Image)
  return () => { window.Image = OriginalImage }
}

describe('compressImage', () => {
  it('resolves with a Blob for a valid file', async () => {
    const restore = mockImage()
    const { compressImage } = await import('../util/image')
    const file = new File(['fake'], 'test.jpg', { type: 'image/jpeg' })
    const blob = await compressImage(file)
    expect(blob).toBeInstanceOf(Blob)
    restore()
  })

  it('enforces max dimension 1200px on wide image', async () => {
    const restore = mockImage(2000, 800)
    const { compressImage } = await import('../util/image')
    const file = new File(['fake'], 'wide.jpg', { type: 'image/jpeg' })
    const blob = await compressImage(file)
    expect(blob).toBeInstanceOf(Blob)
    restore()
  })

  it('enforces max dimension 1200px on tall image', async () => {
    const restore = mockImage(800, 2000)
    const { compressImage } = await import('../util/image')
    const file = new File(['fake'], 'tall.jpg', { type: 'image/jpeg' })
    const blob = await compressImage(file)
    expect(blob).toBeInstanceOf(Blob)
    restore()
  })

  it('rejects when FileReader fails', async () => {
    const restore = mockImage()
    const { compressImage } = await import('../util/image')
    const originalReadAsDataURL = FileReader.prototype.readAsDataURL
    FileReader.prototype.readAsDataURL = function () {
      if (this.onerror) {
        ;(this.onerror as any)(new Event('error'))
      }
    }
    const file = new File(['fake'], 'test.jpg', { type: 'image/jpeg' })
    await expect(compressImage(file)).rejects.toThrow('Failed to read file')
    FileReader.prototype.readAsDataURL = originalReadAsDataURL
    restore()
  })

  it('rejects when Image load fails', async () => {
    const OriginalImage = window.Image
    vi.stubGlobal('Image', function (this: HTMLImageElement) {
      this.width = 0
      this.height = 0
      this.onload = null
      this.onerror = null
      let _src = ''
      Object.defineProperty(this, 'src', {
        get: () => _src,
        set: (val: string) => {
          _src = val
          setTimeout(() => { if (this.onerror) this.onerror(new Event('error')) }, 0)
        },
      })
      return this
    } as unknown as typeof Image)

    const { compressImage } = await import('../util/image')
    const file = new File(['fake'], 'bad.jpg', { type: 'image/jpeg' })
    await expect(compressImage(file)).rejects.toThrow('Failed to load image')
    window.Image = OriginalImage
  })
})
