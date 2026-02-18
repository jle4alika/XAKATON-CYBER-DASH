import { create } from 'zustand'
import { pauseSimulation, resumeSimulation, setSimulationSpeed } from '../services/simulation'

/**
 * Zustand-стор для управления симуляцией времени.
 *
 * Инкапсулирует вызовы backend API:
 * - изменение скорости симуляции,
 * - постановка на паузу и возобновление.
 * Также хранит небольшой текстовый статус для UI.
 */
const useSimulationStore = create((set, get) => ({
  speed: 1,
  isPaused: false,
  updating: false,
  status: '',
  setSpeed: async (value) => {
    set({ speed: value, updating: true, status: '' })
    try {
      await setSimulationSpeed(value)
      set({ status: 'Speed updated' })
    } catch (err) {
      set({ status: err.message || 'Speed update failed' })
    } finally {
      set({ updating: false })
    }
  },
  pause: async () => {
    set({ updating: true, status: '' })
    try {
      await pauseSimulation()
      set({ isPaused: true, status: 'Paused' })
    } catch (err) {
      set({ status: err.message || 'Pause failed' })
    } finally {
      set({ updating: false })
    }
  },
  resume: async () => {
    set({ updating: true, status: '' })
    try {
      await resumeSimulation(get().speed)
      set({ isPaused: false, status: 'Resumed' })
    } catch (err) {
      set({ status: err.message || 'Resume failed' })
    } finally {
      set({ updating: false })
    }
  },
}))

export default useSimulationStore

 