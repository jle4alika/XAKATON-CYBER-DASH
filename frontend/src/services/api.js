import useErrorStore from '../store/errorStore'

// Базовый URL API. По умолчанию указывает на локальный backend FastAPI.
// Может быть переопределён через VITE_API_BASE_URL.
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Утилита для склейки относительного пути и базового URL.
const buildUrl = (path) => `${API_BASE}${path}`

/**
 * Универсальная функция запроса к backend API.
 *
 * Автоматически:
 * - подставляет JWT-токен из localStorage (если он есть),
 * - парсит JSON-ответ (когда установлен content-type),
 * - обрабатывает ошибки и пушит их в errorStore,
 * - при 401 сбрасывает токен и перекидывает на /login.
 */
async function request(path, options = {}) {
    // Получаем токен из localStorage
    const token = localStorage.getItem('token')

    const headers = {
        'Content-Type': 'application/json',
        ...(token ? {'Authorization': `Bearer ${token}`} : {}),
        ...(options.headers || {}),
    }

    try {
        const res = await fetch(buildUrl(path), {...options, headers})
        const contentType = res.headers.get('content-type') || ''
        const isJson = contentType.includes('application/json')
        const data = isJson ? await res.json().catch(() => null) : await res.text()

        if (!res.ok) {
            const message = (data && data.detail) || res.statusText || 'Request failed'

            // Если токен недействителен, удаляем его
            if (res.status === 401) {
                localStorage.removeItem('token')
                window.location.href = '/login'
            }

            useErrorStore.getState().pushError({source: path, message, context: {status: res.status, data}})
            throw new Error(message)
        }

        return data
    } catch (err) {
        useErrorStore.getState().pushError({
            source: path,
            message: err.message || 'Request failed',
            context: {options},
        })
        throw err
    }
}

export const getAgents = () => request('/api/agents')
export const getAgent = (id) => request(`/api/agents/${id}`)
export const getRelations = () => request('/api/relations')
export const getEvents = () => request('/api/events')
export const postEvent = (payload) =>
    request('/api/events', {method: 'POST', body: JSON.stringify(payload)})
export const postMessage = (id, payload) =>
    request(`/api/agents/${id}/message`, {method: 'POST', body: JSON.stringify(payload)})
export const postSimulationControl = (payload) =>
    request('/api/simulation/control', {method: 'POST', body: JSON.stringify(payload)})
export const createAgent = (payload) =>
    request('/api/agents', {method: 'POST', body: JSON.stringify(payload)})
export const deleteAgent = (id) =>
    request(`/api/agents/${id}`, {method: 'DELETE'})

// API calls for authentication
export const registerUser = (userData) =>
    request('/api/auth/register', {method: 'POST', body: JSON.stringify(userData)})

export const loginUser = (credentials) =>
    request('/api/auth/login', {method: 'POST', body: JSON.stringify(credentials)})

export {API_BASE}
