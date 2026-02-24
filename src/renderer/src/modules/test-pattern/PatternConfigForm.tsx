import { Form, InputNumber, Select, Slider, Radio, Button, Card, Space, App } from 'antd'
import { FolderOpenOutlined, ExportOutlined } from '@ant-design/icons'
import { useTestPatternStore, type Shape, type ColorSpace, type HdrMode, type ExportFormat } from '../../stores/testPatternStore'
import { useAppStore } from '../../stores/appStore'
import { apiClient } from '../../api/client'
import { devicePresets } from '../../utils/device-presets'

export function PatternConfigForm(): React.ReactElement {
  const store = useTestPatternStore()
  const { backendReady } = useAppStore()
  const { message } = App.useApp()

  const handlePresetChange = (value: string): void => {
    if (value === 'custom') return
    const preset = devicePresets.find((p) => `${p.name}` === value)
    if (preset) {
      store.setResolution(preset.width, preset.height)
    }
  }

  const handleSelectOutputDir = async (): Promise<void> => {
    const dir = await window.electronAPI.openDirectory()
    if (dir) {
      store.setOutputDirectory(dir)
    }
  }

  const handleGenerate = async (): Promise<void> => {
    if (!store.outputDirectory) {
      message.warning('请先选择输出目录')
      return
    }
    store.setIsGenerating(true)
    try {
      const result = await apiClient.generate({
        width: store.width,
        height: store.height,
        apl_percent: store.aplPercent,
        shape: store.shape,
        color_space: store.colorSpace,
        hdr_mode: store.hdrMode,
        hdr_peak_nits: store.hdrPeakNits,
        export_format: store.exportFormat,
        output_directory: store.outputDirectory
      })
      message.success('生成成功！')
      window.electronAPI.showItemInFolder(result.output_path)
    } catch (err) {
      message.error(`生成失败：${err instanceof Error ? err.message : '未知错误'}`)
    } finally {
      store.setIsGenerating(false)
    }
  }

  // Group presets by brand
  const presetOptions = Object.entries(
    devicePresets.reduce(
      (groups, preset) => {
        if (!groups[preset.brand]) groups[preset.brand] = []
        groups[preset.brand].push(preset)
        return groups
      },
      {} as Record<string, typeof devicePresets>
    )
  ).map(([brand, presets]) => ({
    label: brand,
    options: presets.map((p) => ({
      label: `${p.name} (${p.width}x${p.height})`,
      value: p.name
    }))
  }))

  return (
    <Card style={{ background: '#1f1f1f', border: '1px solid #303030' }}>
      <Form layout="vertical" size="middle">
        {/* 设备预设 */}
        <Form.Item label="设备预设">
          <Select
            placeholder="选择设备或手动输入分辨率"
            options={presetOptions}
            onChange={handlePresetChange}
            allowClear
            showSearch
            filterOption={(input, option) =>
              (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
            }
          />
        </Form.Item>

        {/* 分辨率 */}
        <Form.Item label="分辨率">
          <Space>
            <InputNumber
              min={1}
              max={8192}
              value={store.width}
              onChange={(v) => v && store.setResolution(v, store.height)}
              addonAfter="宽"
              style={{ width: 130 }}
            />
            <span style={{ color: 'rgba(255,255,255,0.45)' }}>x</span>
            <InputNumber
              min={1}
              max={8192}
              value={store.height}
              onChange={(v) => v && store.setResolution(store.width, v)}
              addonAfter="高"
              style={{ width: 130 }}
            />
          </Space>
        </Form.Item>

        {/* 形状 */}
        <Form.Item label="形状">
          <Radio.Group
            value={store.shape}
            onChange={(e) => store.setShape(e.target.value as Shape)}
            optionType="button"
            buttonStyle="solid"
            options={[
              { label: '矩形', value: 'rectangle' },
              { label: '圆形', value: 'circle' }
            ]}
          />
        </Form.Item>

        {/* APL 滑块 */}
        <Form.Item label={`APL：${store.aplPercent}%`}>
          <Slider
            min={1}
            max={100}
            value={store.aplPercent}
            onChange={(v) => store.setAplPercent(v)}
            marks={{ 1: '1%', 25: '25%', 50: '50%', 75: '75%', 100: '100%' }}
          />
        </Form.Item>

        {/* 色彩空间 */}
        <Form.Item label="色彩空间">
          <Radio.Group
            value={store.colorSpace}
            onChange={(e) => store.setColorSpace(e.target.value as ColorSpace)}
            optionType="button"
            buttonStyle="solid"
            options={[
              { label: 'Rec.709 / sRGB', value: 'rec709' },
              { label: 'Display P3', value: 'displayP3' },
              { label: 'Rec.2020', value: 'rec2020' }
            ]}
          />
        </Form.Item>

        {/* HDR 模式 */}
        <Form.Item label="HDR 模式">
          <Radio.Group
            value={store.hdrMode}
            onChange={(e) => store.setHdrMode(e.target.value as HdrMode)}
            optionType="button"
            buttonStyle="solid"
            options={[
              { label: 'SDR', value: 'none' },
              { label: 'Apple Gain Map', value: 'apple-gainmap' },
              { label: 'Ultra HDR', value: 'ultra-hdr' }
            ]}
          />
        </Form.Item>

        {/* 峰值亮度 - 仅 HDR 模式显示 */}
        {store.hdrMode !== 'none' && (
          <Form.Item label={`峰值亮度：${store.hdrPeakNits} nits`}>
            <Slider
              min={200}
              max={4000}
              step={100}
              value={store.hdrPeakNits}
              onChange={(v) => store.setHdrPeakNits(v)}
              marks={{ 400: '400', 600: '600', 1000: '1000', 1600: '1600', 4000: '4000' }}
            />
          </Form.Item>
        )}

        {/* 导出格式 */}
        <Form.Item label="导出格式">
          <Radio.Group
            value={store.exportFormat}
            onChange={(e) => store.setExportFormat(e.target.value as ExportFormat)}
            optionType="button"
            buttonStyle="solid"
            options={[
              { label: 'PNG', value: 'png' },
              { label: 'JPEG', value: 'jpeg' },
              { label: 'HEIF', value: 'heif' },
              { label: 'H.264', value: 'h264' },
              { label: 'H.265', value: 'h265' },
            ]}
          />
        </Form.Item>

        {/* 输出目录 */}
        <Form.Item label="输出目录">
          <Button icon={<FolderOpenOutlined />} onClick={handleSelectOutputDir}>
            {store.outputDirectory || '选择文件夹...'}
          </Button>
        </Form.Item>

        {/* 生成按钮 */}
        <Form.Item>
          <Button
            type="primary"
            icon={<ExportOutlined />}
            size="large"
            block
            loading={store.isGenerating}
            disabled={!backendReady}
            onClick={handleGenerate}
          >
            生成
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}
