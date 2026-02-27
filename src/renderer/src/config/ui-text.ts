/**
 * UI text constants for internationalization support.
 * All user-facing strings are centralized here.
 */

export const UI_TEXT = {
  // App header
  APP_TITLE: 'c0lor-mem',

  // Sidebar
  MENU_TEST_PATTERN: 'APL 测试图案',
  THEME_SWITCH_LIGHT: '切换浅色',
  THEME_SWITCH_DARK: '切换深色',

  // Footer
  ENGINE_STATUS: '引擎状态：',
  STATUS_ONLINE: '在线就绪',
  STATUS_OFFLINE: '连接中断',

  // Test pattern form
  SECTION_RESOLUTION: '分辨率',
  SECTION_APL: 'APL 设置',
  SECTION_COLOR: '色彩空间',
  SECTION_HDR: 'HDR 设置',
  SECTION_OUTPUT: '输出设置',
  SECTION_BATCH: '批量导出',

  WIDTH_LABEL: '宽度 (像素)',
  HEIGHT_LABEL: '高度 (像素)',
  APL_LABEL: 'APL 百分比',

  SHAPE_LABEL: '形状',
  SHAPE_RECTANGLE: '矩形',
  SHAPE_CIRCLE: '圆形',

  COLOR_SPACE_LABEL: '色彩空间',
  COLOR_SPACE_REC709: 'Rec.709 (sRGB)',
  COLOR_SPACE_DISPLAY_P3: 'Display P3',
  COLOR_SPACE_REC2020: 'Rec.2020',

  HDR_MODE_LABEL: 'HDR 模式',
  HDR_MODE_NONE: 'SDR',
  HDR_MODE_ULTRA_HDR: 'Ultra HDR',
  HDR_MODE_HDR10_PQ: 'HDR10 PQ',

  HDR_PEAK_NITS_LABEL: 'HDR 峰值亮度 (nits)',
  HDR_VIDEO_PEAK_NITS_LABEL: 'HDR 视频峰值亮度 (nits)',

  FORMAT_LABEL: '输出格式',
  OUTPUT_DIR_LABEL: '输出目录',
  SELECT_DIR: '选择目录',

  // Buttons
  PREVIEW: '预览',
  GENERATE: '生成',
  BATCH_GENERATE: '批量导出',
  CANCEL: '取消',

  // Batch
  BATCH_APL_RANGE: 'APL 范围',
  BATCH_APL_START: '起始 APL',
  BATCH_APL_END: '结束 APL',
  BATCH_APL_STEP: '步长',
  BATCH_PROGRESS: '批量导出进度',
  BATCH_COMPLETED: '已完成',
  BATCH_FAILED: '失败',
  BATCH_CANCELLED: '已取消',

  // Messages
  GENERATE_SUCCESS: '生成成功',
  GENERATE_ERROR: '生成失败',
  PREVIEW_ERROR: '预览加载失败',
  OUTPUT_DIR_REQUIRED: '请先选择输出目录',

  // Presets
  PRESET_IPHONE_15_PRO: 'iPhone 15 Pro',
  PRESET_IPHONE_16_PRO_MAX: 'iPhone 16 Pro Max',
  PRESET_4K_TV: '4K TV',
  PRESET_CUSTOM: '自定义',
} as const
