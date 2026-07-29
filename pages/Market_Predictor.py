#Import necessary packages:
import time
from datetime import datetime, timedelta
import streamlit as st
import requests
import yfinance as yf
import numpy as np
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import times
import pandas as pd
import plotly.express as px
from openai import OpenAI # type: ignore
from scoring_script.scoring import make_prediction
from services.result_rationalizer import rationalize_result
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

#Import the API Keys from the st.secrets (from the Streamlit secrets file)

openai_api_key = st.secrets["openai"]["api_key"]
POLYGON_API_KEY = st.secrets["polygon"]["api_key"]


print(yf.__version__)

#***************************Page Setup and Sidebar Setup*****************#

# Set page configuration
st.set_page_config(
    page_title="Market Sentiment Summarizer & Predictor",
    page_icon="📰",
    initial_sidebar_state="collapsed",
)

# Sidebar with Help Section
st.sidebar.title("Help & FAQs")

st.sidebar.write("""
**Google News Search API**

We use the Google News Search API to fetch the latest news articles related to your chosen company or topic. This allows us to aggregate up to 150 recent articles from various reputable sources. The aggregated news is then used for sentiment analysis and summarization, providing insights into market sentiment and potential impacts on stock prices.
""")

st.sidebar.write("""
**OpenAI API**

We leverage the OpenAI API to perform natural language processing tasks. Specifically, we use it to generate concise summaries of news headlines and analyze the overall sentiment of the news articles. This helps in understanding market sentiment without manually reading all the articles.
""")

st.sidebar.write("""
**PolygonIO Library**

We utilize the PolygonIO library to retrieve historical stock price data for your selected company. This includes daily open, high, low, and close prices over the past six months. The data is used to calculate technical indicators like RSI and ATR, which help assess stock performance and volatility.
""")

st.sidebar.subheader("What is RSI?")
st.sidebar.write("""
A higher RSI may mean the stock's price has risen quickly and could drop soon, while a lower RSI might mean it's a good time to buy as the price could rise.
""")

st.sidebar.subheader("RSI Explainer")
st.sidebar.write("""
Imagine you're shopping, and you notice an item that's suddenly much more expensive than usual—that's like a high RSI, suggesting it might not be the best time to buy. Conversely, if the item is cheaper than normal (low RSI), it might be a good opportunity to purchase.
""")

st.sidebar.subheader("What is ATR?")
st.sidebar.write("""
A higher ATR means the stock price moves a lot during the day, which can be risky but also offer more opportunities for profit. A lower ATR means the price is steadier, which might be safer but with smaller gains.
""")

st.sidebar.subheader("ATR Explainer")
st.sidebar.write("""
Think of the stock market like the weather. On a windy day (high ATR), things can change rapidly, and you need to be prepared. On a calm day (low ATR), you can expect steadier conditions.
""")

st.sidebar.write("""
**Sentiment Analysis**

Sentiment Analysis involves evaluating news articles to determine the overall sentiment—positive, negative, or neutral—towards a company or topic. In our app, we analyze aggregated news to gauge market sentiment, which can influence stock price movements and aid in making informed investment decisions.
""")

st.sidebar.write("""
**Machine Learning Model**

We utilize a gradient boosted machine learning model that analyzes the past week's market data and average sentiment scores to predict stock price movements for the next week. This model helps forecast whether the stock is likely to trend upward or downward based on historical patterns and current sentiment. Model: Gradient Boosted Model (GradientBoostingClassifier); Model Features: learning_rate=0.1, max_depth=3, max_features='sqrt', min_samples_leaf=1, min_samples_split=2, n_estimators=100, subsample=1.0, random_state=42
""")

st.sidebar.write("""
**Volatility Percentage**

Volatility Percentage represents the stock's average price movement as a percentage of its current price. It is calculated by dividing the Average True Range (ATR) by the latest closing price and multiplying by 100. This metric helps you understand how much the stock price typically fluctuates, indicating the level of market risk.
""")

st.sidebar.write("""
**Overbought/Oversold Conditions**

These conditions are identified using the RSI indicator. An RSI above 70 suggests the stock is overbought, meaning it may have risen too quickly and could be due for a pullback. An RSI below 30 indicates the stock is oversold, suggesting it may be undervalued and could experience a price increase.
""")

st.sidebar.write("""
**Volatility**

Volatility refers to the degree of variation in a stock's price over time. A higher volatility means the stock price fluctuates significantly, indicating higher risk and potential reward. We use the ATR to measure volatility, helping you understand how much the stock price moves on average.
""")

st.sidebar.write("""
**Momentum**

Momentum measures the rate at which a stock's price is changing. Positive momentum indicates the price is rising, while negative momentum suggests it is falling. In our app, we assess momentum through indicators like RSI to help identify potential trends in stock price movements.
""")

st.sidebar.write("""
**Bullish/Bearish Trends**

A bullish trend signifies that the stock price is moving upward, reflecting market optimism. A bearish trend indicates a downward movement, reflecting pessimism. Understanding these trends helps investors make decisions about buying or selling stocks. Our app identifies these trends using technical analysis and sentiment data.
""")

st.sidebar.write("""
**Stock Ticker Symbol**

A stock ticker symbol is a unique series of letters assigned to a publicly traded company. It is used to identify the company on stock exchanges and financial markets. In our app, you input the ticker symbol to fetch specific stock data and news articles for that company.
""")

st.sidebar.write("""
**Technical Indicators**

Technical indicators are mathematical calculations based on historical price and volume data used to predict future stock movements. In our app, we calculate indicators like RSI and ATR to analyze stock performance, helping you understand market trends and make informed decisions.
""")

st.sidebar.write("""
**Moving Averages**

A moving average smooths out price data by creating a constantly updated average price. This helps identify the direction of a trend. While our app focuses on RSI and ATR, moving averages are also important technical indicators commonly used in market analysis.
""")

st.sidebar.write("""
**Market Sentiment**

Market sentiment reflects the overall attitude of investors towards a particular stock or financial market. It is influenced by news, economic indicators, and market trends. Our app gauges market sentiment through sentiment analysis of news articles, providing insights into how the market views a company.
""")

st.sidebar.write("""
**Headline Summarization**

We use the OpenAI API to generate concise summaries of news headlines fetched via the Bing News Search API. This provides you with an overview of the most important news affecting the stock, saving you time from reading each article individually.
""")

st.sidebar.write("""
**News Articles Aggregation**

Our app aggregates news articles related to your selected company or topic using the Bing News Search API. By collecting multiple sources of information, we provide a comprehensive view of current events and sentiments that may impact stock performance.
""")

#***************************Insert CSS*****************#
# Inject CSS for card styling and marquee effect
st.markdown("""
    <style>
    /* Card styling */
    .card {
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        background-color: #f9f9f9;
    }
    .card h4 {
        margin: 0;
        color: #1e90ff;
    }
    .card p {
        color: #444;
    }
    .card .description {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: #333;
        max-width: 100%;
    }
    .card a {
        color: #1e90ff;
        text-decoration: none;
    }
    .card a:hover {
        text-decoration: underline;
    }
        /* Centering the title */
    .centered-title {
        text-align: center;

    </style>
    """, unsafe_allow_html=True)

# Centered title
st.markdown(
    """
    <h1 class='centered-title'>
        📰 Market Sentiment Summarizer & Predictor
    </h1>
    """,
    unsafe_allow_html=True
)

#***************************Initialize Vader and OpenAI Client*****************#

# Ensure VADER lexicon is downloaded
nltk.download('vader_lexicon')

API_Key = openai_api_key
secret_key = API_Key

# Function to generate a summary of headlines using OpenAI Chat API
client = OpenAI(api_key=secret_key)

#***************************Ticker Name Extraction*****************#
@st.cache_data(show_spinner=False)
def resolve_ticker_from_company(company_name):
    import requests
    base_url = "https://api.polygon.io/v3/reference/tickers"
    params = {
        "search": company_name,
        "active": "true",
        "apiKey": POLYGON_API_KEY
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if data.get("results"):
        first_match = data["results"][0]
        ticker = first_match.get("ticker", "")
        name = first_match.get("name", "")
        return ticker, name
    else:
        return None, None

#***************************RSI and ATR Calculations*****************#

def calculate_rsi(data, window=14):
    # Ensure 'Close' is numeric and handle missing values
    close_series = pd.to_numeric(data['Close'], errors='coerce').fillna(method='ffill')
    data['RSI'] = RSIIndicator(close_series, window=window).rsi()
    return data

def calculate_atr(data, window=14):
    # Ensure 'High', 'Low', and 'Close' are numeric and clean
    high_series = pd.to_numeric(data['High'], errors='coerce').dropna()
    low_series = pd.to_numeric(data['Low'], errors='coerce').dropna()
    close_series = pd.to_numeric(data['Close'], errors='coerce').dropna()

    # Align columns
    aligned_data = pd.concat([high_series, low_series, close_series], axis=1).dropna()
    aligned_data.columns = ['High', 'Low', 'Close']

    # Calculate ATR components
    aligned_data['High-Low'] = aligned_data['High'] - aligned_data['Low']
    aligned_data['High-Close'] = np.abs(aligned_data['High'] - aligned_data['Close'].shift(1))
    aligned_data['Low-Close'] = np.abs(aligned_data['Low'] - aligned_data['Close'].shift(1))
    aligned_data['TR'] = aligned_data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
    aligned_data['ATR'] = aligned_data['TR'].rolling(window).mean()

    # Return ATR series
    data['ATR'] = aligned_data['ATR']
    return data

#***************************Summary and Sentiments Generation*****************#


#***************************HelperFunctions*****************#

import re

def _extract_lines(text: str):
    # grab non-empty lines; strip bullets like "-", "•"
    lines = []
    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s:
            continue
        s = re.sub(r'^\s*[-•]\s*', '', s)
        lines.append(s)
    return lines

def _finalize_sentence(s: str) -> str:
    s = re.sub(r'\s+', ' ', s).strip()
    if not s:
        return s
    # If there is a sentence terminator somewhere, trim to the last one.
    m = re.search(r'(.+[.!?])[^.!?]*$', s)
    if m:
        return m.group(1).strip()
    # Otherwise, just ensure it ends with a period.
    return s.rstrip('.') + '.'

def _fix_bulleted_summary(text: str, n=4):
    lines = _extract_lines(text)
    if not lines:
        return text
    # Keep at most n bullets and ensure each is a full sentence.
    fixed = [_finalize_sentence(l) for l in lines[:n]]
    # Return in your expected bullet format
    return '\n'.join(f"- {b}" for b in fixed)


#***************************HelperFunctions*****************#

# Function to generate a summary of headlines using OpenAI's updated API
def generate_summary(headlines):
    # Join all headlines into a single prompt string
    prompt = "Hi, imagine that you are a very respected and very experienced journalist. So, there are a lot of news that we get everyday right. It can sometime be very overwhelming to go through all the news headlines individually. Its is also important to keep its simple and extract the main theme from all the ews articles while you are reading it. Always keep in mind the context, s that will make the summary much more grounded. Each bullet must be a **complete sentence that ends with a period**. Do not cut off mid-sentence. Now this is very important, never never ever cot-off mid-sentence. Please always remember to complete the full sentence. So, I would want you to summarize all the news that is here into a four-line summary (preferably in bullet points):\n\n" + "\n".join(headlines)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Imagine that you are a very respected and very experienced journalist with over 30 years of experince in journalism. It is important to keep in mind that the headlines need to summarized in a clear concise way, so the reader can just understand all the main point by just glancing over it. Also another thing to consider, maybe just consider the historical context of the news you are summarizing, so when you are summarizing something, keep all the past context (as far as you know) in mind. Also see to it that you do not give any incomplete responses please. "},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.2
    )
    
    # Retrieve the summary from the response
    #summary = response.choices[0].message['content'].strip()
    #return summary
    
    #The below line works
    #return response.choices[0].message.content.strip() 

    raw =  (response.choices[0].message.content or "").strip()
    return _fix_bulleted_summary(raw, n=4)


# Function to generate a summary of headlines using OpenAI's updated API
def generate_sector_summary(headlines):
    # Join all headlines into a single prompt string
    prompt = "Hi, imagine that you are a very respected and very experienced journalist. So, there are a lot of news that we get everyday right. It can sometime be very overwhelming to go through all the news headlines individually. Its is also important to keep its simple and extract the main theme from all the news articles while you are reading it. Always keep in mind the context, that will make the summary much more grounded. In this case provide the summary of the business sector that is being talked about. Each bullet must be a **complete sentence that ends with a period**. Do not cut off mid-sentence. Now this is very important, never never ever cot-off mid-sentence. Please always remember to complete the full sentence. So, I would want you to summarize all the news that is here into a four-line summary (preferably in bullet points):\n\n" + "\n".join(headlines)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Imagine that you are a very respected and very experienced journalist with over 30 years of experince in journalism. It is important to keep in mind that the headlines need to summarized in a clear concise way, so the reader can just understand all the main point by just glancing over it. The main task is to provide the summary of the business sector that a company is functioning in. So, if you have a sector like, Information Technology, then the main objective here is to summarize the text with that sector (Information Technology) in this case in mind. Also another thing to consider, maybe just consider the historical context of the news you are summarizing, so when you are summarizing something, keep all the past context (as far as you know) in mind. Also see to it that you do not give any incomplete responses please. "},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.2
    )
    
    # Retrieve the summary from the response
    #summary = response.choices[0].message['content'].strip()
    return response.choices[0].message.content.strip() 
    #return summary

def _normalize_label(text: str) -> str:
    """Map any model output to one of 5 labels; fallback Neutral."""
    t = (text or "").strip().lower()
    if "trending" in t and "positive" in t: return "Trending Positive"
    if "trending" in t and "negative" in t: return "Trending Negative"
    if "positive" in t: return "Positive"
    if "negative" in t: return "Negative"
    if "neutral"  in t: return "Neutral"
    # direct exact match just in case
    if t in {"positive","trending positive","neutral","trending negative","negative"}:
        return t.title()
    return "Neutral"



def analyze_sentiment(descriptions):
    prompt = (
        "You are an expert in sentiment analysis. Analyze the overall sentiment "
        "of the following news article descriptions and provide any of the following sentiments: "
        "Positive, Trending Positive, Trending Negative, Negative, or Neutral. "
        "So, if the sentiment is definitiely Positive/Negative then either respond Positive or Negative, but if it is getting hard to decide "
        "and if you think its between Negative and Neutral then respond with Trending Negative. If its between Positive and Neutral then respond with Trending Positive"
        "If its genuinely Neutral, then just respond with Neutral"
        "Think hard before giving something outright Negative. If something is sounding Positive, maybe go with it"
        "Always provide one of the responses, never give a blank response.\n\n"
        f"{descriptions}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in sentiment analysis of news articles."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0.2
    )
    raw = (response.choices[0].message.content or "").strip()
    return _normalize_label(raw)
    #return response.choices[0].message.content.strip() 

def analyze_sector_sentiment(descriptions):
    prompt = (
        "You are an expert in sentiment analysis. Analyze the overall sentiment "
        "of the following news article descriptions and provide any of the following sentiments: "
        "Positive, Trending Positive, Trending Negative, Negative, or Neutral. "
        "So, if the sentiment is definitiely Positive/Negative then either respond Positive or Negative, but if it is getting hard to decide "
        "and if you think its between Negative and Neutral then respond with Trending Negative. If its between Positive and Neutral then respond with Trending Positive"
        "If its genuinely Neutral, then just respond with Neutral"
        "Think hard before giving something outright Negative. If something is sounding Positive, maybe go with it"
        "Think like a very experienced business journalist. The text you will be provided with will be of a specific business sector."
        "So, when you are providing the response, think of it in the context of the business sector in total. "
        "Always provide one of the responses, never give a blank response.\n\n"
        f"{descriptions}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in sentiment analysis of news articles."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0.2
    )
    raw = (response.choices[0].message.content or "").strip()
    return _normalize_label(raw)
    #return response.choices[0].message.content.strip() 

#***************************Extract the News *****************#

# --- DROP-IN REPLACEMENT: Bing -> Google News RSS (no API key needed) ---
import html
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, urlparse
from datetime import datetime

_GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

def _guess_provider_from_title_or_domain(title: str, link: str) -> str:
    # Try "Headline - Publisher" pattern first (common in Google News titles)
    parts = (title or "").rsplit(" - ", 1)
    if len(parts) == 2 and 2 <= len(parts[1]) <= 40:
        return parts[1].strip()

    # Fallback: map domain to brand name
    netloc = urlparse(link or "").netloc.lower()
    domain_map = {
        "www.bloomberg.com": "Bloomberg", "bloomberg.com": "Bloomberg",
        "www.reuters.com": "Reuters", "reuters.com": "Reuters",
        "www.cnbc.com": "CNBC", "cnbc.com": "CNBC",
        "www.ft.com": "Financial Times", "ft.com": "Financial Times",
        "www.theguardian.com": "Guardian", "theguardian.com": "Guardian",
        "finance.yahoo.com": "Yahoo Finance", "news.yahoo.com": "Yahoo",
        "www.barrons.com": "Barrons",
        "www.bbc.com": "BBC", "www.bbc.co.uk": "BBC",
        "www.marketwatch.com": "Market Watch", "www.economist.com": "Economist",
        "asia.nikkei.com": "Nikkei",
        "www.ecb.europa.eu": "ECB", "www.federalreserve.gov": "Fed",
        "www.fxstreet.com": "FXStreet", "www.forexlive.com": "Forex Live",
        "www.zerohedge.com": "Zero Hedge",
    }
    return domain_map.get(netloc, netloc or "Unknown")

def _parse_pubdate(pub: str) -> str:
    """Normalize pubDate to ISO 8601 string if possible; else return original."""
    if not pub:
        return ""
    # Typical RSS format: 'Mon, 17 Feb 2025 12:34:56 GMT'
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(pub, fmt).isoformat()
        except Exception:
            pass
    return pub

def get_news_articles(query: str, freshness_days: int = 30, max_results: int = 150) -> pd.DataFrame:
    """
    Google News RSS replacement for the old Bing fetcher.
    - query: search string, e.g. 'Tesla' or 'Artificial Intelligence'
    - freshness_days: 1, 3, 7, 30, etc. (maps to Google News 'when:Xd')
    - max_results: cap total rows (RSS typically returns tens to ~100 items)
    Returns: DataFrame with columns ['Title','Description','URL','Published At','Provider']
    """
    g_query = f"{query} when:{freshness_days}d"
    url = _GOOGLE_NEWS_RSS.format(query=quote_plus(g_query))

    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    items = root.findall(".//item")

    rows, seen = [], set()
    for it in items:
        title = html.unescape((it.findtext("title") or "").strip())
        desc  = html.unescape((it.findtext("description") or "").strip())
        link  = (it.findtext("link") or "").strip()
        pub   = (it.findtext("{http://purl.org/dc/elements/1.1/}date")  # sometimes present
                 or it.findtext("pubDate") or "").strip()

        if not link or link in seen:
            continue
        seen.add(link)

        provider = _guess_provider_from_title_or_domain(title, link)

        rows.append({
            "Title": title,
            "Description": desc,
            "URL": link,
            "Published At": _parse_pubdate(pub),
            "Provider": provider,
        })

        if len(rows) >= max_results:
            break

    return pd.DataFrame(rows)



def display_articles_in_grid(articles):
    '''This function is used to display the articles in a grid format'''
    top_articles = articles.head(20)
    cols = st.columns(3)  # Three-column layout
    for idx, (_, row) in enumerate(top_articles.iterrows()):
        with cols[idx % 3]:  # Rotate through columns
            st.markdown(f"""
                <div style="
                    border: 1px solid #444; 
                    border-radius: 10px; 
                    padding: 15px; 
                    margin: 10px 0; 
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.6); 
                    background-color: #333; 
                    color: #f0f0f0;
                ">
                    <h4 style="margin-bottom: 10px;">
                        <a href="{row['URL']}" target="_blank" style="color:#1e90ff; text-decoration:none;">
                            {row['Title']}
                        </a>
                    </h4>
                </div>
            """, unsafe_allow_html=True)


#***************************Application Interface Piece (Define the radio buttons and UI*****************#

# Step 1: User choice selection
choice = st.radio(
    "Choose your analysis type:",
    ("Company-Specific Sentiment and Prediction", "General Sentiment of a Topic")
)

# Step 2: General Sentiment Workflow
if choice == "General Sentiment of a Topic":
    # Input field for keyword (General topic)
    keyword = st.text_input("Enter Topic/Keyword for General Sentiment Analysis")
    
    if st.button("Fetch Articles for General Sentiment"):
        if keyword:
            with st.spinner("Fetching Articles, Generating Summary and Sentiments"):
                progress_bar = st.progress(0)
                articles_df = get_news_articles(keyword)

                for percent_complete in range(0, 101, 10):
                    time.sleep(0.1)
                    progress_bar.progress(percent_complete)

            st.write(f"Total articles found: {len(articles_df)}")

            # Add artificial delay and progress updates
            for percent_complete in range(0, 101, 10):
                time.sleep(0.1)
                progress_bar.progress(percent_complete)

            # Generate summary of headlines
            headlines = articles_df['Title'].tolist()
            summary = generate_summary(headlines)

            # Display the summary at the top
            st.write("### Summary of Headlines")
            st.info(summary)

            # Concatenate all descriptions for sentiment analysis
            all_descriptions = " ".join(articles_df['Description'].dropna().tolist())
            overall_sentiment = analyze_sentiment(all_descriptions)

            # Display the overall sentiment
            st.write("### Overall Sentiment of Articles")
            #if overall_sentiment == 'positive':
                #st.success(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            #elif overall_sentiment == 'negative':
                #st.error(f"The overall sentiment of the news articles is: **{overall_sentiment}**")

            #st.info(f"The overall sentiment of the news articles is: **{overall_sentiment}**")

            if overall_sentiment == 'Positive':
                st.success(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            elif overall_sentiment == 'Trending Positive':
                st.success(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            elif overall_sentiment == 'Neutral':
                st.info(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            elif overall_sentiment == 'Trending Negative':
                st.error(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            elif overall_sentiment == 'Negative':
                st.error(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            else:
                st.info(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            
            # Display articles in grid layout
            st.write("### Latest News Articles")
            display_articles_in_grid(articles_df)
        else:
            st.warning("Please enter a topic or keyword for sentiment analysis.")

# Step 3: Company-Specific Sentiment and Prediction Workflow
elif choice == "Company-Specific Sentiment and Prediction":
    # Input fields for Company Name and Ticker
    company_name = st.text_input("Enter the company name for prediction:")
    ticker_symbol = None
    resolved_name = None
        
    if company_name:
        with st.spinner("🔍 Extracting ticker symbol from company name..."):
            ticker_symbol, resolved_name = resolve_ticker_from_company(company_name)

        if ticker_symbol:
            st.success(f"✅ Resolved {company_name} → **{ticker_symbol}** ({resolved_name})")
        else:
            st.error("⚠️ Could not resolve ticker symbol. Please try another name.")
            ticker_symbol = st.text_input("Enter the ticker symbol manually (e.g., TSLA):")


    #ticker_symbol = st.text_input("Enter the stock ticker symbol for prediction:")
    sector = st.text_input("Enter the sector the company functions in:")
    
    if st.button("Fetch Articles and Predict"):
        if company_name and ticker_symbol:
            with st.spinner("Fetching Articles, Generating Summary, Sentiments, and Prediction"):
                # Fetch articles related to the company
                articles_df = get_news_articles(company_name)
                progress_bar = st.progress(0)
                
                # Simulate progress for article fetching
                for percent_complete in range(0, 101, 10):
                    time.sleep(0.1)
                    progress_bar.progress(percent_complete)

            # Concatenate all descriptions for sentiment analysis
            all_descriptions = " ".join(articles_df['Description'].dropna().tolist())
            overall_sentiment = analyze_sentiment(all_descriptions)

            #**************************************************
            # Display sector summary
            # Fetch articles related to the sector
            if sector:
                sector_articles_df = get_news_articles(sector)
                # Generate summary of sector headlines
                sector_headlines = sector_articles_df['Title'].tolist()
                sector_summary = generate_sector_summary(sector_headlines)

                # Analyze sentiment of sector articles
                sector_descriptions = " ".join(sector_articles_df['Description'].dropna().tolist())
                sector_sentiment = analyze_sector_sentiment(sector_descriptions)

            #**************************************************

            # Get the prediction from scoring.py
            prediction = make_prediction(company_name, ticker_symbol)
            
            # Rationalize prediction and sentiment
            final_message = rationalize_result(overall_sentiment, prediction)
            
            # Display the final rationalized message
            st.subheader("Prediction Result")
            # Convert prediction to lowercase for consistent comparison
            prediction_lower = prediction.lower()

            # Display prediction result with appropriate color
            if 'positive' in prediction_lower or 'upward' in prediction_lower:
                st.success(final_message)
            else:
                st.warning(final_message)

            #st.success(final_message)

            #####**********************************************************************************

            st.write(f"Total articles found: {len(articles_df)}")

            # Generate summary of headlines
            headlines = articles_df['Title'].tolist()
            summary = generate_summary(headlines)

            # Display the summary at the top
            st.write("### Summary of Company Headlines")
            st.info(summary)


            # Display the overall sentiment
            st.write("### Overall Sentiment of Company Specific Articles")
            #st.success(f"The overall sentiment of the news articles is: **{overall_sentiment}**")

            # Convert sentiment to lowercase for consistent comparison
            sentiment = overall_sentiment.lower()

            # Display sentiment with appropriate color
            if sentiment == 'positive':
                st.success(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            elif sentiment == 'trending positive':
                st.success(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            elif sentiment == 'neutral':
                st.info(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            elif sentiment == 'trending negative':
                st.error(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            elif sentiment == 'negative':
                st.error(f"The overall sentiment of the news articles is: **{overall_sentiment}**")
            else:
                st.info(f"The overall sentiment of the news articles is: **{overall_sentiment}**")


            if sector:

                st.write(f"### Summary of {sector.title()} Sector Headlines")
                st.info(sector_summary)

                # Display sector sentiment
                st.write(f"### Overall Sentiment of {sector.title()} Sector Articles")

                # Convert sentiment to lowercase for consistent comparison
                sector_sentiment_lower = sector_sentiment.lower()

                # Display sentiment with appropriate color
                if 'positive' in sector_sentiment_lower:
                    st.success(f"The overall sentiment of the {sector.title()} sector is: **{sector_sentiment}**")
                elif 'negative' in sector_sentiment_lower:
                    st.warning(f"The overall sentiment of the {sector.title()} sector is: **{sector_sentiment}**")
                else:
                    st.info(f"The overall sentiment of the {sector.title()} sector is: **{sector_sentiment}**")

            #####**********************************************************************************

            # ************* (Technical Analysis Indicators) **************

            # ************* Technical Analysis Indicators - Full Polygon.io Integration *************
            try:
                from datetime import datetime, timedelta
                import os

                polygon_key = POLYGON_API_KEY
                end_date = datetime.today()
                start_date = end_date - timedelta(days=180)

                start_str = start_date.strftime('%Y-%m-%d')
                end_str = end_date.strftime('%Y-%m-%d')

                url = f"https://api.polygon.io/v2/aggs/ticker/{ticker_symbol}/range/1/day/{start_str}/{end_str}"
                params = {
                    "adjusted": "true",
                    "sort": "asc",
                    "limit": 5000,
                    "apiKey": polygon_key
                }

                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if "results" not in data:
                    st.warning("No stock data returned from Polygon.io.")
                    st.stop()

                df = pd.DataFrame(data["results"])
                df["Date"] = pd.to_datetime(df["t"], unit="ms")
                df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
                df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].dropna()

                # Calculate RSI and ATR
                from ta.momentum import RSIIndicator
                from ta.volatility import AverageTrueRange
                df["RSI"] = RSIIndicator(close=df["Close"], window=14).rsi()
                atr_calc = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"], window=14)
                df["ATR"] = atr_calc.average_true_range()

                latest_rsi = df["RSI"].dropna().iloc[-1]
                latest_atr = df["ATR"].dropna().iloc[-1]
                latest_close = df["Close"].dropna().iloc[-1]
                volatility_percentage = (latest_atr / latest_close) * 100

                # Display Indicators
                st.write("## Technical Indicator Analysis")
                st.write(f"### Relative Strength Index (RSI): {latest_rsi:.2f}")
                if latest_rsi > 70:
                    st.error("RSI > 70 → **Overbought** → Possible pullback")
                    momentum = "**Bullish momentum** based on price surge"
                elif latest_rsi < 30:
                    st.success("RSI < 30 → **Oversold** → Possible rebound")
                    momentum = "**Bearish momentum** due to downward pressure"
                else:
                    st.info("RSI in 30–70 range → **Neutral**")
                    momentum = "Leaning bullish" if latest_rsi > 50 else "Leaning bearish"
                st.info(f"**Momentum Analysis:** {momentum}")

                st.write("---")
                st.write(f"### Average True Range (ATR): {latest_atr:.2f}")
                st.info(f"**Volatility Percentage:** {volatility_percentage:.2f}%")

                if volatility_percentage > 5:
                    st.warning("**High volatility** — significant price swings likely.")
                elif volatility_percentage > 2:
                    st.info("**Moderate volatility** — watch closely.")
                else:
                    st.success("**Low volatility** — relatively stable.")

                # 📈 Line Chart
                st.write(f"### {company_name} ({ticker_symbol}) Stock Performance - Last 6 Months")
                import plotly.express as px
                fig = px.line(df, x='Date', y='Close', title=f"{company_name} Stock Price Over Last 6 Months")
                st.plotly_chart(fig)

                # 📊 Candlestick Chart
                import plotly.graph_objects as go
                fig = go.Figure(
                    data=[go.Candlestick(
                        x=df['Date'],
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name="Candlestick")]
                )
                fig.update_layout(
                    title=f"{company_name} Candlestick Chart - Last 6 Months",
                    xaxis_title="Date",
                    yaxis_title="Price"
                )
                st.plotly_chart(fig)


                if st.checkbox("🔽 Show All News Articles"):
                    display_articles_in_grid(articles_df)
            except Exception as e:
                st.error(f"❌ Error fetching or processing data from Polygon.io: {e}")

        
        else:
            st.warning("Please enter both the company name and stock ticker symbol.")

if st.button("🔙 Back to Home"):
    st.switch_page("Home.py")



