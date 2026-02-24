import { Typography, Row, Col } from 'antd'
import { PatternConfigForm } from './PatternConfigForm'
import { PatternPreview } from './PatternPreview'
import { BatchExportPanel } from './BatchExportPanel'

export function TestPatternPage(): React.ReactElement {
  return (
    <div>
      <Typography.Title level={3} style={{ marginTop: 0 }}>
        APL 测试图案生成器
      </Typography.Title>
      <Row gutter={24}>
        <Col xs={24} lg={10}>
          <PatternConfigForm />
          <BatchExportPanel />
        </Col>
        <Col xs={24} lg={14}>
          <PatternPreview />
        </Col>
      </Row>
    </div>
  )
}
