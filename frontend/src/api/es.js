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
  return request.post(`/es/indexes/${encodeURIComponent(index)}/export.do`, params, { responseType: 'blob' })
}

export function importExcel(formData) {
  return request.post('/es/indexes/import.do', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
