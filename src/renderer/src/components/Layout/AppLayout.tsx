import { Layout, Typography, Tag } from 'antd'
import { useEffect } from 'react'
import { useAppStore } from '../../stores/appStore'
import { apiClient } from '../../api/client'
import { TestPatternPage } from '../../modules/test-pattern/TestPatternPage'

const { Sider, Content, Footer } = Layout

export function AppLayout(): React.ReactElement {
  const { backendReady, setBackendUrl, setBackendReady } = useAppStore()

  useEffect(() => {
    window.electronAPI.onBackendUrl(async (url) => {
      setBackendUrl(url)
      try {
        const result = await apiClient.health()
        if (result.status === 'ok') {
          setBackendReady(true)
        }
      } catch {
        console.error('Health check failed')
      }
    })
  }, [setBackendUrl, setBackendReady])

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider
        width={200}
        style={{
          background: '#1f1f1f',
          borderRight: '1px solid #303030',
          padding: '16px 0'
        }}
      >
        <div style={{ padding: '0 16px', marginBottom: 24 }}>
          <Typography.Title level={4} style={{ margin: 0, color: '#fff' }}>
            c0lor-mem
          </Typography.Title>
        </div>
        <div
          style={{
            padding: '8px 16px',
            background: '#177ddc22',
            borderLeft: '3px solid #177ddc',
            cursor: 'pointer'
          }}
        >
          <Typography.Text strong style={{ color: '#177ddc' }}>
            APL 测试图案
          </Typography.Text>
        </div>
      </Sider>
      <Layout>
        <Content style={{ overflow: 'auto', padding: 24 }}>
          <TestPatternPage />
        </Content>
        <Footer
          style={{
            background: '#1f1f1f',
            borderTop: '1px solid #303030',
            padding: '6px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}
        >
          <Tag color={backendReady ? 'success' : 'error'}>
            {backendReady ? '后端就绪' : '连接中...'}
          </Tag>
        </Footer>
      </Layout>
    </Layout>
  )
}
