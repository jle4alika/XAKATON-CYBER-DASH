import {create} from 'zustand'
import {getEvents} from '../services/api'

// Максимальное количество событий в ленте — старые записи "съезжают" в историю.
const MAX_EVENTS = 200

// Пока мок-события не используются, но оставлены для возможного оффлайн-режима.
const fallbackEvents = []

/**
 * Zustand-стор для ленты событий симуляции.
 *
 * Умеет:
 * - подгружать последние события с API,
 * - аккуратно добавлять новые события в конец (realtime-стрим),
 * - ограничивать размер ленты до MAX_EVENTS.
 */
const useEventStore = create((set) => ({
    events: [],
    loading: false,
    error: null,
    fetchEvents: async () => {
        set({loading: true, error: null})
        try {
            const data = await getEvents()
            set({events: Array.isArray(data) ? data.slice(-MAX_EVENTS) : []})
        } catch (err) {
            console.warn('Falling back to mock events', err)
            set({events: fallbackEvents})
        } finally {
            set({loading: false})
        }
    },
    addEvent: (event) =>
        set((state) => {
            const next = [...state.events, event].slice(-MAX_EVENTS)
            return {events: next}
        }),
}))

export default useEventStore

