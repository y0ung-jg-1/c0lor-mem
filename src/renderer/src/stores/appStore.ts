import { create } from 'zustand'

interface AppState {
  backendUrl: string | null
  backendReady: boolean
  setBackendUrl: (url: string) => void
  setBackendReady: (ready: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
  backendUrl: null,
  backendReady: false,
  setBackendUrl: (url) => set({ backendUrl: url }),
  setBackendReady: (ready) => set({ backendReady: ready })
}))
