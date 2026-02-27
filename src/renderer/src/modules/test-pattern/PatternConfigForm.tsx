import {
  Form,
  InputNumber,
  Select,
  Slider,
  Radio,
  Button,
  Card,
  Space,
  App,
  theme,
  Divider,
  Typography,
} from 'antd'
import { FolderOpenOutlined, ExportOutlined } from '@ant-design/icons'
import { Settings2, MonitorPlay } from 'lucide-react'
import {
  useTestPatternStore,
  type Shape,
  type ColorSpace,
  type HdrMode,
  type ExportFormat,
} from '../../stores/testPatternStore'
import { useAppStore } from '../../stores/appStore'
import { apiClient } from '../../api/client'
import { devicePresets } from '../../utils/device-presets'

const FORMAT_BY_HDR: Record<HdrMode, ExportFormat[]> = {
  none: ['png', 'jpeg', 'heif', 'h264', 'h265'],
  'ultra-hdr': ['jpeg'],
  'hdr10-pq': ['png', 'h264', 'h265'],
}

export function PatternConfigForm(): React.ReactElement {
  const store = useTestPatternStore()
  const { backendReady } = useAppStore()
  const { message } = App.useApp()
  const { token } = theme.useToken()

  const allowedFormats = FORMAT_BY_HDR[store.hdrMode]

  const handleHdrModeChange = (mode: HdrMode): void => {
    store.setHdrMode(mode)
    const allowed = FORMAT_BY_HDR[mode]
    if (!allowed.includes(store.exportFormat)) {
      store.setExportFormat(allowed[0])
    }
  }

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
        hdr_video_peak_nits: store.hdrVideoPeakNits,
        export_format: store.exportFormat,
        output_directory: store.outputDirectory,
      })
      message.success('生成成功！')
      window.electronAPI.showItemInFolder(result.output_path)
    } catch (err) {
      message.error(`生成失败：${err instanceof Error ? err.message : '未知错误'}`)
    } finally {
      store.setIsGenerating(false)
    }
  }

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
      value: p.name,
    })),
  }))

  const cardStyle = {
    background: token.colorBgContainer,
    borderRadius: 16,
    boxShadow: `0 4px 24px -6px ${token.colorText}10`,
    border: `1px solid ${token.colorBorderSecondary}`,
    overflow: 'hidden',
  }

  return (
    <Card
      style={cardStyle}
      styles={{
        header: { padding: '20px 24px', borderBottom: `1px solid ${token.colorBorderSecondary}` },
        body: { padding: 24 },
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Settings2 size={18} color={token.colorPrimary} />
          <Typography.Text strong style={{ fontSize: 16 }}>
            基础配置
          </Typography.Text>
        </div>
      }
    >
      <Form layout="vertical" size="middle">
        <Form.Item label={<span style={{ fontWeight: 500 }}>设备预设</span>}>
          <Select
            placeholder="选择设备自动设置分辨率"
            options={presetOptions}
            onChange={handlePresetChange}
            allowClear
            showSearch
            filterOption={(input, option) =>
              (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
            }
          />
        </Form.Item>

        <Form.Item label={<span style={{ fontWeight: 500 }}>画布分辨率</span>}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <InputNumber
              min={1}
              max={8192}
              value={store.width}
              onChange={(v) => v && store.setResolution(v, store.height)}
              addonBefore="宽"
              style={{ flex: 1 }}
            />
            <span style={{ color: token.colorTextDescription }}>&times;</span>
            <InputNumber
              min={1}
              max={8192}
              value={store.height}
              onChange={(v) => v && store.setResolution(store.width, v)}
              addonBefore="高"
              style={{ flex: 1 }}
            />
          </div>
        </Form.Item>

        <Form.Item label={<span style={{ fontWeight: 500 }}>目标 APL ({store.aplPercent}%)</span>}>
          <Slider
            min={1}
            max={100}
            value={store.aplPercent}
            onChange={(v) => store.setAplPercent(v)}
            marks={{ 1: '1%', 50: '50%', 100: '100%' }}
            tooltip={{ formatter: (v) => `${v}%` }}
          />
        </Form.Item>

        <Form.Item label={<span style={{ fontWeight: 500 }}>测试区形状</span>}>
          <Radio.Group
            value={store.shape}
            onChange={(e) => store.setShape(e.target.value as Shape)}
            optionType="button"
            buttonStyle="solid"
            style={{ width: '100%' }}
          >
            <Radio.Button value="rectangle" style={{ width: '50%', textAlign: 'center' }}>
              矩形 (Rectangle)
            </Radio.Button>
            <Radio.Button value="circle" style={{ width: '50%', textAlign: 'center' }}>
              圆形 (Circle)
            </Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Divider style={{ margin: '24px 0', borderColor: token.colorBorderSecondary }} />

        <Typography.Title
          level={5}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 20,
            color: token.colorText,
          }}
        >
          <MonitorPlay size={18} color={token.colorPrimary} /> 色彩与动态范围
        </Typography.Title>

        <Form.Item label={<span style={{ fontWeight: 500 }}>色彩空间</span>}>
          <Radio.Group
            value={store.colorSpace}
            onChange={(e) => store.setColorSpace(e.target.value as ColorSpace)}
            optionType="button"
            buttonStyle="solid"
            style={{ width: '100%', display: 'flex' }}
          >
            <Radio.Button value="rec709" style={{ flex: 1, textAlign: 'center' }}>
              Rec.709
            </Radio.Button>
            <Radio.Button value="displayP3" style={{ flex: 1, textAlign: 'center' }}>
              Display P3
            </Radio.Button>
            <Radio.Button value="rec2020" style={{ flex: 1, textAlign: 'center' }}>
              Rec.2020
            </Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item label={<span style={{ fontWeight: 500 }}>HDR 模式</span>}>
          <Radio.Group
            value={store.hdrMode}
            onChange={(e) => handleHdrModeChange(e.target.value as HdrMode)}
            optionType="button"
            buttonStyle="solid"
            style={{ width: '100%', display: 'flex' }}
          >
            <Radio.Button value="none" style={{ flex: 1, textAlign: 'center' }}>
              SDR
            </Radio.Button>
            <Radio.Button value="ultra-hdr" style={{ flex: 1, textAlign: 'center' }}>
              Ultra HDR
            </Radio.Button>
            <Radio.Button value="hdr10-pq" style={{ flex: 1, textAlign: 'center' }}>
              HDR10 PQ
            </Radio.Button>
          </Radio.Group>
        </Form.Item>

        {store.hdrMode === 'hdr10-pq' && (
          <Form.Item
            label={
              <span style={{ fontWeight: 500 }}>视频峰值亮度：{store.hdrVideoPeakNits} nits</span>
            }
          >
            <Slider
              min={200}
              max={10000}
              step={100}
              value={store.hdrVideoPeakNits}
              onChange={(v) => store.setHdrVideoPeakNits(v)}
              marks={{ 1000: '1k', 4000: '4k', 10000: '10k' }}
            />
          </Form.Item>
        )}
        {store.hdrMode === 'ultra-hdr' && (
          <Form.Item
            label={<span style={{ fontWeight: 500 }}>图片峰值亮度：{store.hdrPeakNits} nits</span>}
          >
            <Slider
              min={200}
              max={4000}
              step={100}
              value={store.hdrPeakNits}
              onChange={(v) => store.setHdrPeakNits(v)}
              marks={{ 400: '400', 1000: '1k', 4000: '4k' }}
            />
          </Form.Item>
        )}

        <Divider style={{ margin: '24px 0', borderColor: token.colorBorderSecondary }} />

        <Form.Item label={<span style={{ fontWeight: 500 }}>输出格式</span>}>
          <Radio.Group
            value={store.exportFormat}
            onChange={(e) => store.setExportFormat(e.target.value as ExportFormat)}
            optionType="button"
            buttonStyle="solid"
          >
            <Space size={8} wrap>
              <Radio.Button value="png" disabled={!allowedFormats.includes('png')}>
                PNG
              </Radio.Button>
              <Radio.Button value="jpeg" disabled={!allowedFormats.includes('jpeg')}>
                JPEG
              </Radio.Button>
              <Radio.Button value="heif" disabled={!allowedFormats.includes('heif')}>
                HEIF
              </Radio.Button>
              <Radio.Button value="h264" disabled={!allowedFormats.includes('h264')}>
                H.264
              </Radio.Button>
              <Radio.Button value="h265" disabled={!allowedFormats.includes('h265')}>
                H.265
              </Radio.Button>
            </Space>
          </Radio.Group>
        </Form.Item>

        <Form.Item label={<span style={{ fontWeight: 500 }}>保存路径</span>}>
          <Button
            icon={<FolderOpenOutlined />}
            onClick={handleSelectOutputDir}
            style={{ width: '100%', textAlign: 'left', borderRadius: 8 }}
          >
            {store.outputDirectory || '选择输出目录...'}
          </Button>
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, marginTop: 32 }}>
          <Button
            type="primary"
            icon={<ExportOutlined />}
            size="large"
            block
            loading={store.isGenerating}
            disabled={!backendReady}
            onClick={handleGenerate}
            style={{
              height: 48,
              borderRadius: 12,
              fontSize: 16,
              fontWeight: 600,
              boxShadow: `0 4px 12px ${token.colorPrimary}40`,
            }}
          >
            单张生成
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}
