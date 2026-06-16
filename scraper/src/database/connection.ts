import { Pool, PoolClient, QueryResult, QueryResultRow } from 'pg';
import { getConfig } from '../config';
import { logger } from '../utils/logger';

let pool: Pool | null = null;

export async function initializePool(): Promise<Pool> {
  if (pool) {
    return pool;
  }

  const config = getConfig();

  pool = new Pool({
    host: config.database.host,
    port: config.database.port,
    database: config.database.database,
    user: config.database.user,
    password: config.database.password,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  });

  pool.on('error', (err) => {
    logger.error('Unexpected database pool error', { error: err.message });
  });

  pool.on('connect', () => {
    logger.debug('New database connection established');
  });

  // Test the connection
  try {
    const client = await pool.connect();
    await client.query('SELECT 1');
    client.release();
    logger.info('Database connection established successfully');
  } catch (error) {
    logger.error('Failed to connect to database', { error: (error as Error).message });
    throw error;
  }

  return pool;
}

export async function getPool(): Promise<Pool> {
  if (!pool) {
    return initializePool();
  }
  return pool;
}

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string,
  params?: unknown[]
): Promise<QueryResult<T>> {
  const p = await getPool();
  const start = Date.now();
  
  try {
    const result = await p.query<T>(text, params);
    const duration = Date.now() - start;
    
    logger.debug('Query executed', {
      text: text.substring(0, 100),
      duration: `${duration}ms`,
      rows: result.rowCount,
    });
    
    return result;
  } catch (error) {
    logger.error('Query failed', {
      text: text.substring(0, 100),
      error: (error as Error).message,
      params,
    });
    throw error;
  }
}

export async function getClient(): Promise<PoolClient> {
  const p = await getPool();
  return p.connect();
}

export async function transaction<T>(
  callback: (client: PoolClient) => Promise<T>
): Promise<T> {
  const client = await getClient();
  
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

export async function closePool(): Promise<void> {
  if (pool) {
    await pool.end();
    pool = null;
    logger.info('Database pool closed');
  }
}

// For use in non-async contexts (e.g., module initialization)
export function getPoolSync(): Pool | null {
  return pool;
}