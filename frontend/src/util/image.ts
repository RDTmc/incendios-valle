export function compressImage(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      loadImage(reader.result as string)
        .then(img => compressToBlob(img))
        .then(resolve)
        .catch(reject)
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsDataURL(file)
  })
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = src
  })
}

function compressToBlob(img: HTMLImageElement): Promise<Blob> {
  let { width, height } = img
  const max = 1200
  if (width > max || height > max) {
    if (width > height) {
      height = Math.round(height * max / width)
      width = max
    } else {
      width = Math.round(width * max / height)
      height = max
    }
  }
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')!
  ctx.drawImage(img, 0, 0, width, height)
  return new Promise((resolve, reject) => {
    canvas.toBlob(blob => {
      if (blob) resolve(blob)
      else reject(new Error('Canvas toBlob failed'))
    }, 'image/jpeg', 0.75)
  })
}