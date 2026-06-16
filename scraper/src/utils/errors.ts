import { logger } from './logger';

export class ScraperError extends Error {
  public readonly code: string;
  public readonly url?: string;
  public readonly retryable: boolean;
  public readonly details?: Record<string, unknown>;

  constructor(
    message: string,
    options: {
      code?: string;
      url?: string;
      retryable?: boolean;
      details?: Record<string, unknown>;
    } = {}
  ) {
    super(message);
    this.name = 'ScraperError';
    this.code = options.code ?? 'UNKNOWN';
    this.url = options.url;
    this.retryable = options.retryable ?? true;
    this.details = options.details;
  }
}

export class RateLimitError extends ScraperError {
  constructor(url?: string, retryAfter?: number) {
    super('Rate limit exceeded', {
      code: 'RATE_LIMIT',
      url,
      retryable: true,
      details: retryAfter ? { retryAfter } : undefined,
    });
    this.name = 'RateLimitError';
  }
}

export class AuthenticationError extends ScraperError {
  constructor(url?: string) {
    super('Authentication required or failed', {
      code: 'AUTH_REQUIRED',
      url,
      retryable: false,
    });
    this.name = 'AuthenticationError';
  }
}

export class NotFoundError extends ScraperError {
  constructor(url?: string) {
    super('Resource not found', {
      code: 'NOT_FOUND',
      url,
      retryable: false,
    });
    this.name = 'NotFoundError';
  }
}

export class ParseError extends ScraperError {
  constructor(message: string, url?: string) {
    super(`Failed to parse content: ${message}`, {
      code: 'PARSE_ERROR',
      url,
      retryable: true,
    });
    this.name = 'ParseError';
  }
}

export class DatabaseError extends Error {
  public readonly operation: string;

  constructor(message: string, operation: string) {
    super(message);
    this.name = 'DatabaseError';
    this.operation = operation;
  }
}

export class ConfigurationError extends Error {
  public readonly missingFields: string[];

  constructor(message: string, missingFields: string[] = []) {
    super(message);
    this.name = 'ConfigurationError';
    this.missingFields = missingFields;
  }
}

export interface ErrorContext {
  jobId?: number;
  companyName?: string;
  url?: string;
  phase?: string;
}

export function handleError(error: unknown, context: ErrorContext = {}): ScraperError {
  if (error instanceof ScraperError) {
    logger.error(`Scraper error in ${context.phase}`, {
      code: error.code,
      url: error.url ?? context.url,
      company: context.companyName,
      jobId: context.jobId,
      retryable: error.retryable,
      details: error.details,
    });
    return error;
  }

  if (error instanceof Error) {
    const scraperError = new ScraperError(error.message, {
      code: 'INTERNAL_ERROR',
      url: context.url,
      retryable: false,
      details: { stack: error.stack },
    });

    logger.error(`Internal error in ${context.phase}`, {
      url: context.url,
      company: context.companyName,
      jobId: context.jobId,
      error: error.message,
      stack: error.stack,
    });

    return scraperError;
  }

  const unknownError = new ScraperError('Unknown error occurred', {
    code: 'UNKNOWN',
    url: context.url,
    retryable: false,
  });

  logger.error(`Unknown error in ${context.phase}`, {
    url: context.url,
    company: context.companyName,
    jobId: context.jobId,
  });

  return unknownError;
}

export function isRetryableError(error: unknown): boolean {
  if (error instanceof ScraperError) {
    return error.retryable;
  }
  return false;
}

export function shouldRetry(error: unknown): boolean {
  if (error instanceof RateLimitError) {
    return true;
  }
  if (error instanceof ScraperError) {
    return error.retryable;
  }
  return false;
}

export function formatErrorForStorage(error: unknown): Record<string, unknown> {
  if (error instanceof ScraperError) {
    return {
      message: error.message,
      code: error.code,
      url: error.url,
      retryable: error.retryable,
      details: error.details,
      stack: error.stack,
    };
  }
  
  if (error instanceof Error) {
    return {
      message: error.message,
      name: error.name,
      stack: error.stack,
    };
  }
  
  return {
    message: String(error),
    type: typeof error,
  };
}