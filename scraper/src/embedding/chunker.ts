import { logger } from '../utils/logger';

export interface TextChunk {
  text: string;
  chunkIndex: number;
  totalChunks: number;
  originalUrl: string;
  originalTitle: string;
  startChar: number;
  endChar: number;
}

export interface ChunkerConfig {
  chunkSize: number;
  chunkOverlap: number;
  minChunkSize: number;
  maxChunkSize: number;
}

const DEFAULT_CONFIG: ChunkerConfig = {
  chunkSize: 500,
  chunkOverlap: 50,
  minChunkSize: 100,
  maxChunkSize: 1000,
};

export function splitIntoSentences(text: string): string[] {
  // Split on sentence boundaries
  const sentencePattern = /[^.!?]+[.!?]+/g;
  const matches = text.match(sentencePattern) || [];
  
  if (matches.length === 0 && text.length > 0) {
    return [text];
  }
  
  return matches.map(s => s.trim()).filter(s => s.length > 0);
}

export function splitIntoParagraphs(text: string): string[] {
  return text
    .split(/\n\s*\n/)
    .map(p => p.trim())
    .filter(p => p.length > 0);
}

export function countWords(text: string): number {
  return text.split(/\s+/).filter(w => w.length > 0).length;
}

export function chunkText(
  text: string,
  config: Partial<ChunkerConfig> = {}
): TextChunk[] {
  const cfg = { ...DEFAULT_CONFIG, ...config };
  const chunks: TextChunk[] = [];
  
  if (!text || text.trim().length === 0) {
    return chunks;
  }
  
  // Clean the text
  const cleanText = text
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/\t/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  
  const sentences = splitIntoSentences(cleanText);
  let currentChunk = '';
  let chunkIndex = 0;
  let startChar = 0;
  
  for (const sentence of sentences) {
    const wordsInCurrent = countWords(currentChunk);
    const wordsInSentence = countWords(sentence);
    
    // If adding this sentence would exceed chunk size
    if (wordsInCurrent + wordsInSentence > cfg.chunkSize && currentChunk.length > 0) {
      // Save the current chunk
      chunks.push({
        text: currentChunk.trim(),
        chunkIndex,
        totalChunks: 0, // Will be updated later
        originalUrl: '',
        originalTitle: '',
        startChar,
        endChar: startChar + currentChunk.length,
      });
      
      chunkIndex++;
      
      // Start new chunk with overlap
      const overlapText = getOverlapText(currentChunk, cfg.chunkOverlap);
      currentChunk = overlapText + ' ' + sentence;
      startChar = startChar + currentChunk.length - sentence.length - overlapText.length;
      
    } else {
      if (currentChunk.length > 0) {
        currentChunk += ' ';
      }
      currentChunk += sentence;
    }
  }
  
  // Add the last chunk
  if (currentChunk.trim().length >= cfg.minChunkSize) {
    chunks.push({
      text: currentChunk.trim(),
      chunkIndex,
      totalChunks: 0,
      originalUrl: '',
      originalTitle: '',
      startChar,
      endChar: startChar + currentChunk.length,
    });
  }
  
  // Update totalChunks for all chunks
  const totalChunks = chunks.length;
  chunks.forEach(chunk => {
    chunk.totalChunks = totalChunks;
  });
  
  logger.debug('Text chunked', {
    originalLength: text.length,
    chunkCount: chunks.length,
    avgChunkSize: Math.round(chunks.reduce((sum, c) => sum + countWords(c.text), 0) / Math.max(chunks.length, 1)),
  });
  
  return chunks;
}

function getOverlapText(text: string, overlapChars: number): string {
  if (text.length <= overlapChars) {
    return text;
  }
  
  // Find a good break point (end of sentence or word boundary)
  const overlapSection = text.substring(text.length - overlapChars);
  const sentenceBreak = overlapSection.search(/[.!?]\s+[A-Z]/);
  
  if (sentenceBreak !== -1) {
    return overlapSection.substring(sentenceBreak + 2).trim();
  }
  
  // Fall back to word boundary
  const wordBreak = overlapSection.search(/\s+\S*$/);
  if (wordBreak !== -1) {
    return overlapSection.substring(wordBreak).trim();
  }
  
  return overlapSection.trim();
}

export function chunkDocument(
  content: string,
  url: string,
  title: string,
  config: Partial<ChunkerConfig> = {}
): TextChunk[] {
  const chunks = chunkText(content, config);
  
  // Add metadata to chunks
  return chunks.map(chunk => ({
    ...chunk,
    originalUrl: url,
    originalTitle: title,
  }));
}

export function validateChunk(chunk: TextChunk): boolean {
  const wordCount = countWords(chunk.text);
  
  return (
    chunk.text.length > 0 &&
    wordCount >= 10 &&
    chunk.chunkIndex >= 0 &&
    chunk.totalChunks > 0 &&
    chunk.startChar >= 0 &&
    chunk.endChar > chunk.startChar
  );
}

export function mergeSmallChunks(
  chunks: TextChunk[],
  minSize = 100
): TextChunk[] {
  if (chunks.length <= 1) return chunks;
  
  const merged: TextChunk[] = [];
  let buffer: TextChunk | null = null;
  
  for (const chunk of chunks) {
    if (!buffer) {
      buffer = { ...chunk };
      continue;
    }
    
    if (countWords(buffer.text) < minSize) {
      // Merge with next chunk
      buffer.text += ' ' + chunk.text;
      buffer.endChar = chunk.endChar;
    } else {
      merged.push(buffer);
      buffer = { ...chunk };
    }
  }
  
  if (buffer) {
    merged.push(buffer);
  }
  
  // Recalculate chunk indices
  merged.forEach((chunk, index) => {
    chunk.chunkIndex = index;
    chunk.totalChunks = merged.length;
  });
  
  return merged;
}

export function truncateChunk(chunk: TextChunk, maxChars: number): TextChunk {
  if (chunk.text.length <= maxChars) {
    return chunk;
  }
  
  return {
    ...chunk,
    text: chunk.text.substring(0, maxChars) + '...',
    endChar: chunk.startChar + maxChars,
  };
}

export function getChunkStats(chunks: TextChunk[]): {
  totalChunks: number;
  totalWords: number;
  avgChunkSize: number;
  minChunkSize: number;
  maxChunkSize: number;
} {
  if (chunks.length === 0) {
    return {
      totalChunks: 0,
      totalWords: 0,
      avgChunkSize: 0,
      minChunkSize: 0,
      maxChunkSize: 0,
    };
  }
  
  const wordCounts = chunks.map(c => countWords(c.text));
  
  return {
    totalChunks: chunks.length,
    totalWords: wordCounts.reduce((sum, w) => sum + w, 0),
    avgChunkSize: Math.round(wordCounts.reduce((sum, w) => sum + w, 0) / chunks.length),
    minChunkSize: Math.min(...wordCounts),
    maxChunkSize: Math.max(...wordCounts),
  };
}