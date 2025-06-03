import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from datetime import datetime
import json
import os

class TVScheduleScraper:
    def __init__(self, base_url):
        """
        Initialize the TV schedule scraper with the base URL of the TV guide website.
        
        Args:
            base_url (str): The base URL of the TV guide website
        """
        self.base_url = base_url.rstrip('/') # Remove trailing slash if present
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.channels = []
        self.schedules = {}
    
    def get_channel_list(self, channels_page_url=None):
        """
        Scrape the list of available TV channels from the channels page.
        Specifically adapted for staseraintv.com structure.
        
        Args:
            channels_page_url (str, optional): URL of the channels listing page. If None, will use base_url.
            
        Returns:
            list: List of channel dictionaries with 'name' and 'url' keys
        """
        try:
            url = channels_page_url if channels_page_url else self.base_url
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # For staseraintv.com, look for the channel links in the dropdown menu
            channel_links = soup.select('ul.dropdown-menu li a')
            
            # If we can't find channels in the dropdown, try another approach
            if not channel_links:
                # Try to find other navigation elements that might contain channel links
                channel_links = soup.select('div.navigation a') or soup.select('nav a')
            
            # Extract channels from links that appear to be for TV channels
            for link in channel_links:
                href = link.get('href', '')
                # Check if this link is likely to be a channel link
                if 'canale' in href.lower() or 'programmi' in href.lower() or 'stasera-in-tv' in href.lower():
                    channel_name = link.get_text().strip()
                    
                    # Skip general navigation links
                    if channel_name.lower() in ['home', 'contatti', 'privacy', 'cookie']:
                        continue
                        
                    channel_url = href if href.startswith('http') else f"{self.base_url}/{href.lstrip('/')}"
                    
                    self.channels.append({
                        'name': channel_name,
                        'url': channel_url
                    })
            
            # If we still couldn't find channels, try looking for listing boxes directly on the homepage
            if not self.channels:
                print("Trying to find channels directly from the homepage listings...")
                listing_boxes = soup.select('div.listingprevbox')
                
                for box in listing_boxes:
                    heading = box.find(['h2', 'h3', 'h4', 'strong'])
                    if heading:
                        channel_name = heading.get_text().strip()
                        # Use the current page as the channel URL since we're already on a page with listings
                        self.channels.append({
                            'name': channel_name,
                            'url': url
                        })
            
            print(f"Found {len(self.channels)} channels")
            return self.channels
            
        except Exception as e:
            print(f"Error retrieving channel list: {e}")
            return []
    
    def scrape_channel_schedule(self, channel_url, channel_name):
        """
        Scrape the TV schedule for a specific channel.
        Adapted specifically for staseraintv.com structure.
        
        Args:
            channel_url (str): URL of the channel's schedule page
            channel_name (str): Name of the channel
            
        Returns:
            list: List of program dictionaries with time and title information
        """
        try:
            programs = []
            
            response = requests.get(channel_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # For staseraintv.com - find all listing boxes
            listing_boxes = soup.select('div.listingprevbox')
            target_box = None
            
            # Try to find the box that corresponds to the channel we want
            for box in listing_boxes:
                # Look for heading elements containing the channel name
                heading = box.find(['h2', 'h3', 'h4', 'strong'])
                if heading and channel_name.lower() in heading.get_text().lower():
                    target_box = box
                    break
            
            # If we couldn't find a box specifically for this channel name
            # (perhaps we're already on a channel-specific page)
            if not target_box and listing_boxes:
                # Just use the first box we find
                target_box = listing_boxes[0]
            
            if not target_box:
                print(f"Could not find listing box for channel: {channel_name}")
                return programs
            
            # Extract program info from paragraphs with left-aligned text
            program_data = target_box.select_one('p[style*="text-align:left"]')
            
            # If we can't find a paragraph with that style, try any paragraph
            if not program_data:
                program_data = target_box.find('p')
            
            if not program_data:
                print(f"Could not find program data for channel: {channel_name}")
                return programs
            
            # Process the raw text to extract program times and titles
            # Split by <br> tags to get individual program lines
            br_tags = program_data.find_all('br')
            
            if br_tags:
                # If there are <br> tags, get program lines by splitting at them
                program_lines = []
                current_item = ""
                for content in program_data.contents:
                    if content.name == 'br':
                        if current_item.strip():
                            program_lines.append(current_item.strip())
                        current_item = ""
                    else:
                        current_item += str(content)
                
                # Add the last item if it exists
                if current_item.strip():
                    program_lines.append(current_item.strip())
            else:
                # Otherwise, just get the text content and try to split by newlines
                program_lines = program_data.get_text(separator='\n').strip().split('\n')
            
            for line in program_lines:
                line = line.strip()
                if not line or line == "":
                    continue
                
                # Match pattern like "19:45 - Blue Bloods" or "19:45: Blue Bloods"
                match = re.match(r'(\d{1,2}:\d{2})\s*[-:]\s*(.*)', line)
                if match:
                    time_str = match.group(1)
                    title = match.group(2).strip()
                    
                    programs.append({
                        'time': time_str,
                        'title': title
                    })
            
            print(f"Found {len(programs)} programs for channel {channel_name}")
            return programs
            
        except Exception as e:
            print(f"Error scraping channel {channel_name}: {e}")
            return []
    
    def scrape_all_channels(self):
        """
        Scrape schedules for all available channels.
        Adapted for staseraintv.com to handle its specific structure.
        
        Returns:
            dict: Dictionary with channel names as keys and program lists as values
        """
        if not self.channels:
            self.get_channel_list()
        
        for channel in self.channels:
            print(f"Scraping schedule for {channel['name']}...")
            programs = self.scrape_channel_schedule(channel['url'], channel['name'])
            self.schedules[channel['name']] = programs
            
            # Be nice to the server with a small delay between requests
            time.sleep(1.5)
        
        return self.schedules
    
    def scrape_homepage(self):
        """
        Scrape all channels directly from the homepage of staseraintv.com.
        This is an alternative approach that gets all data at once.
        
        Returns:
            dict: Dictionary with channel names as keys and program lists as values
        """
        try:
            print(f"Scraping all channels from homepage: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            self.scrape_from_html(response.text)
            
            print(f"Successfully scraped {len(self.schedules)} channels from homepage")
            return self.schedules
            
        except Exception as e:
            print(f"Error scraping homepage: {e}")
            return {}
    
    def scrape_multiple_pages(self, max_pages=10):
        """
        Scrape multiple index pages (index.html, index1.html, index2.html, etc.)
        
        Args:
            max_pages (int): Maximum number of index pages to try
            
        Returns:
            dict: Dictionary with channel names as keys and program lists as values
        """
        all_schedules = {}
        page_counter = 0
        
        # Try the base URL first (which is typically index.html or equivalent)
        base_url_parts = self.base_url.split('/')
        base_domain = '/'.join(base_url_parts[:-1]) if base_url_parts[-1].startswith('index') else self.base_url
        
        # Ensure base domain ends with a slash
        if not base_domain.endswith('/'):
            base_domain += '/'
        
        # First check if base_url works (index.html or equivalent)
        print(f"Checking base URL: {self.base_url}")
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            # Scrape the base page
            self.scrape_from_html(response.text)
            page_counter += 1
            print(f"Successfully scraped base page: {self.base_url}")
            
            # Store the first set of schedules
            for channel, programs in self.schedules.items():
                if channel not in all_schedules:
                    all_schedules[channel] = programs
                else:
                    all_schedules[channel].extend(programs)
            
        except requests.exceptions.RequestException as e:
            print(f"Error accessing base URL: {e}")
        
        # Now try numbered index pages
        for i in range(1, max_pages + 1):
            # Reset schedules for this page
            self.schedules = {}
            
            # Construct URL for this index page
            page_url = f"{base_domain}index{i}.html"
            
            print(f"Trying to access page: {page_url}")
            try:
                response = requests.get(page_url, headers=self.headers)
                response.raise_for_status()
                
                # Scrape this page
                self.scrape_from_html(response.text)
                page_counter += 1
                print(f"Successfully scraped page {i}: {page_url}")
                
                # Merge schedules
                for channel, programs in self.schedules.items():
                    if channel not in all_schedules:
                        all_schedules[channel] = programs
                    else:
                        # Extend the existing programs list
                        # But first check for duplicates
                        existing_times = set(p['time'] for p in all_schedules[channel])
                        for program in programs:
                            if program['time'] not in existing_times:
                                all_schedules[channel].append(program)
                
                # Be nice to the server
                time.sleep(1.5)
                
            except requests.exceptions.RequestException as e:
                print(f"Page {i} not found or error: {e}")
                # Break after 3 consecutive failures
                if i > 3 and page_counter == 0:
                    print("Multiple consecutive pages not found, stopping search.")
                    break
        
        print(f"Total pages scraped: {page_counter}")
        
        # Update the main schedules with all the combined results
        self.schedules = all_schedules
        return all_schedules
    
    def scrape_from_html(self, html_content):
        """
        Extract TV schedule data directly from HTML content.
        Adapted for staseraintv.com structure.
        
        Args:
            html_content (str): HTML content of the page
            
        Returns:
            dict: Dictionary with channel names as keys and program lists as values
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all listing boxes (these contain the TV schedules on staseraintv.com)
            listing_boxes = soup.select('div.listingprevbox')
            
            for box in listing_boxes:
                # Extract channel name from the box heading elements
                channel_name = None
                heading = box.find(['h2', 'h3', 'h4', 'strong', 'b'])
                if heading:
                    channel_name = heading.get_text().strip()
                else:
                    # Try to extract channel name from the first line or a specific attribute
                    first_text = box.get_text().strip().split('\n')[0]
                    channel_name = first_text
                
                # Extract program information
                programs = []
                program_data = box.select_one('p[style*="text-align:left"]')
                
                # If we can't find a paragraph with that style, try any paragraph
                if not program_data:
                    program_data = box.find('p')
                
                if program_data:
                    # Check if there are <br> tags in the program data
                    br_tags = program_data.find_all('br')
                    
                    if br_tags:
                        # If there are <br> tags, get program lines by splitting at them
                        program_lines = []
                        current_item = ""
                        for content in program_data.contents:
                            if isinstance(content, str):
                                current_item += content
                            elif content.name == 'br':
                                if current_item.strip():
                                    program_lines.append(current_item.strip())
                                current_item = ""
                            else:
                                current_item += content.get_text()
                        
                        # Add the last item if it exists
                        if current_item.strip():
                            program_lines.append(current_item.strip())
                    else:
                        # Otherwise, just get the text content and try to split by newlines
                        program_lines = program_data.get_text(separator='\n').strip().split('\n')
                    
                    for line in program_lines:
                        line = line.strip()
                        if not line or line == "":
                            continue
                        
                        # Match pattern like "19:45 - Blue Bloods" or "19:45: Blue Bloods"
                        match = re.match(r'(\d{1,2}:\d{2})\s*[-:]\s*(.*)', line)
                        if match:
                            time_str = match.group(1)
                            title = match.group(2).strip()
                            
                            programs.append({
                                'time': time_str,
                                'title': title
                            })
                    
                    if channel_name:
                        # If channel already exists, extend its programs
                        if channel_name in self.schedules:
                            existing_times = set(p['time'] for p in self.schedules[channel_name])
                            for program in programs:
                                if program['time'] not in existing_times:
                                    self.schedules[channel_name].append(program)
                        else:
                            self.schedules[channel_name] = programs
                        
                        print(f"Extracted {len(programs)} programs for {channel_name}")
            
            return self.schedules
            
        except Exception as e:
            print(f"Error extracting data from HTML: {e}")
            return {}
    
    def save_to_csv(self, filename='tv_schedules.csv'):
        """
        Save all scraped TV schedules to a CSV file.
        
        Args:
            filename (str): Name of the CSV file to save
        """
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Channel', 'Time', 'Program'])
                
                for channel, programs in self.schedules.items():
                    for program in programs:
                        writer.writerow([channel, program['time'], program['title']])
                        
            print(f"Saved TV schedules to {filename}")
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")
    
    def save_to_json(self, filename='tv_schedules.json'):
        """
        Save all scraped TV schedules to a JSON file.
        
        Args:
            filename (str): Name of the JSON file to save
        """
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(self.schedules, file, ensure_ascii=False, indent=4)
                
            print(f"Saved TV schedules to {filename}")
            
        except Exception as e:
            print(f"Error saving to JSON: {e}")
    
    def create_output_folder(self, folder_name='output'):
        """
        Create a folder for storing output files.
        
        Args:
            folder_name (str): Name of the folder to create
            
        Returns:
            str: Path to the created folder
        """
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"Created output folder: {folder_name}")
            return folder_name
        except Exception as e:
            print(f"Error creating output folder: {e}")
            return ""
    
    def save_all_outputs(self, output_folder='output'):
        """
        Save all scraped data to various formats in an output folder.
        
        Args:
            output_folder (str): Name of the folder to save files in
        """
        folder_path = self.create_output_folder(output_folder)
        if not folder_path:
            folder_path = "."  # Use current directory if folder creation failed
        
        # Save combined data
        self.save_to_csv(os.path.join(folder_path, "all_tv_schedules.csv"))
        self.save_to_json(os.path.join(folder_path, "all_tv_schedules.json"))
        
        # Save current date and time to the filenames
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_to_csv(os.path.join(folder_path, f"tv_schedules_{current_time}.csv"))
        self.save_to_json(os.path.join(folder_path, f"tv_schedules_{current_time}.json"))
        
        print(f"All outputs saved to folder: {folder_path}")


# Example usage
if __name__ == "__main__":
    # Use the actual URL of the TV guide website
    tv_guide_url = "https://www.staseraintv.com/"
    
    scraper = TVScheduleScraper(tv_guide_url)
    
    # OPTION 1: Scrape schedules from all channels found on the website
    # This approach first gets a list of channels, then scrapes each one
    # scraper.get_channel_list()
    # schedules = scraper.scrape_all_channels()
    
    # OPTION 2: Scrape schedules directly from the homepage
    # schedules = scraper.scrape_homepage()
    
    # OPTION 3: Scrape multiple pages (index.html, index1.html, index2.html, etc.)
    schedules = scraper.scrape_multiple_pages(max_pages=10)
    
    # OPTION 4: Parse HTML directly (for testing or if you have HTML saved locally)
    # with open('sample_tv_guide.html', 'r', encoding='utf-8') as file:
    #     html_content = file.read()
    #     schedules = scraper.scrape_from_html(html_content)
    
    # Save the results to both formats with timestamps
    scraper.save_all_outputs()
    
    # Print a summary of what was scraped
    print("\nSummary of scraped data:")
    total_programs = 0
    for channel, programs in scraper.schedules.items():
        print(f"- {channel}: {len(programs)} programs")
        total_programs += len(programs)
    
    print(f"\nTotal: {len(scraper.schedules)} channels with {total_programs} programs")