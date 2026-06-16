import { normalize, generateNameVariations } from './normalizer';
import { logger } from '../utils/logger';

export interface EntityReference {
  name: string;
  type: 'acronym' | 'full_name' | 'alternative' | 'variation';
  confidence: number;
}

export interface LinkedEntities {
  canonicalName: string;
  references: EntityReference[];
}

// Common acronyms and their expansions
const KNOWN_ACRONYMS: Record<string, string> = {
  'ai': 'Artificial Intelligence',
  'ml': 'Machine Learning',
  'dl': 'Deep Learning',
  'nlp': 'Natural Language Processing',
  'cv': 'Computer Vision',
  'saas': 'Software as a Service',
  'paas': 'Platform as a Service',
  'iaas': 'Infrastructure as a Service',
  'api': 'Application Programming Interface',
  'sdk': 'Software Development Kit',
  'cli': 'Command Line Interface',
  'ui': 'User Interface',
  'ux': 'User Experience',
  'devops': 'Development Operations',
  'secops': 'Security Operations',
  'fintech': 'Financial Technology',
  'edtech': 'Education Technology',
  'healthtech': 'Health Technology',
  'biotech': 'Biotechnology',
  'cleantech': 'Clean Technology',
  'regtech': 'Regulatory Technology',
  'insurtech': 'Insurance Technology',
  'proptech': 'Property Technology',
  'hrtech': 'Human Resources Technology',
  'martech': 'Marketing Technology',
  'adtech': 'Advertising Technology',
  'ecommerce': 'Electronic Commerce',
  'b2b': 'Business to Business',
  'b2c': 'Business to Consumer',
  'iot': 'Internet of Things',
  'blockchain': 'Distributed Ledger Technology',
  'vrar': 'Virtual Reality Augmented Reality',
};

export function extractAcronym(name: string): string | null {
  // Extract potential acronym from name with capitals
  const capitals = name.match(/[A-Z]/g);
  if (capitals && capitals.length >= 2) {
    return capitals.join('');
  }
  
  // Check if name is itself an acronym (all capitals)
  if (name === name.toUpperCase() && name.length >= 2 && name.length <= 10) {
    return name;
  }
  
  return null;
}

export function expandAcronym(acronym: string): string | null {
  const upper = acronym.toLowerCase();
  return KNOWN_ACRONYMS[upper] || null;
}

export function findNameVariations(name: string): string[] {
  const variations: Set<string> = new Set();
  
  // Add the normalized name
  variations.add(normalize(name));
  
  // Add acronym if applicable
  const acronym = extractAcronym(name);
  if (acronym) {
    variations.add(acronym.toLowerCase());
    
    // Add expansion if known
    const expansion = expandAcronym(acronym);
    if (expansion) {
      variations.add(normalize(expansion));
    }
  }
  
  // Add common variations
  const baseName = name
    .replace(/\b(Inc|Corp|Ltd|LLC|Company|Technologies|Solutions|Services|Group|Holdings)\b/gi, '')
    .trim();
  
  if (baseName !== name) {
    variations.add(normalize(baseName));
  }
  
  // Generate pattern-based variations
  const patternVariations = generateNameVariations(name);
  for (const v of patternVariations) {
    variations.add(v);
  }
  
  // Remove empty and filter
  return Array.from(variations).filter(v => v.length > 0 && v !== normalize(name));
}

export function linkEntities(
  names: string[],
  threshold = 0.8
): LinkedEntities[] {
  const linked: LinkedEntities[] = [];
  const processed = new Set<string>();
  
  for (const name of names) {
    if (processed.has(normalize(name))) continue;
    
    const variations = findNameVariations(name);
    const allNames = [name, ...variations];
    
    // Find all matching names
    const references: EntityReference[] = [];
    let canonical = name;
    let maxConfidence = 1;
    
    for (const n of allNames) {
      const norm = normalize(n);
      if (processed.has(norm)) continue;
      
      const isAcronym = extractAcronym(n) === n;
      const isExpansion = expandAcronym(extractAcronym(n) || '') !== null;
      
      let type: EntityReference['type'] = 'variation';
      let confidence = 0.8;
      
      if (isAcronym && !isExpansion) {
        type = 'acronym';
        confidence = 0.9;
      } else if (isExpansion || expandAcronym(extractAcronym(n) || '') !== null) {
        type = 'full_name';
        confidence = 0.9;
      } else if (n !== name) {
        type = 'alternative';
        confidence = 0.85;
      }
      
      references.push({ name: n, type, confidence });
      processed.add(norm);
      
      if (confidence > maxConfidence) {
        canonical = n;
        maxConfidence = confidence;
      }
    }
    
    if (references.length > 1) {
      linked.push({
        canonicalName: canonical,
        references: references.sort((a, b) => b.confidence - a.confidence),
      });
    }
  }
  
  return linked;
}

export function findEntityLinks(
  text: string,
  knownEntities: string[]
): Map<string, string[]> {
  const links = new Map<string, string[]>();
  
  for (const entity of knownEntities) {
    const normEntity = normalize(entity);
    const variations = findNameVariations(entity);
    
    const foundInText: string[] = [];
    
    for (const variation of [entity, ...variations]) {
      if (text.toLowerCase().includes(variation.toLowerCase())) {
        foundInText.push(variation);
      }
    }
    
    if (foundInText.length > 1) {
      links.set(entity, [...new Set(foundInText)]);
    }
  }
  
  return links;
}

export function createEntityGraph(
  companies: Array<{ company_name: string; description?: string }>
): Map<string, Set<string>> {
  const graph = new Map<string, Set<string>>();
  
  for (const company of companies) {
    const name = company.company_name;
    const normName = normalize(name);
    
    if (!graph.has(normName)) {
      graph.set(normName, new Set());
    }
    
    // Find mentions in other descriptions
    for (const other of companies) {
      if (other.company_name === name) continue;
      
      const otherNorm = normalize(other.company_name);
      const variations = findNameVariations(other.company_name);
      
      for (const variant of [other.company_name, ...variations]) {
        if (other.description?.toLowerCase().includes(variant.toLowerCase())) {
          graph.get(normName)!.add(otherNorm);
        }
      }
    }
  }
  
  return graph;
}

export function logEntityLinks(entities: LinkedEntities[]): void {
  logger.debug('Entity links discovered', {
    canonicalCount: entities.length,
    totalReferences: entities.reduce((sum, e) => sum + e.references.length, 0),
  });
}