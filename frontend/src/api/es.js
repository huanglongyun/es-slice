import request from '@/utils/request'

export function getIndexes() {
  return request.get('/es/indexes.do')
}

export function getIndexFields(index) {
  return request.get(`/es/indexes/${encodeURIComponent(index)}/fields.do`)
}

export function searchDocs(index, params) {
  return request.post(`/es/indexes/${encodeURIComponent(index)}/search.do`, params)
}

export function getDoc(index, docId) {
  return request.get(`/es/indexes/${encodeURIComponent(index)}/doc/${encodeURIComponent(docId)}.do`)
}

export function updateDoc(index, docId, body) {
  return request.put(`/es/indexes/${encodeURIComponent(index)}/doc/${encodeURIComponent(docId)}.do`, body)
}

export function deleteDoc(index, docId) {
  return request.delete(`/es/indexes/${encodeURIComponent(index)}/doc/${encodeURIComponent(docId)}.do`)
}

export function exportDocs(index, params) {
  const token = localStorage.getItem('token')
  return request.post(`/es/indexes/${encodeURIComponent(index)}/export.do`, params, {
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  }).then(res => res).catch(e => {
    // blob 错误响应需要特殊处理
    if (e.response?.data instanceof Blob) {
      return e.response.data.text().then(t => {
        try { const err = JSON.parse(t); throw new Error(err.message || '导出失败') }
        catch (_) { throw new Error('导出失败') }
      })
    }
    throw e
  })
}

export function importExcel(formData) {
  return request.post('/es/indexes/import.do', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
