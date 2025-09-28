# -*- coding: utf-8 -*-

import streamlit as st
import requests
import pandas as pd
import altair as alt
from textblob import TextBlob

# Streamlit page settings
st.set_page_config(
    page_title="News Sentiment Dashboard",
    page_icon="📰",
    layout="wide"
)

# Function to fetch and analyze news from GNews API
@st.cache_data(ttl=600)
def fetch_and_analyze_news(api_key: str, query: str) -> pd.DataFrame:
    url = f"https://gnews.io/api/v4/search?q={query}&lang=en&token={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            st.warning("No articles found for this query.")
            return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching news: {e}")
        return pd.DataFrame()

    analyzed_articles = []
    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "")
        url = article.get("url", "")
        source = article.get("source", {}).get("name", "Unknown")

        if not title:
            continue

        text = f"{title} {description}".strip()
        polarity = TextBlob(text).sentiment.polarity

        if polarity > 0.1:
            sentiment = "Positive"
        elif polarity < -0.1:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        analyzed_articles.append({
            "title": title,
            "source": source,
            "sentiment_score": round(polarity, 3),
            "sentiment_label": sentiment,
            "url": url
        })

    return pd.DataFrame(analyzed_articles)


# UI
st.title("Real-Time News Sentiment Dashboard")
st.markdown("Powered by **GNews**, **TextBlob**, and **Streamlit**.")

with st.sidebar:
    st.header("settings")
    api_key_secret = st.secrets.get("GNEWS_API_KEY", "")
    if not api_key_secret:
        api_key_secret = st.text_input("Enter your GNews API Key", type="password")

    query = st.text_input("Enter a news topic")

    refresh_button = st.button("Fetch and Analyze News", type="primary")


if refresh_button and api_key_secret:
    with st.spinner("Fetching news and running analysis... Please wait."):
        df = fetch_and_analyze_news(api_key_secret, query)

    if not df.empty:
        st.success(f" Successfully analyzed {len(df)} articles for '{query}'!")

        sentiment_counts = df["sentiment_label"].value_counts()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Articles", len(df))
        col2.metric("✅ Positive", sentiment_counts.get("Positive", 0))
        col3.metric("❌ Negative", sentiment_counts.get("Negative", 0))

        # Sentiment distribution chart
        st.subheader("Sentiment Distribution")
        chart_data = pd.DataFrame(sentiment_counts).reset_index()
        chart_data.columns = ["sentiment", "count"]

        chart = alt.Chart(chart_data).mark_bar(size=40).encode(
            x=alt.X("sentiment", axis=alt.Axis(title="Sentiment")),
            y=alt.Y("count", axis=alt.Axis(title="Number of Articles")),
            color=alt.Color("sentiment",
                            scale=alt.Scale(
                                domain=["Positive", "Negative", "Neutral"],
                                range=["#2ca02c", "#d62728", "#7f7f7f"]
                            )),
            tooltip=["sentiment", "count"]
        ).properties(title=f"Sentiment for '{query}'")

        st.altair_chart(chart, use_container_width=True)

        # Table of analyzed news
        st.subheader("📰 Analyzed Headlines")
        st.dataframe(df, use_container_width=True, column_config={
            "url": st.column_config.LinkColumn("Article Link")
        })

    else:
        st.error("Could not retrieve or analyze news. Check your API key or query.")
else:
    st.info(" Enter your GNews API key and a topic, then click 'Fetch and Analyze News' to begin.")
