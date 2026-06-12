from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
import re
from app.core.config import settings


class CompanyScraper:
    """
    Web scraper for company websites using Playwright and BeautifulSoup.
    """
    
    def __init__(self):
        self.timeout = settings.SCRAPE_TIMEOUT * 1000  # Convert to milliseconds
        self.max_retries = settings.SCRAPE_MAX_RETRIES
    
    def scrape(self, url: str) -> Optional[Dict]:
        """
        Scrape a company website and extract information.
        """
        try:
            # Try Playwright first for dynamic content
            data = self._scrape_with_playwright(url)
            
            if not data or not data.get("text_content"):
                # Fall back to requests + BeautifulSoup
                data = self._scrape_with_requests(url)
            
            return data
            
        except Exception as e:
            print(f"Scraping error for {url}: {str(e)}")
            return None
    
    def _scrape_with_playwright(self, url: str) -> Optional[Dict]:
        """
        Scrape using Playwright for JavaScript-rendered content.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(url, timeout=self.timeout, wait_until="networkidle")
                
                # Get page title
                title = page.title()
                
                # Get meta description
                description = page.meta("description") or ""
                
                # Get main content
                text_content = self._extract_text_content(page.content())
                
                # Extract structured data
                data = {
                    "url": url,
                    "title": title,
                    "description": description,
                    "text_content": text_content,
                    "links": self._extract_links(page, url),
                    "images": self._extract_images(page)
                }
                
                return data
                
            except Exception as e:
                print(f"Playwright error: {str(e)}")
                return None
            finally:
                browser.close()
    
    def _scrape_with_requests(self, url: str) -> Optional[Dict]:
        """
        Scrape using requests and BeautifulSoup.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=settings.SCRAPE_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "lxml")
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Get title
            title_tag = soup.find("title")
            title = title_tag.get_text().strip() if title_tag else ""
            
            # Get meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            description = meta_desc.get("content", "") if meta_desc else ""
            
            # Get main content
            main_content = soup.find("main") or soup.find("article") or soup.find("body")
            text_content = main_content.get_text(separator="\n", strip=True) if main_content else ""
            
            # Extract links
            links = []
            for a in soup.find_all("a", href=True):
                href = urljoin(url, a["href"])
                text = a.get_text().strip()
                if text and len(text) < 200:
                    links.append({"url": href, "text": text})
            
            return {
                "url": url,
                "title": title,
                "description": description,
                "text_content": text_content[:50000],  # Limit content size
                "links": links[:100],  # Limit number of links
                "images": []
            }
            
        except Exception as e:
            print(f"Requests error: {str(e)}")
            return None
    
    def _extract_text_content(self, html: str) -> str:
        """
        Extract clean text content from HTML.
        """
        soup = BeautifulSoup(html, "lxml")
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()
        
        # Get main content
        main = soup.find("main") or soup.find("article") or soup.find("div", class_=re.compile(r"content|main|text"))
        
        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)[:50000]  # Limit content size
    
    def _extract_links(self, page, base_url: str) -> List[Dict]:
        """
        Extract relevant links from the page.
        """
        links = []
        for a in page.query_selector_all("a[href]"):
            href = a.get_attribute("href")
            if href:
                full_url = urljoin(base_url, href)
                text = a.inner_text().strip()
                if text and len(text) < 200:
                    links.append({"url": full_url, "text": text})
        return links[:100]
    
    def _extract_images(self, page) -> List[Dict]:
        """
        Extract image URLs from the page.
        """
        images = []
        for img in page.query_selector_all("img[src]"):
            src = img.get_attribute("src")
            alt = img.get_attribute("alt") or ""
            if src:
                images.append({"url": src, "alt": alt})
        return images[:50]
    
    def scrape_document(self, url: str) -> Optional[Dict]:
        """
        Scrape a document (PDF, whitepaper, etc.).
        """
        # For now, just return the URL
        # In production, would download and extract text from PDF
        return {
            "url": url,
            "type": "document",
            "content": None
        }


class ContentExtractor:
    """
    Extract structured content from raw text using patterns and heuristics.
    """
    
    @staticmethod
    def extract_company_name(text: str) -> Optional[str]:
        """Extract company name from text."""
        patterns = [
            r"^([A-Z][A-Za-z\s&]+(?:Inc|LLC|Corp|Ltd| GmbH|Co\.))",
            r"Company:\s*([^\n]+)",
            r"^#\s+(.+)$",  # Markdown heading
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return None
    
    @staticmethod
    def extract_contact_info(text: str) -> Dict:
        """Extract contact information from text."""
        info = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            info["emails"] = emails
        
        # Phone pattern
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            info["phones"] = phones
        
        # Address pattern
        address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)'
        addresses = re.findall(address_pattern, text, re.IGNORECASE)
        if addresses:
            info["addresses"] = addresses
        
        return info
    
    @staticmethod
    def extract_social_media(text: str) -> Dict:
        """Extract social media links."""
        social = {}
        
        patterns = {
            "linkedin": r'linkedin\.com/in/([\w-]+)',
            "twitter": r'twitter\.com/([\w-]+)',
            "facebook": r'facebook\.com/([\w-]+)',
            "github": r'github\.com/([\w-]+)',
        }
        
        for platform, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                social[platform] = match.group(0)
        
        return social
    
    @staticmethod
    def extract_technology_keywords(text: str) -> List[str]:
        """Extract technology keywords from text."""
        tech_keywords = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring",
            "AWS", "Azure", "GCP", "Kubernetes", "Docker", "Terraform",
            "Machine Learning", "Deep Learning", "AI", "NLP", "Computer Vision",
            "IoT", "Edge Computing", "5G", "Blockchain", "Cloud",
            "REST", "GraphQL", "gRPC", "Microservices", "Serverless",
            "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Kafka",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy"
        ]
        
        found = []
        text_lower = text.lower()
        
        for tech in tech_keywords:
            if tech.lower() in text_lower:
                found.append(tech)
        
        return found
    
    @staticmethod
    def extract_metrics(text: str) -> Dict:
        """Extract business metrics from text."""
        metrics = {}
        
        # Employee count patterns
        employee_patterns = [
            r'(\d+,?\d*)\s*(?:employees|employees|team members|staff)',
            r'company size[:\s]+(\d+,?\d*)',
        ]
        
        for pattern in employee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics["employees"] = int(match.group(1).replace(",", ""))
                break
        
        # Revenue patterns
        revenue_patterns = [
            r'revenue[:\s]+\$?(\d+(?:\.\d+)?)\s*(?:million|billion|M|B)?',
            r'(\d+(?:\.\d+)?)\s*(?:million|billion)\s*(?:in\s+)?revenue',
        ]
        
        for pattern in revenue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics["revenue"] = float(match.group(1))
                break
        
        # Year founded
        year_pattern = r'(?:founded|established|since)\s+(?:in\s+)?(\d{4})'
        match = re.search(year_pattern, text, re.IGNORECASE)
        if match:
            metrics["founded_year"] = int(match.group(1))
        
        return metrics


class DocumentExtractor:
    """
    Extract content from various document formats.
    """
    
    @staticmethod
    def extract_from_pdf(file_path: str) -> Optional[str]:
        """Extract text from PDF."""
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text
            
        except Exception as e:
            print(f"PDF extraction error: {str(e)}")
            return None
    
    @staticmethod
    def extract_from_docx(file_path: str) -> Optional[str]:
        """Extract text from DOCX."""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            
            return text
            
        except Exception as e:
            print(f"DOCX extraction error: {str(e)}")
            return None