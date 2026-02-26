import { useState, useEffect, useCallback } from 'react'
import { Form, InputNumber, Button, Card, Progress, Space, Typography, App, theme } from 'antd'
import { StopOutlined, FolderOpenOutlined } from '@ant-design/icons'
import { Zap, Layers } from 'lucide-react'
import { useTestPatternStore } from '../../stores/testPatternStore'
import { useAppStore } from '../../stores/appStore'
import { apiClient } from '../../api/client'
import { connectWebSocket, onBatchProgress, cancelBatch, type BatchProgress } from '../../api/websocket'

export function BatchExportPanel(): React.ReactElement {
  const store = useTestPatternStore()
  const { backendReady } = useAppStore()
  const { message } = App.useApp()
  const { token } = theme.useToken()

  const [aplStart, setAplStart] = useState(1)
  const [aplEnd, setAplEnd] = useState(100)
  const [aplStep, setAplStep] = useState(1)
  const [batchId, setBatchId] = useState<string | null>(null)
  const [progress, setProgress] = useState<BatchProgress | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    if (backendReady) {
      connectWebSocket()
    }
  }, [backendReady])

  useEffect(() => {
    const unsubscribe = onBatchProgress((p) => {
      if (batchId && p.batch_id === batchId) {
        setProgress(p)
        if (p.status !== 'running') {
          setIsRunning(false)
          if (p.status === 'completed') {
            message.success(`批量完成：已生成 ${p.completed} 张图片`)
          } else if (p.status === 'failed') {
            message.error(`批量完成，${p.failed} 张失败`)
          } else if (p.status === 'cancelled') {
            message.info('批量导出已取消')
          }
        }
      }
    })
    return unsubscribe
  }, [batchId, message])

  const handleSelectOutputDir = async (): Promise<void> => {
    const dir = await window.electronAPI.openDirectory()
    if (dir) {
      store.setOutputDirectory(dir)
    }
  }

  const handleStartBatch = useCallback(async () => {
    if (!store.outputDirectory) {
      message.warning('请先选择输出目录')
      return
    }

    setIsRunning(true)
    setProgress(null)

    try {
      const result = await apiClient.batchGenerate({
        width: store.width,
        height: store.height,
        apl_range_start: aplStart,
        apl_range_end: aplEnd,
        apl_step: aplStep,
        shape: store.shape,
        color_space: store.colorSpace,
        hdr_mode: store.hdrMode,
        hdr_peak_nits: store.hdrPeakNits,
        hdr_video_peak_nits: store.hdrVideoPeakNits,
        export_format: store.exportFormat,
        output_directory: store.outputDirectory,
      })
      setBatchId(result.batch_id)
    } catch (err) {
      setIsRunning(false)
      message.error(`批量导出失败：${err instanceof Error ? err.message : '未知错误'}`)
    }
  }, [store, aplStart, aplEnd, aplStep, message])

  const handleCancel = useCallback(() => {
    if (batchId) {
      cancelBatch(batchId)
    }
  }, [batchId])

  const totalImages = Math.max(0, Math.floor((aplEnd - aplStart) / aplStep) + 1)
  const percent = progress ? Math.round((progress.completed / progress.total) * 100) : 0

  const cardStyle = {
    background: token.colorBgContainer,
    borderRadius: 16,
    boxShadow: `0 4px 24px -6px ${token.colorText}10`,
    border: `1px solid ${token.colorBorderSecondary}`,
    overflow: 'hidden'
  }

  return (
    <Card
      style={cardStyle}
      styles={{
        header: { padding: '20px 24px', borderBottom: `1px solid ${token.colorBorderSecondary}` },
        body: { padding: 24 }
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Layers size={18} color={token.colorPrimary} />
          <Typography.Text strong style={{ fontSize: 16 }}>批量序列导出</Typography.Text>
        </div>
      }
    >
      <Form layout="vertical" size="middle">
        <Form.Item label={<span style={{ fontWeight: 500 }}>APL 渐变范围 (%)</span>}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <InputNumber min={1} max={100} value={aplStart} onChange={(v) => v && setAplStart(v)} style={{ width: 80 }} />
            <span style={{ color: token.colorTextDescription }}>至</span>
            <InputNumber min={1} max={100} value={aplEnd} onChange={(v) => v && setAplEnd(v)} style={{ width: 80 }} />
            <span style={{ color: token.colorTextDescription }}>步长</span>
            <InputNumber min={1} max={99} value={aplStep} onChange={(v) => v && setAplStep(v)} style={{ width: 70 }} />
          </div>
          <Typography.Text type="secondary" style={{ display: 'block', marginTop: 12, fontSize: 13 }}>
            共计 {totalImages} 张目标图片
          </Typography.Text>
        </Form.Item>

        <Form.Item label={<span style={{ fontWeight: 500 }}>保存路径</span>}>
          <Button icon={<FolderOpenOutlined />} onClick={handleSelectOutputDir} style={{ width: '100%', textAlign: 'left', borderRadius: 8 }}>
            {store.outputDirectory || '选择文件夹...'}
          </Button>
        </Form.Item>

        {progress && isRunning && (
          <div style={{ background: token.colorFillAlter, padding: 16, borderRadius: 12, marginBottom: 24 }}>
            <Progress
              percent={percent}
              status={progress.status === 'running' ? 'active' : 'normal'}
              format={() => `${progress.completed}/${progress.total}`}
              strokeColor={{
                '0%': token.colorPrimary,
                '100%': token.colorSuccess,
              }}
            />
            {progress.current_apl !== null && (
              <Typography.Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 13 }}>
                正在生成 APL {progress.current_apl}%...
              </Typography.Text>
            )}
          </div>
        )}

        <Form.Item style={{ marginBottom: 0 }}>
          <Space style={{ width: '100%' }}>
            <Button
              type="primary"
              loading={isRunning}
              disabled={!backendReady || isRunning}
              onClick={handleStartBatch}
              style={{
                height: 44, borderRadius: 8, fontWeight: 500, flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                background: !isRunning ? token.colorWarning : undefined,
                borderColor: !isRunning ? token.colorWarning : undefined,
              }}
            >
              {!isRunning && <Zap size={16} />} 
              开始批量导出
            </Button>
            {isRunning && (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={handleCancel}
                style={{ height: 44, borderRadius: 8, fontWeight: 500 }}
              >
                中止任务
              </Button>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}