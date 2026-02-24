export interface DevicePreset {
  name: string
  brand: string
  width: number
  height: number
}

export const devicePresets: DevicePreset[] = [
  // Apple
  { name: 'iPhone 16 Pro Max', brand: 'Apple', width: 1320, height: 2868 },
  { name: 'iPhone 16 Pro', brand: 'Apple', width: 1206, height: 2622 },
  { name: 'iPhone 16', brand: 'Apple', width: 1170, height: 2532 },
  { name: 'iPhone 15 Pro Max', brand: 'Apple', width: 1290, height: 2796 },
  { name: 'iPhone 15 Pro', brand: 'Apple', width: 1179, height: 2556 },
  { name: 'iPhone 15', brand: 'Apple', width: 1179, height: 2556 },
  { name: 'iPhone 14 Pro Max', brand: 'Apple', width: 1290, height: 2796 },
  { name: 'iPhone 14 Pro', brand: 'Apple', width: 1179, height: 2556 },
  { name: 'iPad Pro 13"', brand: 'Apple', width: 2064, height: 2752 },
  { name: 'iPad Pro 11"', brand: 'Apple', width: 1668, height: 2388 },

  // Samsung
  { name: 'Galaxy S24 Ultra', brand: 'Samsung', width: 1440, height: 3120 },
  { name: 'Galaxy S24+', brand: 'Samsung', width: 1440, height: 3120 },
  { name: 'Galaxy S24', brand: 'Samsung', width: 1080, height: 2340 },
  { name: 'Galaxy S23 Ultra', brand: 'Samsung', width: 1440, height: 3088 },
  { name: 'Galaxy Z Fold5', brand: 'Samsung', width: 1812, height: 2176 },

  // Xiaomi
  { name: 'Xiaomi 14 Ultra', brand: 'Xiaomi', width: 1440, height: 3200 },
  { name: 'Xiaomi 14 Pro', brand: 'Xiaomi', width: 1440, height: 3200 },
  { name: 'Xiaomi 14', brand: 'Xiaomi', width: 1200, height: 2670 },

  // Google
  { name: 'Pixel 9 Pro XL', brand: 'Google', width: 1344, height: 2992 },
  { name: 'Pixel 9 Pro', brand: 'Google', width: 1280, height: 2856 },
  { name: 'Pixel 9', brand: 'Google', width: 1080, height: 2424 },

  // HUAWEI
  { name: 'Mate 60 Pro', brand: 'HUAWEI', width: 1260, height: 2720 },
  { name: 'P60 Pro', brand: 'HUAWEI', width: 1220, height: 2700 },

  // OnePlus
  { name: 'OnePlus 12', brand: 'OnePlus', width: 1440, height: 3168 },

  // Common
  { name: '1080p', brand: 'Standard', width: 1080, height: 1920 },
  { name: '1440p (2K)', brand: 'Standard', width: 1440, height: 2560 },
  { name: '4K UHD', brand: 'Standard', width: 2160, height: 3840 },
]
