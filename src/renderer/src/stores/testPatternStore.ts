import { create } from 'zustand'

export type Shape = 'rectangle' | 'circle'
export type ColorSpace = 'rec709' | 'displayP3' | 'rec2020'
export type HdrMode = 'none' | 'ultra-hdr' | 'hdr10-pq'
export type ExportFormat = 'png' | 'jpeg' | 'heif' | 'h264' | 'h265'

export interface TestPatternConfig {
  width: number
  height: number
  aplPercent: number
  shape: Shape
  colorSpace: ColorSpace
  hdrMode: HdrMode
  hdrPeakNits: number
  hdrVideoPeakNits: number
  exportFormat: ExportFormat
  outputDirectory: string
}

interface TestPatternState extends TestPatternConfig {
  isGenerating: boolean
  setResolution: (width: number, height: number) => void
  setAplPercent: (apl: number) => void
  setShape: (shape: Shape) => void
  setColorSpace: (cs: ColorSpace) => void
  setHdrMode: (mode: HdrMode) => void
  setHdrPeakNits: (nits: number) => void
  setHdrVideoPeakNits: (nits: number) => void
  setExportFormat: (fmt: ExportFormat) => void
  setOutputDirectory: (dir: string) => void
  setIsGenerating: (generating: boolean) => void
}

export const useTestPatternStore = create<TestPatternState>((set) => ({
  width: 1170,
  height: 2532,
  aplPercent: 50,
  shape: 'rectangle',
  colorSpace: 'rec709',
  hdrMode: 'none',
  hdrPeakNits: 1000,
  hdrVideoPeakNits: 10000,
  exportFormat: 'png',
  outputDirectory: '',
  isGenerating: false,
  setResolution: (width, height) => set({ width, height }),
  setAplPercent: (aplPercent) => set({ aplPercent }),
  setShape: (shape) => set({ shape }),
  setColorSpace: (colorSpace) => set({ colorSpace }),
  setHdrMode: (hdrMode) => set({ hdrMode }),
  setHdrPeakNits: (hdrPeakNits) => set({ hdrPeakNits }),
  setHdrVideoPeakNits: (hdrVideoPeakNits) => set({ hdrVideoPeakNits }),
  setExportFormat: (exportFormat) => set({ exportFormat }),
  setOutputDirectory: (outputDirectory) => set({ outputDirectory }),
  setIsGenerating: (isGenerating) => set({ isGenerating })
}))
