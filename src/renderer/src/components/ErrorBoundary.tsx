import { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button, Typography } from 'antd'

const { Text } = Typography

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Error Boundary component that catches JavaScript errors in child components.
 * Displays a fallback UI instead of crashing the entire application.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null })
  }

  handleReload = (): void => {
    window.location.reload()
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          style={{
            height: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#141414',
            padding: 24,
          }}
        >
          <Result
            status="error"
            title="应用程序发生错误"
            subTitle={
              <div style={{ maxWidth: 500 }}>
                <Text type="secondary">应用程序遇到了意外错误。请尝试重置或刷新页面。</Text>
                {this.state.error && (
                  <div
                    style={{
                      marginTop: 16,
                      padding: 12,
                      background: '#1a1a1a',
                      borderRadius: 6,
                      textAlign: 'left',
                    }}
                  >
                    <Text code style={{ fontSize: 12, color: '#ff7875' }}>
                      {this.state.error.message}
                    </Text>
                  </div>
                )}
              </div>
            }
            extra={[
              <Button key="reset" onClick={this.handleReset}>
                重置
              </Button>,
              <Button key="reload" type="primary" onClick={this.handleReload}>
                刷新页面
              </Button>,
            ]}
          />
        </div>
      )
    }

    return this.props.children
  }
}
