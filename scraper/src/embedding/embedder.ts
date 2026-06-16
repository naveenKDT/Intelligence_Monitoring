import OpenAI from 'openai';
import { getConfig } from '../config';
import { logger } from '../utils/logger';
import { delay } from '../utils/delays';
import { TextChunk } from './chunker';

export interface EmbeddingResult {
  embedding: number[];
  tokens: number;
  model: string;
  cached: boolean;
}

export interface BatchEmbeddingResult {
  results: EmbeddingResult[];
  totalTokens: number;
  totalCost: number;
  cached: number;
}

// Cost per 1M tokens for text-embedding-3-small
const EMBEDDING_COST_PER_1M_TOKENS = 0.02;

let openaiClient: OpenAI | null = null;

function getOpenAIClient(): OpenAI {
  if (!openaiClient) {
    const config = getConfig();
    openaiClient = new OpenAI({
      apiKey: config.openai.apiKey,
    });
  }
  return openaiClient;
}

// Simple token estimation (OpenAI uses ~4 chars per token on average)
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

export async function generateEmbedding(
  text: string,
  model = 'text-embedding-3-small'
): Promise<EmbeddingResult> {
  if (!text || text.trim().length === 0) {
    return {
      embedding: [],
      tokens: 0,
      model,
      cached: false,
    };
  }
  
  // Truncate if too long (8191 tokens max)
  const maxChars = 8191 * 4;
  const truncatedText = text.length > maxChars ? text.substring(0, maxChars) : text;
  
  const tokens = estimateTokens(truncatedText);
  
  try {
    const client = getOpenAIClient();
    
    const response = await client.embeddings.create({
      model,
      input: truncatedText,
    });
    
    const embedding = response.data[0]?.embedding;
    
    if (!embedding) {
      throw new Error('No embedding returned from OpenAI');
    }
    
    logger.debug('Embedding generated', {
      model,
      tokens,
      dimensions: embedding.length,
    });
    
    return {
      embedding,
      tokens,
      model,
      cached: false,
    };
    
  } catch (error) {
    logger.error('Failed to generate embedding', {
      error: (error as Error).message,
      textLength: truncatedText.length,
    });
    throw error;
  }
}

export async function generateBatchEmbeddings(
  texts: string[],
  model = 'text-embedding-3-small',
  batchSize = 100
): Promise<BatchEmbeddingResult> {
  const results: EmbeddingResult[] = [];
  let totalTokens = 0;
  let cachedCount = 0;
  
  // Process in batches
  for (let i = 0; i < texts.length; i += batchSize) {
    const batch = texts.slice(i, i + batchSize);
    
    try {
      const client = getOpenAIClient();
      
      // Filter out empty texts
      const validBatch = batch.filter(t => t.trim().length > 0);
      if (validBatch.length === 0) continue;
      
      const response = await client.embeddings.create({
        model,
        input: validBatch.map(t => t.substring(0, 8191 * 4)),
      });
      
      for (let i = 0; i < response.data.length; i++) {
        const data = response.data[i];
        const tokens = estimateTokens(''); // Approximate tokens for batch
        results.push({
          embedding: data.embedding,
          tokens,
          model,
          cached: false, // Batch API doesn't indicate cache per-item
        });
        totalTokens += tokens;
      }
      
      logger.debug('Batch embeddings generated', {
        batchIndex: Math.floor(i / batchSize) + 1,
        batchSize: validBatch.length,
        totalSoFar: results.length,
      });
      
      // Rate limiting - be nice to OpenAI
      if (i + batchSize < texts.length) {
        await delay(100); // Small delay between batches
      }
      
    } catch (error) {
      logger.error('Batch embedding failed', {
        batchIndex: Math.floor(i / batchSize) + 1,
        error: (error as Error).message,
      });
      
      // Add empty embeddings for failed items
      for (let j = 0; j < batch.length; j++) {
        results.push({
          embedding: [],
          tokens: 0,
          model,
          cached: false,
        });
      }
    }
  }
  
  const totalCost = (totalTokens / 1_000_000) * EMBEDDING_COST_PER_1M_TOKENS;
  
  logger.info('Batch embedding complete', {
    totalTexts: texts.length,
    successfulEmbeddings: results.filter(r => r.embedding.length > 0).length,
    totalTokens,
    estimatedCost: `$${totalCost.toFixed(4)}`,
  });
  
  return {
    results,
    totalTokens,
    totalCost,
    cached: cachedCount,
  };
}

export async function embedChunks(
  chunks: TextChunk[],
  model = 'text-embedding-3-small'
): Promise<Array<{ chunk: TextChunk; embedding: number[]; tokens: number }>> {
  const texts = chunks.map(c => c.text);
  const batchResult = await generateBatchEmbeddings(texts, model);
  
  return chunks.map((chunk, index) => ({
    chunk,
    embedding: batchResult.results[index]?.embedding || [],
    tokens: batchResult.results[index]?.tokens || 0,
  }));
}

export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) {
    throw new Error('Vectors must have the same dimension');
  }
  
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  
  normA = Math.sqrt(normA);
  normB = Math.sqrt(normB);
  
  if (normA === 0 || normB === 0) {
    return 0;
  }
  
  return dotProduct / (normA * normB);
}

export function findSimilarChunks(
  queryEmbedding: number[],
  chunksWithEmbeddings: Array<{ chunk: TextChunk; embedding: number[] }>,
  topK = 5
): Array<{ chunk: TextChunk; similarity: number }> {
  const similarities = chunksWithEmbeddings.map(({ chunk, embedding }) => ({
    chunk,
    similarity: cosineSimilarity(queryEmbedding, embedding),
  }));
  
  return similarities
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, topK);
}

export interface EmbeddingStats {
  totalEmbeddings: number;
  totalTokens: number;
  estimatedCost: number;
  avgTokensPerEmbedding: number;
}

export function calculateEmbeddingStats(
  results: EmbeddingResult[]
): EmbeddingStats {
  const successful = results.filter(r => r.embedding.length > 0);
  const totalTokens = results.reduce((sum, r) => sum + r.tokens, 0);
  
  return {
    totalEmbeddings: successful.length,
    totalTokens,
    estimatedCost: (totalTokens / 1_000_000) * EMBEDDING_COST_PER_1M_TOKENS,
    avgTokensPerEmbedding: successful.length > 0
      ? Math.round(totalTokens / successful.length)
      : 0,
  };
}

export function formatCost(cost: number): string {
  if (cost < 0.01) {
    return `$${(cost * 1000).toFixed(2)}m`;
  }
  return `$${cost.toFixed(4)}`;
}

// Cache for embeddings (in-memory, for session)
const embeddingCache = new Map<string, number[]>();

export function getCacheKey(text: string): string {
  // Simple hash for cache key
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return `embed_${Math.abs(hash)}_${text.length}`;
}

export async function generateEmbeddingCached(
  text: string,
  model = 'text-embedding-3-small'
): Promise<EmbeddingResult> {
  const cacheKey = getCacheKey(text);
  
  if (embeddingCache.has(cacheKey)) {
    return {
      embedding: embeddingCache.get(cacheKey)!,
      tokens: estimateTokens(text),
      model,
      cached: true,
    };
  }
  
  const result = await generateEmbedding(text, model);
  
  if (result.embedding.length > 0) {
    embeddingCache.set(cacheKey, result.embedding);
  }
  
  return result;
}

export function clearCache(): void {
  embeddingCache.clear();
  logger.info('Embedding cache cleared');
}

export function getCacheSize(): number {
  return embeddingCache.size;
}