/**
 * Structured logger for Electron main process.
 * In development, logs to console. In production, logs are minimal.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

const isDev = process.env.NODE_ENV === 'development' || !process.env.NODE_ENV

function formatMessage(level: LogLevel, msg: string): string {
  const timestamp = new Date().toISOString()
  return `[${timestamp}] ${level.toUpperCase()}: ${msg}`
}

export const logger = {
  debug: (msg: string, ...args: unknown[]): void => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.log(formatMessage('debug', msg), ...args)
    }
  },
  info: (msg: string, ...args: unknown[]): void => {
    // eslint-disable-next-line no-console
    console.log(formatMessage('info', msg), ...args)
  },
  warn: (msg: string, ...args: unknown[]): void => {
    console.warn(formatMessage('warn', msg), ...args)
  },
  error: (msg: string, ...args: unknown[]): void => {
    console.error(formatMessage('error', msg), ...args)
  },
}
