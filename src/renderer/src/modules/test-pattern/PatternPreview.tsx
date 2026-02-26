import { useRef, useEffect } from 'react'
import { Card, Typography, theme } from 'antd'
import { Maximize2 } from 'lucide-react'
import { useTestPatternStore } from '../../stores/testPatternStore'
import { calcRectangle, calcCircle } from '../../utils/pattern-math'

export function PatternPreview(): React.ReactElement {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { width, height, aplPercent, shape } = useTestPatternStore()
  const { token } = theme.useToken()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 考虑到预览区域自适应，定义最大渲染尺寸并根据比例缩放
    const parentNode = canvas.parentElement
    const maxDisplayW = parentNode ? parentNode.clientWidth - 48 : 600
    const maxDisplayH = 600
    const scale = Math.min(maxDisplayW / width, maxDisplayH / height)
    const displayW = Math.round(width * scale)
    const displayH = Math.round(height * scale)

    canvas.width = displayW
    canvas.height = displayH

    // SDR Preview uses standard colors. Background is black.
    ctx.fillStyle = '#000000'
    ctx.fillRect(0, 0, displayW, displayH)

    // Window shape is white.
    ctx.fillStyle = '#ffffff'

    if (shape === 'rectangle') {
      const rect = calcRectangle(displayW, displayH, aplPercent)
      ctx.fillRect(rect.x, rect.y, rect.w, rect.h)
    } else {
      const circle = calcCircle(displayW, displayH, aplPercent)
      ctx.beginPath()
      ctx.arc(circle.cx, circle.cy, circle.radius, 0, Math.PI * 2)
      ctx.fill()
    }
  }, [width, height, aplPercent, shape])

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
        body: { padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Maximize2 size={18} color={token.colorPrimary} />
          <Typography.Text strong style={{ fontSize: 16 }}>实时预览</Typography.Text>
        </div>
      }
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
        <Typography.Text type="secondary" style={{ 
          background: token.colorFillAlter, 
          padding: '6px 16px', 
          borderRadius: 20, 
          fontSize: 13,
          fontWeight: 500,
          border: `1px solid ${token.colorBorderSecondary}` 
        }}>
          {width} × {height} &nbsp;|&nbsp; APL {aplPercent}%
        </Typography.Text>
      </div>
      
      <div style={{ 
        width: '100%', 
        display: 'flex', 
        justifyContent: 'center', 
        padding: '24px 0',
        background: `radial-gradient(circle at center, ${token.colorFillAlter} 0%, transparent 100%)`
      }}>
        <canvas
          ref={canvasRef}
          style={{
            border: `1px solid ${token.colorBorder}`,
            borderRadius: 8,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
            maxWidth: '100%',
            transition: 'all 0.4s cubic-bezier(0.22, 1, 0.36, 1)'
          }}
        />
      </div>
      
      <Typography.Text type="secondary" style={{ fontSize: 13, textAlign: 'center', marginTop: 16 }}>
        预览仅代表 SDR 效果与窗口占比，真实的 HDR 亮度与色域由后端独立生成引擎负责处理。
      </Typography.Text>
    </Card>
  )
}