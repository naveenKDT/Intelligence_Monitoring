import { query } from '../database/connection';
import { logger } from '../utils/logger';
import { ExtractedDocument, DocumentType } from '../scraper/documentExtractor';
import { TextChunk } from '../embedding/chunker';

export interface DocumentRecord {
  id: number;
  company_id: number;
  doc_type: DocumentType;
  title: string;
  url: string;
  content: string;
  published_date?: Date;
  scraped_at: Date;
  embedding?: number[];
}

export interface StoreDocumentResult {
  documentId: number;
  isNew: boolean;
  chunksStored: number;
}

// Check if document already exists
async function documentExists(companyId: number, url: string): Promise<number | null> {
  const result = await query<{ id: number }>(
    'SELECT id FROM company_documents WHERE company_id = $1 AND url = $2',
    [companyId, url]
  );
  return result.rows[0]?.id || null;
}

// Store a single document
export async function storeDocument(
  companyId: number,
  docType: DocumentType,
  title: string,
  url: string,
  content: string,
  embedding?: number[],
  publishedDate?: Date
): Promise<number> {
  // Check if document already exists
  const existingId = await documentExists(companyId, url);
  if (existingId) {
    logger.debug('Document already exists', { id: existingId, url });
    return existingId;
  }
  
  const result = await query<{ id: number }>(
    `INSERT INTO company_documents (
      company_id, doc_type, title, url, content, published_date, embedding
    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING id`,
    [
      companyId,
      docType,
      title.substring(0, 500),
      url.substring(0, 500),
      content,
      publishedDate || null,
      embedding ? `[${embedding.join(',')}]` : null,
    ]
  );
  
  logger.debug('Document stored', {
    id: result.rows[0].id,
    companyId,
    docType,
  });
  
  return result.rows[0].id;
}

// Store document with chunked content and embeddings
export async function storeDocumentWithChunks(
  companyId: number,
  document: ExtractedDocument,
  chunksWithEmbeddings: Array<{ chunk: TextChunk; embedding: number[] }>
): Promise<StoreDocumentResult> {
  let documentId: number;
  let isNew = false;
  
  // Check if document exists
  const existingId = await documentExists(companyId, document.url);
  if (existingId) {
    documentId = existingId;
    isNew = false;
  } else {
    // Store the document with the first chunk's embedding (or no embedding)
    const firstEmbedding = chunksWithEmbeddings[0]?.embedding;
    
    documentId = await storeDocument(
      companyId,
      document.doc_type,
      document.title,
      document.url,
      document.content,
      firstEmbedding,
      document.published_date
    );
    isNew = true;
  }
  
  // Store additional chunk embeddings
  let chunksStored = 0;
  for (let i = 1; i < chunksWithEmbeddings.length; i++) {
    const { chunk, embedding } = chunksWithEmbeddings[i];
    
    if (embedding.length > 0) {
      try {
        await query(
          `INSERT INTO company_documents (
            company_id, doc_type, title, url, content, embedding
          ) VALUES ($1, $2, $3, $4, $5, $6)
          ON CONFLICT (company_id, url) DO NOTHING`,
          [
            companyId,
            document.doc_type,
            `${document.title} (part ${i + 1})`,
            document.url,
            chunk.text,
            `[${embedding.join(',')}]`,
          ]
        );
        chunksStored++;
      } catch (error) {
        logger.debug('Failed to store chunk', { error: (error as Error).message });
      }
    }
  }
  
  return {
    documentId,
    isNew,
    chunksStored,
  };
}

// Store multiple documents for a company
export async function storeDocuments(
  companyId: number,
  documents: ExtractedDocument[],
  chunksWithEmbeddings: Map<string, Array<{ chunk: TextChunk; embedding: number[] }>>
): Promise<{
  totalDocuments: number;
  newDocuments: number;
  totalChunks: number;
}> {
  let newDocuments = 0;
  let totalChunks = 0;
  
  for (const doc of documents) {
    const chunks = chunksWithEmbeddings.get(doc.url);
    if (chunks) {
      const result = await storeDocumentWithChunks(companyId, doc, chunks);
      if (result.isNew) newDocuments++;
      totalChunks += result.chunksStored;
    }
  }
  
  return {
    totalDocuments: documents.length,
    newDocuments,
    totalChunks,
  };
}

// Get documents by company
export async function getDocumentsByCompany(
  companyId: number,
  limit = 100
): Promise<DocumentRecord[]> {
  const result = await query<DocumentRecord>(
    `SELECT * FROM company_documents 
     WHERE company_id = $1
     ORDER BY scraped_at DESC
     LIMIT $2`,
    [companyId, limit]
  );
  
  return result.rows;
}

// Get document count by company
export async function getDocumentCount(companyId: number): Promise<number> {
  const result = await query<{ count: string }>(
    'SELECT COUNT(*) as count FROM company_documents WHERE company_id = $1',
    [companyId]
  );
  return parseInt(result.rows[0].count, 10);
}

// Get document count by type
export async function getDocumentCountByType(): Promise<Record<DocumentType, number>> {
  const result = await query<{ doc_type: string; count: string }>(
    'SELECT doc_type, COUNT(*) as count FROM company_documents GROUP BY doc_type'
  );
  
  const counts: Record<string, number> = {};
  for (const row of result.rows) {
    counts[row.doc_type] = parseInt(row.count, 10);
  }
  
  return counts as Record<DocumentType, number>;
}

// Search documents by content
export async function searchDocuments(
  searchTerm: string,
  limit = 20
): Promise<DocumentRecord[]> {
  const result = await query<DocumentRecord>(
    `SELECT * FROM company_documents 
     WHERE content ILIKE $1 OR title ILIKE $1
     ORDER BY scraped_at DESC
     LIMIT $2`,
    [`%${searchTerm}%`, limit]
  );
  
  return result.rows;
}

// Find similar documents using vector similarity
export async function findSimilarDocuments(
  embedding: number[],
  limit = 5,
  minSimilarity = 0.7
): Promise<Array<{ document: DocumentRecord; similarity: number }>> {
  const embeddingStr = `[${embedding.join(',')}]`;
  
  const result = await query<DocumentRecord & { similarity: number }>(
    `SELECT *, 
            1 - (embedding <=> $1::vector) as similarity
     FROM company_documents
     WHERE embedding IS NOT NULL
     AND 1 - (embedding <=> $1::vector) > $2
     ORDER BY embedding <=> $1::vector
     LIMIT $3`,
    [embeddingStr, minSimilarity, limit]
  );
  
  return result.rows.map(row => ({
    document: row,
    similarity: row.similarity,
  }));
}

// Delete documents by company
export async function deleteDocumentsByCompany(companyId: number): Promise<number> {
  const result = await query(
    'DELETE FROM company_documents WHERE company_id = $1',
    [companyId]
  );
  
  return result.rowCount || 0;
}

// Get total document count
export async function getTotalDocumentCount(): Promise<number> {
  const result = await query<{ count: string }>(
    'SELECT COUNT(*) as count FROM company_documents'
  );
  return parseInt(result.rows[0].count, 10);
}

// Get total embeddings count
export async function getTotalEmbeddingsCount(): Promise<number> {
  const result = await query<{ count: string }>(
    'SELECT COUNT(*) as count FROM company_documents WHERE embedding IS NOT NULL'
  );
  return parseInt(result.rows[0].count, 10);
}

// Update document embedding
export async function updateDocumentEmbedding(
  documentId: number,
  embedding: number[]
): Promise<void> {
  await query(
    'UPDATE company_documents SET embedding = $1 WHERE id = $2',
    [`[${embedding.join(',')}]`, documentId]
  );
}

// Get documents without embeddings
export async function getDocumentsWithoutEmbeddings(limit = 100): Promise<DocumentRecord[]> {
  const result = await query<DocumentRecord>(
    `SELECT * FROM company_documents 
     WHERE embedding IS NULL AND content IS NOT NULL
     ORDER BY scraped_at ASC
     LIMIT $1`,
    [limit]
  );
  
  return result.rows;
}

// Batch update embeddings
export async function batchUpdateEmbeddings(
  updates: Array<{ documentId: number; embedding: number[] }>
): Promise<number> {
  let updated = 0;
  
  for (const { documentId, embedding } of updates) {
    try {
      await updateDocumentEmbedding(documentId, embedding);
      updated++;
    } catch (error) {
      logger.debug('Failed to update embedding', {
        documentId,
        error: (error as Error).message,
      });
    }
  }
  
  return updated;
}