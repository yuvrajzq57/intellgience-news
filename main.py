"""
Main entry point for the news analysis pipeline.
Orchestrates fetching, analysis, validation, and reporting.
"""

import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from pipeline import NewsAnalysisPipeline

def ensure_output_directory():
    """Create output directory if it doesn't exist."""
    if not os.path.exists('output'):
        os.makedirs('output')
        print("✓ Created output directory")

def save_json(data, filename):
    """Save data to JSON file in output directory."""
    filepath = os.path.join('output', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {filename}")

def generate_markdown_report(validated_results):
    """Generate a human-readable markdown report."""
    report_lines = [
        "# News Analysis Report",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Articles Analyzed:** {len(validated_results)}",
        "**Source:** NewsAPI",
        "",
        "## Summary",
        ""
    ]
    
    # Count sentiments
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    for result in validated_results:
        sentiment = result.get('analysis', {}).get('sentiment', 'neutral').lower()
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
    
    report_lines.extend([
        f"- Positive: {sentiment_counts['positive']} articles",
        f"- Negative: {sentiment_counts['negative']} articles",
        f"- Neutral: {sentiment_counts['neutral']} articles",
        "",
        "## Detailed Analysis",
        ""
    ])
    
    # Add each article
    for idx, result in enumerate(validated_results, 1):
        article = result.get('article', {})
        analysis = result.get('analysis', {})
        validation = result.get('validation', {})
        
        title = article.get('title', 'No title')
        url = article.get('url', '#')
        gist = analysis.get('gist', 'N/A')
        sentiment = analysis.get('sentiment', 'N/A')
        tone = analysis.get('tone', 'N/A')
        is_valid = validation.get('is_valid', False)
        validation_notes = validation.get('notes', 'No validation notes')
        
        validation_symbol = "✓" if is_valid else "✗"
        
        report_lines.extend([
            f"### Article {idx}: \"{title}\"",
            f"- **Source:** [{url}]({url})",
            f"- **Gist:** {gist}",
            f"- **LLM#1 Sentiment:** {sentiment}",
            f"- **LLM#2 Validation:** {validation_symbol} {validation_notes}",
            f"- **Tone:** {tone}",
            ""
        ])
    
    report_content = "\n".join(report_lines)
    
    # Save report
    filepath = os.path.join('output', 'final_report.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"✓ Generated final_report.md")
    
    return report_content

async def main():
    """Main execution flow."""
    print("=" * 60)
    print("NEWS ANALYSIS PIPELINE - DUAL LLM VALIDATION")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Step 1: Setup
    ensure_output_directory()
    
    pipeline = NewsAnalysisPipeline()
    
    # Run pipeline and listen for events
    async for event_data in pipeline.run(topic="Indian Politics", count=12):
        event_type = event_data.get('event')
        data = event_data.get('data')
        
        if event_type == 'log':
            # Parse the JSON string in data to get the message
            try:
                msg_data = json.loads(data)
                print(f"[LOG] {msg_data.get('message')}")
            except:
                print(f"[LOG] {data}")
                
        elif event_type == 'error':
            print(f"✗ ERROR: {data}")
            return
            
        elif event_type == 'close':
            print("Stream closed.")
            
        elif event_type == 'full_result':
            # Extract full data for saving
            full_data = json.loads(data)
            validated_results = full_data.get('validated_results', [])
            raw_articles = full_data.get('raw_articles', [])
            
            save_json(raw_articles, 'raw_articles.json')
            save_json(validated_results, 'validated_results.json') # Saves analysis_results implicitly as part of valid results if we want separate we'd need to emit it.
            
            # Generate report
            generate_markdown_report(validated_results)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nCheck the 'output' folder for:")
    print("  - raw_articles.json")
    print("  - validated_results.json")
    print("  - final_report.md")

if __name__ == "__main__":
    asyncio.run(main())
