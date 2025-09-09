// Simple logger utility to avoid console call stacks
class Logger {
  private formatMessage(level: string, message: string, data?: any): string {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] ${level}:`;

    if (data !== undefined) {
      // For complex objects, use JSON.stringify to avoid call stacks
      if (typeof data === 'object' && data !== null) {
        try {
          return `${prefix} ${message} ${JSON.stringify(data, null, 2)}`;
        } catch (e) {
          return `${prefix} ${message} [Object]`;
        }
      }
      return `${prefix} ${message} ${String(data)}`;
    }

    return `${prefix} ${message}`;
  }

  info(message: string, data?: any) {
    console.log(this.formatMessage('INFO', message, data));
  }

  debug(message: string, data?: any) {
    console.log(this.formatMessage('DEBUG', message, data));
  }

  warn(message: string, data?: any) {
    console.warn(this.formatMessage('WARN', message, data));
  }

  error(message: string, data?: any) {
    console.error(this.formatMessage('ERROR', message, data));
  }

  // Legacy method for simple string messages
  log(message: string) {
    console.log(`[${new Date().toISOString()}] LOG: ${message}`);
  }
}

export const logger = new Logger();
export default logger;
