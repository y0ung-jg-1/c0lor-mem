import { useRef, useEffect } from 'react'
import { Card, Typography } from 'antd'
import { useTestPatternStore } from '../../stores/testPatternStore'
import { calcRectangle, calcCircle } from '../../utils/pattern-math'

export function PatternPreview(): React.ReactElement {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { width, height, aplPercent, shape } = useTestPatternStore()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Fit canvas to container while maintaining aspect ratio
    const maxDisplayW = 400
    const maxDisplayH = 500
    const scale = Math.min(maxDisplayW / width, maxDisplayH / height)
    const displayW = Math.round(width * scale)
    const displayH = Math.round(height * scale)

    canvas.width = displayW
    canvas.height = displayH

    // Black background
    ctx.fillStyle = '#000000'
    ctx.fillRect(0, 0, displayW, displayH)

    // White shape
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

  return (
    <Card
      style={{ background: '#1f1f1f', border: '1px solid #303030' }}
      styles={{ body: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 } }}
    >
      <Typography.Text type="secondary">
        预览 &mdash; {width} x {height} &mdash; APL {aplPercent}%
      </Typography.Text>
      <canvas
        ref={canvasRef}
        style={{
          border: '1px solid #303030',
          borderRadius: 4,
          maxWidth: '100%'
        }}
      />
    </Card>
  )
}
