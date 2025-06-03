import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def plot_sentiment_distribution(df):
    """Plot sentiment distribution."""
    sentiment_counts = df["Sentiment"].value_counts()
    
    plt.figure(figsize=(10, 6))
    colors = {"Positive": "#4CAF50", "Negative": "#F44336", "Neutral": "#FFC107"}
    sentiment_counts.plot(kind="bar", color=[colors[x] for x in sentiment_counts.index])
    plt.title("Sentiment Distribution for LinkedIn Posts")
    plt.xlabel("Sentiment")
    plt.ylabel("Number of Posts")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("data/sentiment_distribution.png")
    plt.close()

def plot_activity_timeline(df):
    """Plot posting activity over time."""
    if "Timestamp" in df.columns:
        # Convert timestamp strings to datetime if needed
        df["parsed_time"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        
        # Group by date and count posts
        daily_activity = df.groupby(df["parsed_time"].dt.date).size()
        
        plt.figure(figsize=(12, 6))
        daily_activity.plot(kind="line", marker="o")
        plt.title("Posting Activity Timeline")
        plt.xlabel("Date")
        plt.ylabel("Number of Posts")
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.savefig("data/activity_timeline.png")
        plt.close()

def plot_top_authors(df, top_n=10):
    """Plot top authors by number of posts."""
    author_counts = df["Author"].value_counts().head(top_n)
    
    plt.figure(figsize=(12, 6))
    author_counts.plot(kind="barh")
    plt.title(f"Top {top_n} Most Active Authors")
    plt.xlabel("Number of Posts")
    plt.ylabel("Author")
    plt.tight_layout()
    plt.savefig("data/top_authors.png")
    plt.close()

def generate_visualizations(csv_file):
    """Generate all visualizations."""
    try:
        df = pd.read_csv(csv_file)
        
        plot_sentiment_distribution(df)
        plot_activity_timeline(df)
        plot_top_authors(df)
        
        print("Visualizations have been generated successfully!")
        
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")

if __name__ == "__main__":
    generate_visualizations("data/linkedin_aii_posts.csv")