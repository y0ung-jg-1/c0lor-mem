import { useState, useEffect, useCallback } from 'react'
import { Form, InputNumber, Button, Card, Progress, Space, Typography, App } from 'antd'
import { ThunderboltOutlined, StopOutlined, FolderOpenOutlined } from '@ant-design/icons'
import { useTestPatternStore } from '../../stores/testPatternStore'
import { useAppStore } from '../../stores/appStore'
import { apiClient } from '../../api/client'
import { connectWebSocket, onBatchProgress, cancelBatch, type BatchProgress } from '../../api/websocket'

export function BatchExportPanel(): React.ReactElement {
  const store = useTestPatternStore()
  const { backendReady } = useAppStore()
  const { message } = App.useApp()

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

  return (
    <Card
      title="批量导出"
      style={{ background: '#1f1f1f', border: '1px solid #303030', marginTop: 16 }}
    >
      <Form layout="vertical" size="middle">
        <Form.Item label="APL 范围">
          <Space>
            <InputNumber
              min={1}
              max={100}
              value={aplStart}
              onChange={(v) => v && setAplStart(v)}
              addonAfter="%"
              style={{ width: 100 }}
            />
            <span style={{ color: 'rgba(255,255,255,0.45)' }}>至</span>
            <InputNumber
              min={1}
              max={100}
              value={aplEnd}
              onChange={(v) => v && setAplEnd(v)}
              addonAfter="%"
              style={{ width: 100 }}
            />
            <span style={{ color: 'rgba(255,255,255,0.45)' }}>步长</span>
            <InputNumber
              min={1}
              max={99}
              value={aplStep}
              onChange={(v) => v && setAplStep(v)}
              style={{ width: 80 }}
            />
          </Space>
          <Typography.Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
            将生成 {totalImages} 张图片
          </Typography.Text>
        </Form.Item>

        <Form.Item label="输出目录">
          <Button icon={<FolderOpenOutlined />} onClick={handleSelectOutputDir}>
            {store.outputDirectory || '选择文件夹...'}
          </Button>
        </Form.Item>

        {progress && isRunning && (
          <Form.Item>
            <Progress
              percent={percent}
              status={progress.status === 'running' ? 'active' : 'normal'}
              format={() => `${progress.completed}/${progress.total}`}
            />
            {progress.current_apl !== null && (
              <Typography.Text type="secondary">
                正在生成 APL {progress.current_apl}%...
              </Typography.Text>
            )}
          </Form.Item>
        )}

        <Form.Item>
          <Space>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              loading={isRunning}
              disabled={!backendReady || isRunning}
              onClick={handleStartBatch}
            >
              开始批量导出
            </Button>
            {isRunning && (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={handleCancel}
              >
                取消
              </Button>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}
