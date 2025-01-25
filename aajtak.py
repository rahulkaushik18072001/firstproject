import requests
from bs4 import BeautifulSoup
import json
import datetime

# Function to scrape a single article
def scrape_article(article_url):
    try:
        response = requests.get(article_url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract the article details
        title = soup.find("h1").text.strip() if soup.find("h1") else None
        author = soup.find(class_="author_name").text.strip() if soup.find(class_="author_name") else "Unknown"
        description = soup.find("meta", {"name": "description"})["content"].strip() if soup.find("meta", {"name": "description"}) else None
        article_content = " ".join([p.text for p in soup.find_all("p")])  # All paragraphs combined
        published_date = soup.find("time")["datetime"] if soup.find("time") else None
        image = soup.find("img", {"class": "featured-image"})["src"] if soup.find("img", {"class": "featured-image"}) else None

        # If there's no published date, skip the article
        if not published_date:
            return None

        # Convert the published date to a datetime object
        published_date_obj = datetime.datetime.fromisoformat(published_date)
        # Get the current date and time
        current_date = datetime.datetime.now()
        # Calculate the difference in days
        date_difference = (current_date - published_date_obj).days

        # Skip the article if it's older than 2 days
        if date_difference > 2:
            return None

        # Return the data in the desired format
        return {
            'title': title,
            'author': author,
            'description': description,
            'text': article_content,
            'link': article_url,
            'published_date': published_date,
            'image_link': image
        }

    except Exception as e:
        print(f"Error scraping {article_url}: {e}")
        return None

# Function to crawl a section of the site and get articles
def crawl_section(section_url):
    try:
        response = requests.get(section_url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find all article links in the section
        articles = []
        for link in soup.find_all("a", href=True):
            article_url = link["href"]
            if article_url.startswith("https://www.aajtak.in/") and "/story/" in article_url:
                articles.append(article_url)
        
        return list(set(articles))  # Remove duplicates

    except Exception as e:
        print(f"Error crawling section {section_url}: {e}")
        return []

# Main function to crawl AajTak and save articles in JSON format
def main():
    sitemap_urls = [
        "https://www.aajtak.in",  # Main page
        "https://www.aajtak.in/world",  # World news
        "https://www.aajtak.in/sports",  # Sports news
        "https://www.aajtak.in/entertainment",  # Entertainment news
        "https://www.aajtak.in/business",  # Business news
        "https://www.aajtak.in/auto",  # Auto news
        "https://www.aajtak.in/technology",  # Technology news
        "https://www.aajtak.in/crime",  # Crime news
        "https://www.aajtak.in/religion",  # Religion news
        "https://www.aajtak.in/lifestyle",  # Lifestyle news
    ]
    
    all_articles = []
    
    for section_url in sitemap_urls:
        print(f"Crawling section: {section_url}")
        article_links = crawl_section(section_url)
        
        print(f"Found {len(article_links)} articles in {section_url}")
        
        for article_url in article_links:
            article_data = scrape_article(article_url)
            if article_data:
                all_articles.append(article_data)
    
    # Save all articles to a JSON file
    output_file = f"aajtak_articles_{datetime.datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=4)
    
    print(f"Saved {len(all_articles)} articles to {output_file}")

if __name__ == "__main__":
    main()
