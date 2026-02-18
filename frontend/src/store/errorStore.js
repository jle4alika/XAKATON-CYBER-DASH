import { create } from 'zustand'

const useErrorStore = create((set) => ({
  errors: [],
  pushError: (error) =>
    set((state) => {
      const entry = {
        id: `${Date.now()}-${Math.random()}`,
        timestamp: new Date().toISOString(),
        source: error?.source || 'unknown',
        message: error?.message || 'Unknown error',
        context: error?.context || null,
      }
      return { errors: [entry, ...state.errors].slice(0, 200) }
    }),
  clearErrors: () => set({ errors: [] }),
}))

export default useErrorStore

