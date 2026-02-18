import {create} from 'zustand'
import {getAgent, getAgents, getRelations, deleteAgent} from '../services/api'

// Мок-данные агентов и отношений используются в оффлайн-режиме
// или если API недоступен. Это позволяет спокойно разрабатывать UI.
const fallbackAgents = [
    {
        id: 'alice',
        name: 'Alice',
        mood: 0.82,
        energy: 78,
        memories: [
            {description: 'Met Bob', emotion: 'positive', timestamp: new Date().toISOString()},
            {description: 'Was insulted by Eve', emotion: 'negative', timestamp: new Date().toISOString()},
        ],
        plans: [{title: 'Explore the plaza', status: 'active'}],
        interactions: [{with: 'Bob', description: 'Chatted about treasure', timestamp: new Date().toISOString()}],
    },
    {
        id: 'bob',
        name: 'Bob',
        mood: 0.55,
        energy: 64,
        memories: [{description: 'Replied to Alice happily', emotion: 'positive', timestamp: new Date().toISOString()}],
        plans: [{title: 'Guard the camp', status: 'planned'}],
        interactions: [],
    },
    {
        id: 'eve',
        name: 'Eve',
        mood: 0.2,
        energy: 42,
        memories: [{description: 'Insulted Alice', emotion: 'negative', timestamp: new Date().toISOString()}],
        plans: [{title: 'Collect intel', status: 'in-progress'}],
        interactions: [],
    },
]

const fallbackRelations = [
    {source: 'alice', target: 'bob', affinity: 0.78},
    {source: 'bob', target: 'eve', affinity: -0.45},
    {source: 'alice', target: 'eve', affinity: -0.62},
]

/**
 * Zustand-стор, отвечающий за состояние агентов и их отношений.
 *
 * Хранит:
 * - список агентов и отношений,
 * - выбранного агента (для детального просмотра),
 * - флаги загрузки + текст ошибки.
 * Также инкапсулирует работу с API и fallback на локальные данные.
 */
const useAgentStore = create((set, get) => ({
    agents: [],
    relations: [],
    selectedAgent: null,
    loading: false,
    error: null,
    fetchAgents: async () => {
        set({loading: true, error: null})
        try {
            const data = await getAgents()
            set({agents: data || []})
        } catch (err) {
            console.warn('Falling back to mock agents', err)
            set({agents: fallbackAgents, error: 'Оффлайн режим: мок-агенты'})
        } finally {
            set({loading: false})
        }
    },
    fetchAgentById: async (id) => {
        set({loading: true, error: null})
        try {
            const data = await getAgent(id)
            console.log('Agent data received:', data)
            console.log('Plans in data:', data?.plans)
            set({selectedAgent: data})
        } catch (err) {
            const local = get().agents.find((a) => `${a.id}` === `${id}`) || fallbackAgents.find((a) => `${a.id}` === `${id}`)
            set({selectedAgent: local || null, error: err.message || 'Failed to load agent'})
        } finally {
            set({loading: false})
        }
    },
    fetchRelations: async () => {
        set({loading: true, error: null})
        try {
            const data = await getRelations()
            set({relations: data || []})
        } catch (err) {
            console.warn('Falling back to mock relations', err)
            set({relations: fallbackRelations, error: 'Оффлайн режим: мок-отношения'})
        } finally {
            set({loading: false})
        }
    },
    updateAgentFromEvent: (partial) => {
        if (!partial?.id) return
        set((state) => {
            const agents = state.agents.map((agent) => (agent.id === partial.id ? {...agent, ...partial} : agent))
            const selectedAgent =
                state.selectedAgent && state.selectedAgent.id === partial.id
                    ? {...state.selectedAgent, ...partial}
                    : state.selectedAgent
            return {agents, selectedAgent}
        })
    },
    setRelations: (relations) => set({relations: relations || []}),
    deleteAgent: async (id) => {
        set({loading: true, error: null})
        try {
            await deleteAgent(id)
            // Удаляем агента из состояния
            set((state) => ({
                agents: state.agents.filter((agent) => agent.id !== id),
                selectedAgent: state.selectedAgent?.id === id ? null : state.selectedAgent,
            }))
        } catch (err) {
            set({error: err.message || 'Failed to delete agent'})
            throw err
        } finally {
            set({loading: false})
        }
    },
}))

export default useAgentStore

