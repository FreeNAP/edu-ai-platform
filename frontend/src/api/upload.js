import request from './index'

// kind: avatar | resume | image | video
export function uploadFile(kind, file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  return request.post(`/uploads?kind=${kind}`, form, {
    timeout: 0,
    onUploadProgress: (e) => onProgress && e.total && onProgress(Math.round((e.loaded * 100) / e.total))
  })
}
