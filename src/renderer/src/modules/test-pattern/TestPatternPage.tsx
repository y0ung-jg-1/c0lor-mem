import { Typography, Row, Col, theme } from 'antd'
import { motion } from 'framer-motion'
import type { Variants } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import { PatternConfigForm } from './PatternConfigForm'
import { PatternPreview } from './PatternPreview'
import { BatchExportPanel } from './BatchExportPanel'

const ease = [0.22, 1, 0.36, 1] as const

const container: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
}

const item: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease } },
}

export function TestPatternPage(): React.ReactElement {
  const { token } = theme.useToken()

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      style={{ maxWidth: 1400, margin: '0 auto' }}
    >
      <motion.div
        variants={item}
        style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}
      >
        <div
          style={{ background: token.colorInfoBg, padding: 8, borderRadius: 12, display: 'flex' }}
        >
          <Sparkles size={24} color={token.colorPrimary} />
        </div>
        <div>
          <Typography.Title
            level={2}
            style={{ margin: 0, fontWeight: 700, letterSpacing: '-0.02em' }}
          >
            APL 图案引擎
          </Typography.Title>
          <Typography.Text type="secondary" style={{ fontSize: 15 }}>
            配置、预览并导出高精度 SDR/HDR 测试图像
          </Typography.Text>
        </div>
      </motion.div>

      <Row gutter={[32, 32]}>
        <Col xs={24} xl={10}>
          <motion.div variants={item}>
            <PatternConfigForm />
          </motion.div>
          <motion.div variants={item} style={{ marginTop: 32 }}>
            <BatchExportPanel />
          </motion.div>
        </Col>
        <Col xs={24} xl={14}>
          <motion.div variants={item} style={{ position: 'sticky', top: 32 }}>
            <PatternPreview />
          </motion.div>
        </Col>
      </Row>
    </motion.div>
  )
}
