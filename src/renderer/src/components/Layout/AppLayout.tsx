import { Layout, Typography, Tag, Button, theme } from 'antd'
import { useEffect } from 'react'
import { Sun, Moon, Zap, Layers, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../../stores/appStore'
import { apiClient } from '../../api/client'
import { TestPatternPage } from '../../modules/test-pattern/TestPatternPage'

const { Sider, Content, Footer } = Layout

export function AppLayout(): React.ReactElement {
  const {
    backendReady,
    setBackendInfo,
    setBackendReady,
    theme: appTheme,
    toggleTheme,
  } = useAppStore()
  const { token } = theme.useToken()

  useEffect(() => {
    const unsubscribe = window.electronAPI.onBackendInfo(async ({ url, token }) => {
      setBackendReady(false)
      setBackendInfo(url, token)
      try {
        const result = await apiClient.health()
        setBackendReady(result.status === 'ok')
      } catch {
        console.error('Health check failed')
        setBackendReady(false)
      }
    })
    return unsubscribe
  }, [setBackendInfo, setBackendReady])

  const isDark = appTheme === 'dark'

  return (
    <Layout style={{ height: '100vh', background: token.colorBgLayout }}>
      <Sider
        width={240}
        theme={isDark ? 'dark' : 'light'}
        style={{
          background: token.colorBgElevated,
          borderRight: `1px solid ${token.colorBorderSecondary}`,
          padding: '24px 0',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          style={{
            padding: '0 24px',
            marginBottom: 32,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              background: token.colorPrimary,
              borderRadius: 8,
              padding: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 4px 12px ${token.colorPrimary}40`,
            }}
          >
            <Zap size={20} color="#fff" />
          </div>
          <Typography.Title
            level={4}
            style={{ margin: 0, color: token.colorText, fontWeight: 700, letterSpacing: '-0.02em' }}
          >
            c0lor-mem
          </Typography.Title>
        </motion.div>

        <div style={{ flex: 1, padding: '0 12px' }}>
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{
              padding: '12px 16px',
              background: isDark ? '#1668dc22' : '#e6f4ff',
              borderRadius: 8,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              border: `1px solid ${isDark ? '#1668dc44' : '#91caff'}`,
            }}
          >
            <Layers size={18} color={token.colorPrimary} />
            <Typography.Text strong style={{ color: token.colorPrimary, fontSize: 14 }}>
              APL 测试图案
            </Typography.Text>
          </motion.div>
        </div>

        <div style={{ padding: '0 24px', display: 'flex', alignItems: 'center', gap: 12 }}>
          <Button
            type="text"
            icon={isDark ? <Sun size={18} /> : <Moon size={18} />}
            onClick={toggleTheme}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: token.colorTextSecondary,
            }}
          >
            {isDark ? '切换浅色' : '切换深色'}
          </Button>
        </div>
      </Sider>

      <Layout style={{ background: token.colorBgLayout }}>
        <Content
          id="main-content"
          style={{ overflow: 'auto', padding: '32px 40px', position: 'relative' }}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key="test-pattern"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }} // Non-linear custom bezier
            >
              <TestPatternPage />
            </motion.div>
          </AnimatePresence>
        </Content>

        <Footer
          style={{
            background: token.colorBgContainer,
            borderTop: `1px solid ${token.colorBorderSecondary}`,
            padding: '12px 40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backdropFilter: 'blur(10px)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Activity size={16} color={backendReady ? token.colorSuccess : token.colorError} />
            <Typography.Text type="secondary" style={{ fontSize: 13 }}>
              引擎状态：
            </Typography.Text>
            <Tag
              color={backendReady ? 'success' : 'error'}
              style={{
                borderRadius: 12,
                border: 'none',
                background: backendReady ? token.colorSuccessBg : token.colorErrorBg,
              }}
            >
              {backendReady ? '在线就绪' : '连接中断'}
            </Tag>
          </div>
          <Typography.Text type="secondary" style={{ fontSize: 13 }}>
            c0lor-mem v0.1.0 &copy; 2026
          </Typography.Text>
        </Footer>
      </Layout>
    </Layout>
  )
}
