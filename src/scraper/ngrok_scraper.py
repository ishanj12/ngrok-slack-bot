import os
import json
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from typing import Set, Dict, List


class NgrokDocsScraper:
    def __init__(self, base_url: str = "https://ngrok.com/docs", output_dir: str = "data/raw"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.visited_urls: Set[str] = set()
        self.scraped_docs: List[Dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.doc_urls = [
            "https://ngrok.com/docs",
            "https://ngrok.com/docs/how-ngrok-works",
            "https://ngrok.com/docs/why-ngrok",
            "https://ngrok.com/docs/agent",
            "https://ngrok.com/docs/agent/config",
            "https://ngrok.com/docs/cloud-edge",
            "https://ngrok.com/docs/http",
            "https://ngrok.com/docs/tcp",
            "https://ngrok.com/docs/tls",
            "https://ngrok.com/docs/api",
            "https://ngrok.com/docs/integrations",
            "https://ngrok.com/docs/getting-started",
            "https://ngrok.com/docs/using-ngrok-with",
        ]
        
        os.makedirs(output_dir, exist_ok=True)
    
    def is_valid_docs_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return (
            parsed.netloc == 'ngrok.com' and
            parsed.path.startswith('/docs') and
            url not in self.visited_urls and
            '#' not in url
        )
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict:
        content = {
            'url': url,
            'title': '',
            'headings': [],
            'content': '',
            'code_blocks': [],
            'yaml_examples': [],
            'links': []
        }
        
        title_tag = soup.find('h1')
        if title_tag:
            content['title'] = title_tag.get_text(strip=True)
        
        if not title_tag:
            title_tag = soup.find('title')
            if title_tag:
                content['title'] = title_tag.get_text(strip=True).replace(' | ngrok', '').strip()
        
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', {'role': 'main'}) or
            soup.find('div', class_='content') or
            soup.find('body')
        )
        
        if main_content:
            for nav in main_content.find_all(['nav', 'header', 'footer']):
                nav.decompose()
            
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                content['headings'].append({
                    'level': heading.name,
                    'text': heading.get_text(strip=True)
                })
            
            for code in main_content.find_all('code'):
                code_text = code.get_text().strip()
                if code_text and len(code_text) > 5:
                    content['code_blocks'].append(code_text)
                    
                    if 'yaml' in str(code.get('class', [])) or code_text.strip().startswith(('---', 'apiVersion:', 'kind:')):
                        content['yaml_examples'].append(code_text)
            
            for pre in main_content.find_all('pre'):
                code = pre.find('code')
                if code:
                    code_text = code.get_text().strip()
                    if code_text and code_text not in content['code_blocks'] and len(code_text) > 5:
                        content['code_blocks'].append(code_text)
                        
                        if 'yaml' in str(pre.get('class', [])) or 'yaml' in str(code.get('class', [])):
                            content['yaml_examples'].append(code_text)
                elif pre.get_text().strip():
                    code_text = pre.get_text().strip()
                    if len(code_text) > 5:
                        content['code_blocks'].append(code_text)
            
            paragraphs = main_content.find_all(['p', 'li'])
            text_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    text_parts.append(text)
            
            if not text_parts:
                text_parts = [s for s in main_content.stripped_strings]
            
            content['content'] = '\n\n'.join(text_parts)
            
            for link in main_content.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if self.is_valid_docs_url(full_url):
                    content['links'].append(full_url)
        
        return content
    
    def scrape_page(self, url: str) -> None:
        if url in self.visited_urls:
            return
        
        print(f"Scraping: {url}")
        self.visited_urls.add(url)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            content = self.extract_content(soup, url)
            self.scraped_docs.append(content)
            
            time.sleep(1)
            
            for link_url in content['links']:
                if link_url not in self.visited_urls:
                    self.scrape_page(link_url)
        
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
    
    def save_to_json(self, filename: str = "ngrok_docs.json"):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_docs, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(self.scraped_docs)} documents to {filepath}")
    
    def save_to_markdown(self):
        md_dir = os.path.join(self.output_dir, 'markdown')
        os.makedirs(md_dir, exist_ok=True)
        
        for idx, doc in enumerate(self.scraped_docs):
            filename = f"doc_{idx:03d}.md"
            filepath = os.path.join(md_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {doc['title']}\n\n")
                f.write(f"**Source URL:** {doc['url']}\n\n")
                f.write("---\n\n")
                
                if doc['headings']:
                    f.write("## Table of Contents\n\n")
                    for heading in doc['headings']:
                        indent = "  " * (int(heading['level'][1]) - 2)
                        f.write(f"{indent}- {heading['text']}\n")
                    f.write("\n---\n\n")
                
                f.write("## Content\n\n")
                f.write(doc['content'])
                f.write("\n\n")
                
                if doc['code_blocks']:
                    f.write("---\n\n")
                    f.write(f"## Code Examples ({len(doc['code_blocks'])})\n\n")
                    for i, code in enumerate(doc['code_blocks'][:10], 1):
                        f.write(f"### Example {i}\n\n")
                        f.write("```\n")
                        f.write(code)
                        f.write("\n```\n\n")
        
        print(f"Saved {len(self.scraped_docs)} markdown files to {md_dir}")
    
    def run(self, max_pages: int = 100):
        print(f"Starting scrape of ngrok documentation from {self.base_url}")
        print(f"Maximum pages to scrape: {max_pages}")
        print("-" * 60)
        
        for url in self.doc_urls[:max_pages]:
            if url not in self.visited_urls:
                self.scrape_page(url)
        
        if len(self.scraped_docs) >= max_pages:
            self.scraped_docs = self.scraped_docs[:max_pages]
        
        print("\n" + "=" * 60)
        print(f"Scraping complete! Total pages scraped: {len(self.scraped_docs)}")
        print("=" * 60)
        
        self.save_to_json()
        self.save_to_markdown()
        
        print(f"\nStatistics:")
        print(f"  - Total pages: {len(self.scraped_docs)}")
        print(f"  - Total code blocks: {sum(len(doc['code_blocks']) for doc in self.scraped_docs)}")
        print(f"  - Total YAML examples: {sum(len(doc['yaml_examples']) for doc in self.scraped_docs)}")


if __name__ == "__main__":
    scraper = NgrokDocsScraper()
    scraper.run(max_pages=100)
