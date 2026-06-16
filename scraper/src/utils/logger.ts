import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

const LOG_LEVEL_NAMES = ['DEBUG', 'INFO', 'WARN', 'ERROR'];

class Logger {
  private level: LogLevel = LogLevel.INFO;
  private logFile: string;
  private enableConsole = true;
  private enableFile = true;

  constructor() {
    const today = new Date().toISOString().split('T')[0];
    const logsDir = path.join(process.cwd(), 'logs');
    
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }
    
    this.logFile = path.join(logsDir, `scrape-${today}.log`);
  }

  setLevel(level: LogLevel): void {
    this.level = level;
  }

  setLevelByName(name: string): void {
    const index = LOG_LEVEL_NAMES.indexOf(name.toUpperCase());
    if (index >= 0) {
      this.level = index;
    }
  }

  disableConsole(): void {
    this.enableConsole = false;
  }

  disableFile(): void {
    this.enableFile = false;
  }

  private formatMessage(level: LogLevel, message: string, meta?: Record<string, unknown>): string {
    const timestamp = new Date().toISOString();
    const levelName = LOG_LEVEL_NAMES[level];
    const metaStr = meta ? ` ${JSON.stringify(meta)}` : '';
    return `[${timestamp}] [${levelName}] ${message}${metaStr}`;
  }

  private write(level: LogLevel, message: string, meta?: Record<string, unknown>): void {
    if (level < this.level) return;

    const formattedMessage = this.formatMessage(level, message, meta);

    if (this.enableConsole) {
      this.writeConsole(level, message, meta);
    }

    if (this.enableFile) {
      this.writeFile(formattedMessage);
    }
  }

  private writeConsole(level: LogLevel, message: string, meta?: Record<string, unknown>): void {
    const metaStr = meta ? ` ${chalk.gray(JSON.stringify(meta))}` : '';
    
    switch (level) {
      case LogLevel.DEBUG:
        console.log(chalk.gray(`[DEBUG] ${message}${metaStr}`));
        break;
      case LogLevel.INFO:
        console.log(chalk.blue(`[INFO] ${message}${metaStr}`));
        break;
      case LogLevel.WARN:
        console.warn(chalk.yellow(`[WARN] ${message}${metaStr}`));
        break;
      case LogLevel.ERROR:
        console.error(chalk.red(`[ERROR] ${message}${metaStr}`));
        break;
    }
  }

  private writeFile(message: string): void {
    try {
      fs.appendFileSync(this.logFile, message + '\n');
    } catch (error) {
      console.error('Failed to write to log file:', error);
    }
  }

  debug(message: string, meta?: Record<string, unknown>): void {
    this.write(LogLevel.DEBUG, message, meta);
  }

  info(message: string, meta?: Record<string, unknown>): void {
    this.write(LogLevel.INFO, message, meta);
  }

  warn(message: string, meta?: Record<string, unknown>): void {
    this.write(LogLevel.WARN, message, meta);
  }

  error(message: string, meta?: Record<string, unknown>): void {
    this.write(LogLevel.ERROR, message, meta);
  }

  success(message: string, meta?: Record<string, unknown>): void {
    if (this.level <= LogLevel.INFO) {
      const metaStr = meta ? ` ${chalk.gray(JSON.stringify(meta))}` : '';
      console.log(chalk.green(`[SUCCESS] ${message}${metaStr}`));
      
      if (this.enableFile) {
        const fileMsg = `[${new Date().toISOString()}] [INFO] ${message}${meta ? ' ' + JSON.stringify(meta) : ''}`;
        fs.appendFileSync(this.logFile, fileMsg + '\n');
      }
    }
  }

  progress(current: number, total: number, message?: string): void {
    const percentage = ((current / total) * 100).toFixed(1);
    const bar = this.createProgressBar(current, total);
    const msg = message ? ` ${message}` : '';
    console.log(chalk.cyan(`[${bar}] ${percentage}%${msg}`));
  }

  private createProgressBar(current: number, total: number, width = 30): string {
    const filled = Math.round((current / total) * width);
    const empty = width - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  }

  getLogFilePath(): string {
    return this.logFile;
  }
}

export const logger = new Logger();