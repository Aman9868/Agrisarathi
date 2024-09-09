from .utils import get_language_urls, scrape_section_page
import argparse
from datetime import datetime
def scrape_news(source, date=None):
    if date is None:
        date = datetime.now().date()
    
    language_urls = get_language_urls()
    all_posts = []

    if source.upper() in language_urls:
        for lang, urls in language_urls[source.upper()].items():
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
                            post["date"] = date
                        all_posts.extend(posts)

    return all_posts

def main():
    parser = argparse.ArgumentParser(description="Scrape news from various sources.")
    parser.add_argument("source", help="Name of the news source (e.g., ABPLIVE)")
    parser.add_argument("--date", help="Date to scrape news for (YYYY-MM-DD). Defaults to today.", default=None)
    
    args = parser.parse_args()
    
    if args.date:
        date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        date = None
    
    news = scrape_news(args.source, date)
    
    for article in news:
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Source: {article['source']}")
        print(f"Language: {article['language']}")
        print(f"Date: {article['date']}")
        print(f"Data Type: {article['data_type']}")
        print("---")

if __name__ == "__main__":
    main()