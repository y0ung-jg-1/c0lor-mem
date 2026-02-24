import { ConfigProvider, theme, App as AntApp } from 'antd'
import { AppLayout } from './components/Layout/AppLayout'

function App(): React.ReactElement {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#1668dc',
          borderRadius: 6
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
