import os
import requests
import json
from datetime import datetime, time
import streamlit as st
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def fetch_news(start_published_date_str, end_published_date_str, number_of_articles):
    """Prepare the data payload for the Exo API request"""
    api_key = os.getenv("EXO_KEY")
    endpoint = "https://api.exa.ai/search"
    query = "Indian stock market and business news"
    data = {
        "startPublishedDate": start_published_date_str,
        "query": query,
        "type": "neural",
        "useAutoprompt": True,
        "numResults": number_of_articles,
        "endPublishedDate": end_published_date_str,
        "category":"news",
        # "excludeDomains": ["x.com", "twitter.com"],
        # "includeDomains": ["rediff.com", "moneycontrol.com", "reuters.com", "cnbc.com", "businesstoday.in",
        #                    "livemint.com", "economictimes.indiatimes.com", "financialexpress.com", "business-standard.com", "businesstoday.in"],
        "contents": {
            "text": True
        }
    }

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'x-api-key': api_key
    }

    response = requests.post(endpoint, headers=headers, json=data)

    if response.status_code == 200:
        output_data = response.json()
        articles = output_data.get('results', [])
        formatted_articles = []
        for article in articles:
            prompt = (
                "You are an expert in summarizing articles. "
                "Follow the rules to summarize the given article content within 65 words strictly:"
                "1. Headline should be short and crisp in sentence case. "
                "2. Do not add any opinion. "
                "3. The news article should be in past tense and the sentence in present tense. "
                "4. Output only the headline and the news article. "
                "5. The article should not feel like an advertisement."
                "Generate a headline and summarize the following article using the rules:\n\n"
                f"Content prompt: {article.get('text', '')}\n"
            )

            client = Groq(
                api_key=os.environ.get("GROQ_API_KEY"),
            )
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="gemma-7b-it",
            )

            response = chat_completion.choices[0].message.content
            response_text = response.strip()

            if "\n" in response_text:
                headline, summary = response_text.split("\n", 1)
            else:
                headline = response_text
                summary = ""

            formatted_articles.append({
                "headline": headline,
                "news_content": summary,
                "news_source_url": article.get('url', ''),
                "article_date": article.get('publishedDate', '')
            })

        # Save formatted articles to a JSON file
        with open('news.json', 'w') as f:
            f.write(json.dumps(formatted_articles, indent=2))

        return formatted_articles
    else:
        raise Exception(f"Failed to fetch news: {response.status_code} {response.text}")


def image_extractor(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    og_images = soup.find_all('meta', property='og:image')
    og_image_urls = [img['content'] for img in og_images]
    img_urls = og_image_urls
    return img_urls


def main():
    st.title("Indian Financial Market News")

    # User inputs for date range and number of articles
    start_date = st.date_input("Start date")
    end_date = st.date_input("End date")
    num_articles = st.number_input("Number of articles:", min_value=1, max_value=100, value=5)
    start_date_time = datetime.combine(start_date, time(0, 0))
    end_date_time = datetime.combine(end_date, time(23, 59, 59))
    # Convert the dates to the required format (e.g., "2024-08-25T14:17:54.241Z")
    start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    if st.button("Fetch News"):
        try:
            with st.spinner("Fetching news..."):
                articles = fetch_news(start_date_str, end_date_str, num_articles)
                if articles!=[]:
                    st.success("News fetched successfully!")
                else:
                    st.success("No News Found for the selected date range")

                # Display the news articles
                for article in articles:
                    st.subheader(article['headline'])
                    st.write(article['news_content'])
                    st.write(article['news_source_url'])
                    st.write(image_extractor(article['news_source_url']))
                    st.write(f"Published Date: {article['article_date']}")
                    st.write("---")

        except Exception as e:
            st.error(f"Error: {str(e)}")


if __name__ == '__main__':
    main()



