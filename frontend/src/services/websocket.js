import {API_BASE} from './api'
import useErrorStore from '../store/errorStore'

// Базовый URL для WebSocket-подключения.
// Можно переопределить через VITE_WS_BASE_URL, иначе строится из API_BASE или window.location.
const wsBase =
    import.meta.env.VITE_WS_BASE_URL ||
    (API_BASE.startsWith('http')
        ? API_BASE.replace('http', 'ws')
        : typeof window !== 'undefined'
            ? `ws://${window.location.host}`
            : 'ws://localhost:8000')

/**
 * Подключение к стриму событий симуляции по WebSocket.
 *
 * onMessage — колбэк, который получает каждое входящее сообщение (уже распарсенный JSON).
 * opts.onStatus — необязательный колбэк статуса ('connected' | 'disconnected' | 'error').
 * Возвращает объект с методом close() для ручного закрытия соединения.
 */
export function connectEventStream(onMessage, opts = {}) {
    let socket = null
    let alive = true

    const connect = () => {
        socket = new WebSocket(`${wsBase}/ws/events`)

        socket.onopen = () => {
            opts.onStatus?.('connected')
        }

        socket.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data)
                onMessage?.(payload)
            } catch (e) {
                console.warn('WS parse error', e)
                useErrorStore.getState().pushError({source: 'ws:onmessage', message: e.message})
            }
        }

        socket.onclose = () => {
            opts.onStatus?.('disconnected')
            if (alive) {
                useErrorStore.getState().pushError({source: 'ws:onclose', message: 'WebSocket closed'})
                // Простая авто-реконнект-логика с задержкой
                setTimeout(connect, 2000)
            }
        }

        socket.onerror = () => {
            opts.onStatus?.('error')
            useErrorStore.getState().pushError({source: 'ws:onerror', message: 'WebSocket error'})
            socket?.close()
        }
    }

    connect()

    return {
        close: () => {
            alive = false
            socket?.close()
        },
    }
}

 