import { create } from 'zustand'

type ThemeMode = 'light' | 'dark'

interface AppState {
  backendUrl: string | null
  backendToken: string | null
  backendReady: boolean
  theme: ThemeMode
  setBackendInfo: (url: string, token: string) => void
  setBackendReady: (ready: boolean) => void
  toggleTheme: () => void
}

const getInitialTheme = (): ThemeMode => {
  const saved = localStorage.getItem('c0lor-mem-theme')
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useAppStore = create<AppState>((set) => ({
  backendUrl: null,
  backendToken: null,
  backendReady: false,
  theme: getInitialTheme(),
  setBackendInfo: (backendUrl, backendToken) => set({ backendUrl, backendToken }),
  setBackendReady: (ready) => set({ backendReady: ready }),
  toggleTheme: () => set((state) => {
    const newTheme = state.theme === 'dark' ? 'light' : 'dark'
    localStorage.setItem('c0lor-mem-theme', newTheme)
    return { theme: newTheme }
  })
}))
