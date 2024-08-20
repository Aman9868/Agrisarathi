import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract
import urllib
from urllib.parse import urljoin
import re

def is_timestamp_or_pagination(title):
    # Simple regex to check if the title is a timestamp (like "10:02 pm")
    is_timestamp = bool(re.match(r'\d{1,2}:\d{2} ?(am|pm)?', title, re.IGNORECASE))
    
    # Check if the title is a pagination indicator (like "Page 2" or "Next Page")
    is_pagination = any(word.lower() in title.lower() for word in ['page', 'next', 'previous', '', 'more stories', 'page 2'])
    
    return is_timestamp or is_pagination

def generate_title_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find the main heading (you might need to adjust these selectors based on the website structure)
        heading = soup.find('h1')
        if heading:
            return heading.get_text(strip=True)
        
        # If h1 is not found, try h2
        heading = soup.find('h2')
        if heading:
            return heading.get_text(strip=True)
        
        # If no heading is found, return a default title or the URL
        return "No heading found"
    
    except requests.exceptions.RequestException as e:
        print(f"Error extracting heading from {url}: {str(e)}")
        return "Error extracting heading"


def scrape_post_content(post_url, image_class=None):
    try:
        response = requests.get(post_url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements (specific to your case)
        for tag_class in ['auth-name-dt', 'h-author', 'col-md-4', 'd-mags', 'd-social', 'd-nav-item-info']:
            for elem in soup.find_all('div', class_=tag_class):
                elem.decompose()

        # Extract content
        paragraphs = soup.find_all('p')
        content = "\n\n".join([p.get_text(strip=True) for p in paragraphs])



# Extract images
        image_urls = []
        if image_class:
            image_elements = soup.find_all('div', class_=image_class)
            for img_div in image_elements:
                img = img_div.find('img')
                if img:
                    img_url = img.get('src')
                    if img_url:
                        img_url = urljoin(post_url, img_url)
                        if img_url.startswith('http'):
                            image_urls.append(img_url)
                        else:
                            print(f"Skipping invalid image URL: {img_url}")                                             

        else:
            for img in soup.find_all('img'):
                img_url = img.get('src')
                if img_url:
                    img_url = urljoin(post_url, img_url)
                    if img_url.startswith('http'):
                        image_urls.append(img_url)
                    else:
                        print(f"Skipping invalid image URL: {img_url}")


        return content, image_urls
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching content from {post_url}: {str(e)}")
        return "", []

    

def get_clean_domain(url):
    parsed_url = urllib.parse.urlparse(url)
    extracted = tldextract.extract(parsed_url.netloc)
    source = f"{extracted.domain}"
    return source


def scrape_section_page(section_url, class_names, image_class=None, tag_name='div', ids=None):
    try:
        response = requests.get(section_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        section_posts = []
        for i, class_name in enumerate(class_names):
            if class_name == "none":
                continue
            
            # If IDs are provided, use them to find elements
            if ids and i < len(ids) and ids[i] != "none":
                news_list_section = soup.find_all(tag_name, class_=class_name, id=ids[i])
            else:
             news_list_section = soup.find_all(tag_name, class_=class_name)
            
            for news_div in news_list_section:
                news_links = news_div.find_all('a', href=True,title=True)
                for link in news_links:
                    post_title = link['title'].strip()
                    post_url = urljoin(section_url, link['href'])
                    if is_valid_url(post_url):
                        post_title = generate_title_from_url(post_url)
                        content, image = scrape_post_content(post_url, image_class)
                        source = get_clean_domain(post_url)
                        
                        section_posts.append({'title': post_title, 'url': post_url, 'source': source, 'content': content, 'image': image})
                    else:
                        print(f"Invalid URL found: {post_url}")

        return section_posts
    
    except requests.exceptions.RequestException as e:
        print(f"Error scraping section page {section_url}: {str(e)}")
        return []

def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


def get_language_urls():
    return {

        "KRISHAKJAGAT": {
            "HI": {
                "base": "https://www.krishakjagat.org/",
                "tag_name": ['div'],
                "main_class": ["cm-first-post", "cm-posts"],
                "news_classes": ["cm-post-content", "cm-posts"],
                "weather_class": ["weather-home mt-5 mb-3"],
                "khati_badi_class": ["home-2-3-lst"],
                "government_class": ["col-xs-12 col-sm-6 col-md-4 col-lg-4 cat-flex"],
                "image_class": ["cm-featured-image"]
            },
            "EN": {
                "base": "https://www.en.krishakjagat.org/",
                "tag_name": ['div'],
                "main_class": ["cm-first-post", "cm-posts"],
                "news_classes": ["cm-post-content", "cm-posts"],
                "weather_class": ["none"],
                "khati_badi_class": ["home-2-3-lst"],
                "government_class": ["none"],
                "image_class": ["cm-featured-image"]
            },
       },

        "ABPLIVE": {
            "HI": {
                "base": "https://www.abplive.com/search?s=agriculture",
                "tag_name": ['div'],
                "main_class": ["none"],
                "news_classes": ["none"],
                "weather_class": ["none"],
                "khati_badi_class": ["full-wrap"],
                "government_class": ["none"],
                "image_class": ["limgpod-16x9"]
            },
            "EN": {
                "base": "https://news.abplive.com/search?s=agriculture",
                "tag_name": ['div'],
                "main_class": ["none"],
                "news_classes": ["none"],
                "weather_class": ["none"],
                "khati_badi_class": ["full-wrap"],
                "government_class": ["none"],
                "image_class": ["imgpod-16x9"]
            },
                "MR": {
        "base": "https://marathi.abplive.com/search?s=agriculture",
        "tag_name":['div'] , 
        "main_class": ["none"], 
        "news_classes": ["none"],  
        "weather_class": ["none"], 
        "khati_badi_class": ["full-wrap"],  
        "government_class": ["none"], 
        "image_class": ["imgpod-16x9"]   
    },
    
    "BN": {
        "base": "https://bengali.abplive.com/search?s=agriculture",
        "tag_name":['div'] , 
        "main_class": ["none"], 
        "news_classes": ["none"],  
        "weather_class": ["none"], 
        "khati_badi_class": ["full-wrap"],  
        "government_class": ["none"], 
        "image_class": ["imgpod-16x9"]   
    },
    
    "PA": {
        "base": "https://punjabi.abplive.com/search?s=agriculture",
        "tag_name":['div'] , 
        "main_class": ["none"], 
        "news_classes": ["none"],  
        "weather_class": ["none"], 
        "khati_badi_class": ["full-wrap"],  
        "government_class": ["none"], 
        "image_class": ["imgpod-16x9"]  
    },
    
    "GU": {
        "base": "https://gujarati.abplive.com/search?s=agriculture",
        "tag_name":['div'] , 
        "main_class": ["none"], 
        "news_classes": ["none"],  
        "weather_class": ["none"], 
        "khati_badi_class": ["full-wrap"],  
        "government_class": ["none"], 
        "image_class": ["imgpod-16x9"]  
    },
    
    "TE": {
        "base": "https://telugu.abplive.com/search?s=agriculture",
        "tag_name":['div'] , 
        "main_class": ["none"], 
        "news_classes": ["none"],  
        "weather_class": ["none"], 
        "khati_badi_class": ["full-wrap"],  
        "government_class": ["none"], 
        "image_class": ["imgpod-16x9"]   
    },
    
    "TA": {
        "base": "https://tamil.abplive.com/search?s=agriculture",
        "tag_name":['div'] , 
        "main_class": ["none"], 
        "news_classes": ["none"],  
        "weather_class": ["none"], 
        "khati_badi_class": ["full-wrap"],  
        "government_class": ["none"], 
        "image_class": ["imgpod-16x9"]  
    },
        
        },
        "KRISHIJAGRAN": {
            "HI": {
                "base": "https://hindi.krishijagran.com/",
                "tag_name": ['div'],
                "main_class": ["home-top-l"],
                "news_classes": ["home-top-news-lst"],
                "weather_class": ["weather-home mt-5 mb-3"],
                "khati_badi_class": ["home-2-3-lst"],
                "government_class": ["col-xs-12 col-sm-6 col-md-4 col-lg-4 cat-flex"],
                "image_class": ["col-lg-8"]
            },
            "EN": {
                "base": "https://krishijagran.com/",
                "tag_name": ['div'],
                "main_class": ["home-top-l"],
                "news_classes": ["home-top-news-lst"],
                "weather_class": ["none"],
                "khati_badi_class": ["home-2-3-lst"],
                "government_class": ["none"],
                "image_class": ["col-lg-8"]
            },
            "PA": {
        "base": "https://punjabi.krishijagran.com/",
        "tag_name":['div'] ,
        "main_class": ["home-top-l"],
        "news_classes": ["home-top-news-lst"],
        "weather_class": ["none"],
        "khati_badi_class": ["col-xs-12 col-sm-6 col-md-4 col-lg-4 cat-flex"],
        "government_class":["home-2-3-lst"],
        "image_class": ["col-md-12 column"]  
    },  
    "MR": {
        "base": "https://marathi.krishijagran.com/",
        "tag_name":['div'] ,
        "main_class": ["home-top-l"],
        "news_classes": ["home-top-news-lst"],
        "weather_class": ["weather-home mt-5 mb-3"],
        "khati_badi_class": ["none"],
        "government_class":["home-2-3-lst"],
        "image_class": ["story-img"] 
  
     },
    "TA": {
        "base": "https://tamil.krishijagran.com/",
        "tag_name":['div'] ,
        "main_class": ["home-top-l"],
        "news_classes": ["home-top-news-lst"],
        "weather_class": ["none"],
        "khati_badi_class": ["home-2-3-lst"],
        "government_class":["news-list-wide shadow-sm"],
        "image_class": ["none"]  
    },
    "ML": {
        "base": "https://malayalam.krishijagran.com/",
        "tag_name":['div'] ,
        "main_class": ["home-top-l"],
        "news_classes": ["home-top-news-lst"],
        "weather_class": ["none"],
        "khati_badi_class": ["none"],
        "government_class":["h-cat-lst shadow-sm"],
        "image_class": ["col-md-12 column"]  
    },
    "BN": {
        "base": "https://bengali.krishijagran.com/",
        "tag_name":['div'] ,
        "main_class": ["home-top-l"],
        "news_classes": ["home-top-news-lst"],
        "weather_class": ["weather-home mt-5 mb-3"],
        "khati_badi_class": ["none"],
        "government_class":["h-cat-lst shadow-sm"],
        "image_class": ["col-md-12 column"]  
    },
    "KN": {
        "base": "https://kannada.krishijagran.com/",
        "tag_name":['div'] ,
        "main_class": ["home-top-l"],
        "news_classes": ["home-top-news-lst"],
        "weather_class": ["none"],
        "khati_badi_class": ["none"],
        "government_class":["h-cat-lst shadow-sm"],
        "image_class": ["col-md-12 column"]  
    },
    "OR": {
        "base": "https://odia.krishijagran.com/",
        "tag_name":['div'] ,
        "main_class": ["home-top-l"],
        "news_classes": ["home-top-news-lst"],
        "weather_class": ["none"],
        "khati_badi_class": ["three-boxes"],
        "government_class":["h-cat-lst shadow-sm"],
        "image_class": ["col-md-12 column"]  
     },
    "AS": {
        "base": "https://asomiya.krishijagran.com/",
        "tag_name":['div'] ,
        "main_class": ["home-top-l"],
        "news_classes": ["home-top-news-lst"],
        "weather_class": ["none"],
        "khati_badi_class": ["none"],
        "government_class":["h-cat-lst shadow-sm"],
        "image_class": ["col-md-12 column"] 
     },    
        },
        "KISANSAMADHAAN": {
            "HI": {
                "base": "https://kisansamadhan.com/",
                "tag_name": ['div'],
                "main_class": ["td_block_inner"],
                "main_ids": ["tdi_68"],
                "news_classes": ["td_block_inner td-mc1-wrap"],
                "news_ids": ["tdi_69"],
                "weather_class": ["td_block_inner td-mc1-wrap"],
                "weather_ids": ["tdi_89"],
                "khati_badi_class": ["td_block_inner td-mc1-wrap"],
                "khati_badi_ids": ["tdi_79"],
                "government_class": ["none"],
                "government_ids": ["none"],
                "image_class": ["tdb-block-inner td-fix-index"]
            }
        },
        "KISANTAK": {
            "HI": {
                "base": "https://www.kisantak.in/",
                "tag_name": ['div'],
                "main_class": ["none"],
                "news_classes": ["mainNews__kisan"],
                "weather_class": ["weatherWigetBd news"],
                "khati_badi_class": ["fullWidget__subBody"],
                "government_class": ["fullWidget__Body"],
                "image_class": ["left-child-contianer"]
            }
        }
    }

    

    

def process_and_scrape_data():
    language_urls = get_language_urls()
    all_posts = []

    for source, languages in language_urls.items():
        for lang, urls in languages.items():
            base_url = urls["base"]
            tag_name = urls["tag_name"]
            image_class = urls["image_class"]

            class_to_data_type = {
                "Main Articles": urls["main_class"],
                "Current News": urls["news_classes"],
                "Weather Information": urls["weather_class"],
                "Agriculture Information": urls["khati_badi_class"],
                "Government Schemes": urls["government_class"]
            }

            for data_type, classes in class_to_data_type.items():
                for class_name in classes:
                    if class_name != "none":
                        posts = scrape_section_page(base_url, [class_name], image_class, tag_name)
                        for post in posts:
                            post["data_type"] = data_type
                            post["language"] = lang
                            post["source"] = source
                        all_posts.extend(posts)
                        #print(all_posts)

    return all_posts