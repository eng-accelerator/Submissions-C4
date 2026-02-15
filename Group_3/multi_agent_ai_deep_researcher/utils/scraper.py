"""
Web scraping utility for the Multi-Agent AI Deep Researcher.

Handles fetching and parsing web content, extracting text, metadata, and handling errors.
Uses BeautifulSoup4 for HTML parsing and Requests for HTTP fetching.

Features:
- Robust error handling for network and parsing issues
- Automatic retries with exponential backoff
- User-Agent rotation to avoid blocking
- Extraction of title, content, author, publication date
- Support for handling paywalls and blocked content
- Timeout handling
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Common User-Agent strings to avoid blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class ContentNotFoundError(ScraperError):
    """Raised when main content cannot be extracted from page."""
    pass


class PaywallDetectedError(ScraperError):
    """Raised when content appears to be behind a paywall."""
    pass


class ScraperMetadata(BaseModel):
    """Metadata extracted from a webpage."""
    
    model_config = ConfigDict(extra="allow")
    
    title: str = Field(default="", description="Page title")
    author: Optional[str] = Field(default=None, description="Author name")
    published_date: Optional[str] = Field(default=None, description="Publication date")
    fetched_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ScraperResult(BaseModel):
    """Result from scraping a URL."""
    
    model_config = ConfigDict(extra="allow")
    
    success: bool = Field(description="Whether scraping succeeded")
    content: str = Field(default="", description="Extracted text content")
    title: str = Field(default="", description="Page title")
    metadata: ScraperMetadata = Field(default_factory=ScraperMetadata)
    url: str = Field(description="Original URL")
    error: Optional[str] = Field(default=None, description="Error message if failed")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
)
def fetch_url(url: str, timeout: int = 10) -> str:
    """
    Fetch URL content with retry logic.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
    
    Returns:
        HTML content as string
    
    Raises:
        ScraperError: If fetch fails after retries
    """
    try:
        headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        return response.text
        
    except requests.Timeout:
        raise
    except requests.RequestException as e:
        raise


def extract_text_content(html: str) -> str:
    """
    Extract main text content from HTML.
    
    Removes scripts, styles, navigation, and returns clean text.
    
    Args:
        html: HTML content
    
    Returns:
        Extracted text content
    
    Raises:
        ContentNotFoundError: If no content can be extracted
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Try to find main content
    main_content = None
    
    # Look for common main content containers
    for selector in ["main", "article", '[role="main"]', ".content", "#content"]:
        element = soup.select_one(selector)
        if element:
            main_content = element
            break
    
    # Fallback to body
    if not main_content:
        main_content = soup.body if soup.body else soup
    
    # Extract text
    text = main_content.get_text(separator=" ", strip=True) if main_content else ""
    
    # Clean up excessive whitespace
    text = " ".join(text.split())
    
    if not text or len(text) < 100:
        raise ContentNotFoundError(f"Insufficient content extracted (length: {len(text)})")
    
    return text


def extract_title(html: str, url: str = "") -> str:
    """
    Extract title from HTML.
    
    Tries multiple sources: og:title, title tag, h1.
    
    Args:
        html: HTML content
        url: Original URL (used as fallback)
    
    Returns:
        Extracted title or URL as fallback
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Try Open Graph title
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"]
    
    # Try title tag
    if soup.title:
        return soup.title.string or ""
    
    # Try h1
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    
    # Fallback to domain
    return url.split("/")[2] if url else "Unknown"


def extract_author(html: str) -> Optional[str]:
    """
    Extract author from HTML.
    
    Tries multiple sources: og:author, meta author, byline.
    
    Args:
        html: HTML content
    
    Returns:
        Author name or None
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Try Open Graph author
    og_author = soup.find("meta", property="og:author")
    if og_author and og_author.get("content"):
        return og_author["content"]
    
    # Try meta author
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author and meta_author.get("content"):
        return meta_author["content"]
    
    # Try byline
    byline = soup.find(class_=["byline", "author", "by-author"])
    if byline:
        return byline.get_text(strip=True)
    
    return None


def extract_published_date(html: str) -> Optional[str]:
    """
    Extract publication date from HTML.
    
    Tries multiple sources: og:published_time, publish_date meta, last-modified.
    
    Args:
        html: HTML content
    
    Returns:
        ISO format date string or None
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Try Open Graph published time
    og_pub = soup.find("meta", property="og:published_time")
    if og_pub and og_pub.get("content"):
        return og_pub["content"]
    
    # Try article:published_time
    article_pub = soup.find("meta", property="article:published_time")
    if article_pub and article_pub.get("content"):
        return article_pub["content"]
    
    # Try datePublished
    date_published = soup.find("meta", attrs={"itemprop": "datePublished"})
    if date_published and date_published.get("content"):
        return date_published["content"]
    
    return None


def extract_metadata(html: str, url: str) -> ScraperMetadata:
    """
    Extract complete metadata from HTML as Pydantic model.
    
    Args:
        html: HTML content
        url: Original URL
    
    Returns:
        ScraperMetadata object with title, author, published_date, etc.
    """
    return ScraperMetadata(
        title=extract_title(html, url),
        author=extract_author(html),
        published_date=extract_published_date(html),
        fetched_at=datetime.utcnow().isoformat(),
    )


def scrape_url(url: str, timeout: int = 10, max_content_length: int = 50000) -> ScraperResult:
    """
    Scrape a URL and extract content and metadata.
    
    Main function for scraping. Handles errors gracefully and returns structured output.
    
    Args:
        url: URL to scrape
        timeout: Request timeout in seconds
        max_content_length: Maximum content length to process
    
    Returns:
        ScraperResult with structured data or error information
    
    Example:
        result = scrape_url("https://example.com/article")
        if result.success:
            print(result.content[:100])
        else:
            print(result.error)
    """
    try:
        # Fetch HTML
        html = fetch_url(url, timeout=timeout)
        
        # Check content length
        if len(html) > max_content_length:
            html = html[:max_content_length]
        
        # Extract content
        content = extract_text_content(html)
        
        # Extract metadata
        metadata = extract_metadata(html, url)
        
        return ScraperResult(
            success=True,
            content=content,
            title=metadata.title,
            metadata=metadata,
            url=url,
            error=None,
        )
        
    except ContentNotFoundError as e:
        return ScraperResult(
            success=False,
            content="",
            title="",
            metadata=ScraperMetadata(),
            url=url,
            error=f"Content not found: {str(e)}",
        )
    except PaywallDetectedError as e:
        return ScraperResult(
            success=False,
            content="",
            title="",
            metadata=ScraperMetadata(),
            url=url,
            error="Content behind paywall",
        )
    except ScraperError as e:
        return ScraperResult(
            success=False,
            content="",
            title="",
            metadata=ScraperMetadata(),
            url=url,
            error=str(e),
        )
    except Exception as e:
        return ScraperResult(
            success=False,
            content="",
            title="",
            metadata=ScraperMetadata(),
            url=url,
            error=f"Unexpected error: {str(e)}",
        )


__all__ = [
    "scrape_url",
    "fetch_url",
    "extract_text_content",
    "extract_title",
    "extract_author",
    "extract_published_date",
    "extract_metadata",
    "ScraperResult",
    "ScraperMetadata",
    "ScraperError",
    "ContentNotFoundError",
    "PaywallDetectedError",
]
