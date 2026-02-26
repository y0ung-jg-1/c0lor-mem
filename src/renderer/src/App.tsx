import { ConfigProvider, theme as antdTheme, App as AntApp } from 'antd'
import { AppLayout } from './components/Layout/AppLayout'
import { useAppStore } from './stores/appStore'

function App(): React.ReactElement {
  const { theme } = useAppStore()

  return (
    <ConfigProvider
      theme={{
        algorithm: theme === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          colorPrimary: '#1668dc',
          borderRadius: 8,
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
          colorBgContainer: theme === 'dark' ? '#141414' : '#ffffff',
          colorBgElevated: theme === 'dark' ? '#1f1f1f' : '#ffffff',
        }
      }}
    >
      <AntApp>
        <AppLayout />
      </AntApp>
    </ConfigProvider>
  )
}

export default App
