import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenderScraper:
    """Service for scraping tender/RFP databases from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Keywords to identify climate/sustainability/environment projects
        self.climate_keywords = [
            'climate', 'sustainability', 'environment', 'environmental', 'green', 'renewable',
            'energy', 'carbon', 'emissions', 'biodiversity', 'conservation', 'ecosystem',
            'clean', 'sustainable', 'circular', 'waste', 'recycling', 'pollution',
            'forest', 'ocean', 'marine', 'agriculture', 'food security', 'water',
            'air quality', 'soil', 'wildlife', 'habitat', 'adaptation', 'mitigation'
        ]
        
    def scrape_aus_tenders(self, max_pages: int = 2) -> List[Dict]:
        """Scrape Australian Government tenders from tenders.gov.au"""
        tenders = []
        base_url = "https://www.tenders.gov.au/atm"
        
        try:
            for page in range(1, max_pages + 1):
                url = f"{base_url}?page={page}"
                logger.info(f"Scraping Australian tenders page {page}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find tender listings - try multiple selectors
                    tender_elements = []
                    selectors = [
                        'div.tender-listing',
                        'tr.tender-row', 
                        'div.tender-item',
                        'div.result-item',
                        'div.listing-item',
                        'div[class*="tender"]',
                        'div[class*="result"]'
                    ]
                    
                    for selector in selectors:
                        tender_elements = soup.select(selector)
                        if tender_elements:
                            logger.info(f"Found {len(tender_elements)} elements using selector: {selector}")
                            break
                    
                    if not tender_elements:
                        logger.warning(f"No tender elements found on page {page} with any selector")
                        continue
                    
                    for element in tender_elements:
                        try:
                            tender = self._parse_aus_tender(element)
                            if tender and self._is_climate_related(tender['title'] + ' ' + tender.get('description', '')):
                                tenders.append(tender)
                        except Exception as e:
                            logger.error(f"Error parsing Australian tender: {e}")
                            continue
                    
                    time.sleep(0.5)  # Reduced delay
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error on page {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Australian tenders: {e}")
            
        logger.info(f"Scraped {len(tenders)} climate-related Australian tenders")
        return tenders
    
    def _parse_aus_tender(self, element) -> Optional[Dict]:
        """Parse individual Australian tender element"""
        try:
            # Extract title
            title_elem = element.find('h3') or element.find('h2') or element.find('a', class_='title')
            title = title_elem.get_text(strip=True) if title_elem else 'Untitled'
            
            # Extract description
            desc_elem = element.find('p', class_='description') or element.find('div', class_='summary')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract closing date
            date_elem = element.find('span', class_='closing-date') or element.find('div', class_='date')
            closing_date = date_elem.get_text(strip=True) if date_elem else ''
            
            # Extract organization
            org_elem = element.find('span', class_='agency') or element.find('div', class_='organization')
            organization = org_elem.get_text(strip=True) if org_elem else ''
            
            # Extract link - filter out JavaScript and invalid links
            link_elem = element.find('a', href=True)
            link = link_elem['href'] if link_elem else ''
            
            # Since we're not using links anymore, just set to empty string
            link = ''
            
            return {
                'title': title,
                'description': description,
                'closing_date': closing_date,
                'organization': organization,
                'link': link,
                'source': 'Australian Government Tenders',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing Australian tender element: {e}")
            return None
    
    def scrape_giz_tenders(self, max_pages: int = 2) -> List[Dict]:
        """Scrape GIZ (German Development Agency) tenders"""
        tenders = []
        base_url = "https://ausschreibungen.giz.de/Satellite/company/welcome.do"
        
        try:
            for page in range(1, max_pages + 1):
                params = {
                    'method': 'showTable',
                    'fromSearch': '1',
                    'tableSortPROJECT_RESULT': '1',
                    'tableSortAttributePROJECT_RESULT': 'relevantDate',
                    'selectedTablePagePROJECT_RESULT': page
                }
                
                logger.info(f"Scraping GIZ tenders page {page}")
                
                try:
                    response = self.session.get(base_url, params=params, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find tender table rows
                    table = soup.find('table')
                    if not table:
                        logger.warning(f"No table found on GIZ page {page}")
                        continue
                        
                    rows = table.find_all('tr')[1:]  # Skip header row
                    logger.info(f"Found {len(rows)} rows on GIZ page {page}")
                    
                    for row in rows:
                        try:
                            tender = self._parse_giz_tender(row)
                            if tender and self._is_climate_related(tender['title'] + ' ' + tender.get('description', '')):
                                tenders.append(tender)
                        except Exception as e:
                            logger.error(f"Error parsing GIZ tender: {e}")
                            continue
                    
                    time.sleep(0.5)  # Reduced delay
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error on GIZ page {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping GIZ tenders: {e}")
            
        logger.info(f"Scraped {len(tenders)} climate-related GIZ tenders")
        return tenders
    
    def _parse_giz_tender(self, row) -> Optional[Dict]:
        """Parse individual GIZ tender row"""
        try:
            cells = row.find_all('td')
            if len(cells) < 5:
                return None
            
            # Extract publication date
            pub_date = cells[0].get_text(strip=True) if len(cells) > 0 else ''
            
            # Extract deadline
            deadline = cells[1].get_text(strip=True) if len(cells) > 1 else ''
            
            # Extract title
            title = cells[2].get_text(strip=True) if len(cells) > 2 else 'Untitled'
            
            # Extract type
            tender_type = cells[3].get_text(strip=True) if len(cells) > 3 else ''
            
            # Extract organization
            organization = cells[4].get_text(strip=True) if len(cells) > 4 else 'GIZ'
            
            # Extract link if available - filter out JavaScript and invalid links
            link_elem = row.find('a', href=True)
            link = link_elem['href'] if link_elem else ''
            
            # Since we're not using links anymore, just set to empty string
            link = ''
            
            return {
                'title': title,
                'description': f"Type: {tender_type}",
                'closing_date': deadline,
                'organization': organization,
                'link': link,
                'source': 'GIZ (German Development Agency)',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing GIZ tender row: {e}")
            return None
    
    def _is_climate_related(self, text: str) -> bool:
        """Check if text contains climate/sustainability related keywords"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.climate_keywords)
    
    def scrape_undp_tenders(self, max_pages: int = 2) -> List[Dict]:
        """Scrape UNDP (United Nations Development Programme) procurement notices"""
        tenders = []
        base_url = "https://procurement-notices.undp.org/"
        
        try:
            for page in range(1, max_pages + 1):
                # UNDP uses a different approach - we'll scrape the main page and look for climate-related content
                if page == 1:
                    url = base_url
                else:
                    # For pagination, we might need to adjust based on how UNDP structures their pages
                    url = f"{base_url}?page={page}"
                
                logger.info(f"Scraping UNDP procurement notices page {page}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find tender items - UNDP uses vacanciesTable__row structure
                    tender_items = soup.find_all('a', class_='vacanciesTable__row')
                    
                    if not tender_items:
                        # Fallback to alternative selectors
                        tender_items = soup.find_all('div', class_='tender-item') or soup.find_all('tr') or soup.find_all('div', class_='procurement-notice')
                        if not tender_items:
                            tender_items = soup.find_all('div', {'class': lambda x: x and 'tender' in x.lower()}) or \
                                         soup.find_all('div', {'class': lambda x: x and 'notice' in x.lower()}) or \
                                         soup.find_all('div', {'class': lambda x: x and 'procurement' in x.lower()})
                    
                    logger.info(f"Found {len(tender_items)} potential tender items on UNDP page {page}")
                    
                    for item in tender_items:
                        try:
                            tender = self._parse_undp_tender(item)
                            if tender and self._is_climate_related(tender['title'] + ' ' + tender.get('description', '')):
                                tenders.append(tender)
                        except Exception as e:
                            logger.error(f"Error parsing UNDP tender: {e}")
                            continue
                    
                    time.sleep(0.5)  # Reduced delay
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error on UNDP page {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping UNDP tenders: {e}")
            
        logger.info(f"Scraped {len(tenders)} climate-related UNDP tenders")
        return tenders

    def _parse_undp_tender(self, element) -> Optional[Dict]:
        """Parse individual UNDP tender element"""
        try:
            # UNDP uses vacanciesTable__cell structure
            cells = element.find_all('div', class_='vacanciesTable__cell')
            
            # Initialize variables
            title = 'Untitled'
            ref_number = ''
            organization = 'UNDP'
            process_type = ''
            deadline = ''
            posted_date = ''
            
            # Parse each cell based on its label
            for cell in cells:
                label_elem = cell.find('div', class_='vacanciesTable__cell__label')
                if label_elem:
                    label = label_elem.get_text(strip=True).lower()
                    value_elem = cell.find('span')
                    if value_elem:
                        value = value_elem.get_text(strip=True)
                        
                        if 'title' in label:
                            title = value
                        elif 'ref no' in label:
                            ref_number = value
                        elif 'undp office/country' in label:
                            organization = value
                        elif 'process' in label:
                            process_type = value
                        elif 'deadline' in label:
                            deadline = value
                        elif 'posted' in label:
                            posted_date = value
            
            # Since we're not using links anymore, just set to empty string
            link = ''
            
            # Build description with available information
            full_description = f"Type: {process_type}" if process_type else "Procurement Notice"
            if ref_number:
                full_description += f" | Ref: {ref_number}"
            if posted_date:
                full_description += f" | Posted: {posted_date}"
            
            return {
                'title': title,
                'description': full_description,
                'closing_date': deadline,
                'organization': organization,
                'link': link,
                'source': 'UNDP (United Nations Development Programme)',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing UNDP tender element: {e}")
            return None

    def scrape_all_sources(self) -> Dict[str, List[Dict]]:
        """Scrape all configured tender sources"""
        results = {
            'aus_tenders': [],
            'giz_tenders': [],
            'undp_tenders': [],
            'total_found': 0,
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            # Scrape Australian tenders
            logger.info("Starting Australian tenders scraping...")
            aus_tenders = self.scrape_aus_tenders()
            results['aus_tenders'] = aus_tenders
            logger.info(f"Found {len(aus_tenders)} Australian tenders")
            
            # Scrape GIZ tenders
            logger.info("Starting GIZ tenders scraping...")
            giz_tenders = self.scrape_giz_tenders()
            results['giz_tenders'] = giz_tenders
            logger.info(f"Found {len(giz_tenders)} GIZ tenders")
            
            # Scrape UNDP tenders
            logger.info("Starting UNDP tenders scraping...")
            undp_tenders = self.scrape_undp_tenders()
            results['undp_tenders'] = undp_tenders
            logger.info(f"Found {len(undp_tenders)} UNDP tenders")
            
            # Calculate total
            results['total_found'] = len(aus_tenders) + len(giz_tenders) + len(undp_tenders)
            
            # Add success flag
            results['success'] = True
            results['message'] = f"Successfully scraped {results['total_found']} tenders"
            
        except Exception as e:
            logger.error(f"Error in scrape_all_sources: {e}")
            results['success'] = False
            results['error'] = str(e)
            results['message'] = f"Scraping failed: {str(e)}"
            
        return results
    
    def save_tenders_to_database(self, tenders: List[Dict], db_connection) -> bool:
        """Save scraped tenders to database"""
        try:
            cursor = db_connection.cursor()
            
            for tender in tenders:
                cursor.execute("""
                    INSERT INTO scraped_tenders 
                    (title, description, closing_date, organization, link, source, scraped_at, is_climate_related)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (title, source) DO UPDATE SET
                    description = EXCLUDED.description,
                    closing_date = EXCLUDED.closing_date,
                    organization = EXCLUDED.organization,
                    scraped_at = EXCLUDED.scraped_at
                """, (
                    tender['title'],
                    tender['description'],
                    tender['closing_date'],
                    tender['organization'],
                    tender['link'],
                    tender['source'],
                    tender['scraped_at'],
                    True  # All tenders are pre-filtered for climate relevance
                ))
            
            db_connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving tenders to database: {e}")
            return False
