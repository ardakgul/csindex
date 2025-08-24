import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime, timedelta
import pytz
import logging
import sys
import os
from typing import Dict, List, Optional
import time
from colorama import init, Fore, Style

# Reuters Business RSS constant (requested)
REUTERS_BUSINESS_RSS = "http://feeds.reuters.com/reuters/businessNews"

# Optional transformer-based sentiment analyzer (lightweight DistilBERT fine-tuned)
try:
    from transformers import pipeline  # type: ignore
    try:
        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
    except Exception as _model_err:
        sentiment_analyzer = None  # Will fallback to keyword scoring
except ImportError:
    sentiment_analyzer = None  # transformers not installed; will fallback

init()  # Initialize colorama for Windows

def distance_based_score(current, ma, max_deviation=0.20):
    """
    Calculate score based on percentage distance from moving average.
    
    Args:
        current: Current price/value
        ma: Moving average value
        max_deviation: Maximum expected deviation (default 20% = 0.20)
    
    Returns:
        score: 0-100 where 50 = at MA, >50 = above MA, <50 = below MA
        diff_ratio: Actual percentage difference from MA
    
    Examples:
        - At MA (0% difference): Score = 50
        - 10% above MA: Score = 75  
        - 10% below MA: Score = 25
        - 20% above MA: Score = 100
        - 20% below MA: Score = 0
    """
    if ma == 0:
        return 50.0, 0.0
    
    diff_ratio = (current - ma) / ma
    
    # Normalize the difference to a 0-100 scale
    # max_deviation maps to 50 points above/below neutral (50)
    normalized_diff = diff_ratio / max_deviation
    
    # Cap at -1 to 1 range to keep scores between 0-100
    normalized_diff = max(-1, min(1, normalized_diff))
    
    # Convert to 0-100 score where 50 is neutral
    score = 50 + (normalized_diff * 50)
    
    return float(score), float(diff_ratio)

def distance_based_score_reversed(current, ma, max_deviation=0.20):
    """
    Reversed scoring for instruments where lower values indicate bullish sentiment
    (like VIX, bond yields, gold in risk-on environments)
    """
    if ma == 0: 
        return 50.0, 0.0
    
    # Reverse the current and ma for opposite scoring
    diff_ratio = (ma - current) / ma
    
    normalized_diff = diff_ratio / max_deviation
    normalized_diff = max(-1, min(1, normalized_diff))
    
    score = 50 + (normalized_diff * 50)
    
    return float(score), float(-diff_ratio)  # Return actual diff for logging

class CloudyShinyIndexCalculator:
    """
    Enhanced Cloudy&Shiny Index Calculator with comprehensive market sentiment analysis
    """
    
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
          # Global market components with enhanced weightings
        # GDP-adjusted component weights (sum to 100%)
        # Categories: US Markets 31.8%, International 35.2%, Risk & Volatility 15%, Safe Havens 10%, Sentiment 8%
        self.components = {
            # US Markets (31.8% total weight)
            'SPY': {'weight': 0.159, 'name': 'S&P 500', 'type': 'equity', 'region': 'US'},
            'QQQ': {'weight': 0.159, 'name': 'NASDAQ 100', 'type': 'equity', 'region': 'US'},

            # International Markets (35.2% total weight)
            '000001.SS': {'weight': 0.205, 'name': 'Shanghai Composite', 'type': 'equity', 'region': 'China'},
            '^N225': {'weight': 0.046, 'name': 'Nikkei 225', 'type': 'equity', 'region': 'Japan'},
            '^HSI': {'weight': 0.004, 'name': 'Hang Seng', 'type': 'equity', 'region': 'Hong Kong'},
            'XU100.IS': {'weight': 0.012, 'name': 'BIST 100', 'type': 'equity', 'region': 'Turkey'},
            '^GDAXI': {'weight': 0.051, 'name': 'DAX', 'type': 'equity', 'region': 'Germany'},
            '^FCHI': {'weight': 0.034, 'name': 'CAC 40', 'type': 'equity', 'region': 'France'},

            # Risk & Volatility Indicators (15% total weight)
            '^VIX': {'weight': 0.10, 'name': 'Volatility Index', 'type': 'volatility', 'inverse': True, 'region': 'Global'},
            'TLT': {'weight': 0.05, 'name': 'US 20Y Treasury', 'type': 'bonds', 'inverse': True, 'region': 'US'},

            # Commodities & Safe Havens (10% total weight)
            'GLD': {'weight': 0.06, 'name': 'Gold', 'type': 'commodity', 'inverse': True, 'region': 'Global'},
            'DX-Y.NYB': {'weight': 0.04, 'name': 'US Dollar Index', 'type': 'currency', 'region': 'Global'},

            # Sentiment Indicator (8% total weight)
            'NEWS_SENTIMENT': {'weight': 0.08, 'name': 'News Sentiment', 'type': 'sentiment', 'region': 'Global'}
        }

        # Enhanced sentiment sources
        self.news_sources = [
            'https://finance.yahoo.com/news/',
            'https://www.marketwatch.com/latest-news',
            'https://www.cnbc.com/markets/'
        ]

        # Reuters RSS feed for business news (using constant)
        self.reuters_rss_url = REUTERS_BUSINESS_RSS
        
    def setup_logging(self):
        """Setup comprehensive logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cloudy_shiny_index.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        """Create necessary directories"""
        directories = ['data', 'website', 'website/data', 'logs', 'backup']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def get_market_data(self, symbol: str, period: str = "90d") -> Optional[pd.DataFrame]:
        """Enhanced market data retrieval with error handling and current price updates"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data with longer period to ensure sufficient data for MA50
            data = ticker.history(period=period)
            
            if data.empty:
                self.logger.warning(f"No data found for {symbol}")
                return None
            
            # Try to get current/real-time price information
            try:
                info = ticker.info
                current_price = None
                
                # Try different price sources in order of preference
                price_sources = ['regularMarketPrice', 'currentPrice', 'preMarketPrice', 'postMarketPrice']
                for source in price_sources:
                    price = info.get(source)
                    if price and price > 0:
                        current_price = float(price)
                        self.logger.info(f"{symbol}: Using {source} = {current_price:.2f}")
                        break
                
                # If we have a more recent price, update the latest data point
                if current_price and current_price != data['Close'].iloc[-1]:
                    latest_date = data.index[-1]
                    
                    # Check if the latest data is from a previous trading day
                    from datetime import datetime
                    today = datetime.now().date()
                    latest_data_date = latest_date.date()
                    
                    if latest_data_date < today:
                        # Add a new row for current day with estimated data
                        new_index = pd.Timestamp.now().floor('D')
                        
                        # Create new row with current price
                        new_row = pd.DataFrame({
                            'Open': [current_price],
                            'High': [current_price],
                            'Low': [current_price], 
                            'Close': [current_price],
                            'Volume': [data['Volume'].iloc[-1]]  # Use previous day's volume as estimate
                        }, index=[new_index])
                        
                        # Append to existing data
                        data = pd.concat([data, new_row])
                        self.logger.info(f"{symbol}: Added current day data with price {current_price:.2f}")
                    else:
                        # Update the existing latest day's close price
                        data.loc[latest_date, 'Close'] = current_price
                        data.loc[latest_date, 'High'] = max(data.loc[latest_date, 'High'], current_price)
                        data.loc[latest_date, 'Low'] = min(data.loc[latest_date, 'Low'], current_price)
                        self.logger.info(f"{symbol}: Updated latest close price to {current_price:.2f}")
                        
            except Exception as e:
                self.logger.warning(f"Could not update current price for {symbol}: {e}")
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None
            
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators"""
        if data is None or len(data) < 2: # Changed minimum length
            return {}
            
        try:
            # Price-based indicators
            current_price = data['Close'].iloc[-1]
            ma_50 = data['Close'].rolling(window=min(50, len(data))).mean().iloc[-1]
            
            return {
                'current_price': current_price,
                'ma_50': ma_50,
            }
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {}
            
    def _model_sentiment_score(self, text: str) -> Optional[float]:
        """Return 0-100 sentiment score using transformer model if available."""
        if not sentiment_analyzer or not text.strip():
            return None
        try:
            result = sentiment_analyzer(text[:450])  # truncate overly long
            if result and isinstance(result, list):
                res = result[0]
                label = res.get('label', '')
                score = float(res.get('score', 0.0))
                if label.upper().startswith('NEG'):
                    # Map negative prob to lower half
                    return (1 - score) * 100 * 0.5  # 0-50 range
                else:
                    return 50 + score * 50  # 50-100 range
        except Exception:
            return None
        return None

    def analyze_reuters_rss(self) -> Dict:
        """Analyze Reuters Business RSS feed for sentiment (keyword + model blend if available)"""
        try:
            import feedparser
        except ImportError:
            self.logger.warning("feedparser not available, installing...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser"])
            import feedparser
        
        sentiment_scores = []
        analyzed_headlines = []
        total_headlines = 0
        
        # Enhanced sentiment keywords with scoring weights (same as news sentiment)
        positive_keywords = {
            'strong': 3, 'surge': 4, 'soar': 4, 'rally': 3, 'boom': 4, 'breakout': 3,
            'gain': 2, 'rise': 2, 'up': 1, 'bull': 3, 'positive': 2, 'growth': 2,
            'advance': 2, 'jump': 3, 'climb': 2, 'recovery': 3, 'optimism': 3,
            'outperform': 3, 'beat': 2, 'exceed': 2, 'record': 2, 'high': 1
        }
        
        negative_keywords = {
            'crash': 5, 'plunge': 4, 'collapse': 5, 'slump': 4, 'tumble': 4,
            'fall': 2, 'drop': 2, 'down': 1, 'bear': 3, 'negative': 2, 'decline': 2,
            'weak': 2, 'struggle': 3, 'concern': 2, 'fear': 3, 'uncertainty': 3,
            'risk': 2, 'loss': 2, 'miss': 2, 'disappoint': 3, 'warning': 3,
            'crisis': 4, 'recession': 4, 'inflation': 2, 'sell-off': 4, 'correction': 3,
            'volatility': 2, 'pressure': 2, 'downturn': 3, 'retreat': 2, 'pullback': 2, 'slide': 2
        }
        
        try:
            # Parse Reuters RSS feed
            feed = feedparser.parse(self.reuters_rss_url)
            
            if feed.entries:
                for entry in feed.entries[:20]:  # Analyze up to 20 latest entries
                    # Combine title and summary for analysis
                    text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower().strip()
                    
                    if len(text) < 10:
                        continue
                    
                    total_headlines += 1
                    analyzed_headlines.append(text[:100])
                    
                    # Keyword sentiment
                    pos_score = sum(weight for word, weight in positive_keywords.items() if word in text)
                    neg_score = sum(weight for word, weight in negative_keywords.items() if word in text)
                    if pos_score == 0 and neg_score == 0:
                        keyword_sent = 50
                    else:
                        net = pos_score - neg_score
                        keyword_sent = 50 + max(-8, min(8, net)) * 5  # clamp
                        keyword_sent = max(10, min(90, keyword_sent))

                    # Model sentiment (if available)
                    model_sent = self._model_sentiment_score(text)
                    if model_sent is not None:
                        headline_sentiment = (keyword_sent * 0.5) + (model_sent * 0.5)
                    else:
                        headline_sentiment = keyword_sent

                    sentiment_scores.append(headline_sentiment)
                    
            else:
                self.logger.warning("No entries found in Reuters RSS feed")
                
        except Exception as e:
            self.logger.error(f"Error analyzing Reuters RSS: {e}")
            return {'score': 50, 'strength': 0, 'headlines_analyzed': 0}
        
        # Calculate overall sentiment
        if sentiment_scores:
            overall_sentiment = np.mean(sentiment_scores)
        else:
            overall_sentiment = 50  # Default neutral
            
        # Calculate sentiment strength
        sentiment_deviation = abs(overall_sentiment - 50)
        sentiment_strength = min(1.0, sentiment_deviation / 40)
        
        result = {
            'score': round(overall_sentiment, 2),
            'strength': round(sentiment_strength, 3),
            'headlines_analyzed': total_headlines
        }
        
        self.logger.info(f"Reuters RSS sentiment: {result['score']:.1f} (strength: {result['strength']:.2f}, headlines: {total_headlines})")
        
        return result
        
    def analyze_news_sentiment(self) -> Dict:
        """Enhanced news sentiment analysis with keyword + transformer blending when available."""
        sentiment_scores: List[float] = []
        analyzed_headlines: List[str] = []
        total_headlines = 0

        positive_keywords = {
            'strong': 3, 'surge': 4, 'soar': 4, 'rally': 3, 'boom': 4, 'breakout': 3,
            'gain': 2, 'rise': 2, 'up': 1, 'bull': 3, 'positive': 2, 'growth': 2,
            'advance': 2, 'jump': 3, 'climb': 2, 'recovery': 3, 'optimism': 3,
            'outperform': 3, 'beat': 2, 'exceed': 2, 'record': 2, 'high': 1
        }
        negative_keywords = {
            'crash': 5, 'plunge': 4, 'collapse': 5, 'slump': 4, 'tumble': 4,
            'fall': 2, 'drop': 2, 'down': 1, 'bear': 3, 'negative': 2, 'decline': 2,
            'weak': 2, 'struggle': 3, 'concern': 2, 'fear': 3, 'uncertainty': 3,
            'risk': 2, 'loss': 2, 'miss': 2, 'disappoint': 3, 'warning': 3,
            'crisis': 4, 'recession': 4, 'inflation': 2
        }
        negative_keywords.update({
            'sell-off': 4, 'correction': 3, 'volatility': 2, 'pressure': 2,
            'downturn': 3, 'retreat': 2, 'pullback': 2, 'slide': 2
        })

        for source in self.news_sources[:3]:
            try:
                response = requests.get(source, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(response.content, 'html.parser')
                if 'yahoo.com' in source:
                    headlines = soup.find_all(['h3', 'h4'], class_=lambda x: x and ('title' in x.lower() or 'headline' in x.lower()), limit=15)
                elif 'marketwatch.com' in source:
                    headlines = soup.find_all(['h1', 'h2', 'h3'], limit=15)
                elif 'cnbc.com' in source:
                    headlines = soup.find_all(['h2', 'h3'], limit=15)
                else:
                    headlines = soup.find_all(['h1', 'h2', 'h3'], limit=15)
                if not headlines:
                    headlines = soup.find_all(['h1', 'h2', 'h3', 'h4'], limit=20)
                source_sentiment_scores: List[float] = []
                for headline in headlines:
                    text = headline.get_text().lower().strip()
                    if len(text) < 10 or any(skip in text for skip in ['menu', 'nav', 'subscribe', 'sign in']):
                        continue
                    total_headlines += 1
                    analyzed_headlines.append(text[:140])
                    pos_score = sum(w for word, w in positive_keywords.items() if word in text)
                    neg_score = sum(w for word, w in negative_keywords.items() if word in text)
                    if pos_score == 0 and neg_score == 0:
                        keyword_sent = 50
                    else:
                        net = pos_score - neg_score
                        keyword_sent = min(90, 50 + net * 5) if net > 0 else max(10, 50 + net * 5)
                    model_sent = self._model_sentiment_score(text)
                    headline_sentiment = 0.5 * keyword_sent + 0.5 * model_sent if model_sent is not None else keyword_sent
                    source_sentiment_scores.append(headline_sentiment)
                if source_sentiment_scores:
                    source_avg = np.mean(source_sentiment_scores)
                    sentiment_scores.append(source_avg)
                    self.logger.info(f"Source sentiment from {source}: {source_avg:.1f} ({len(source_sentiment_scores)} headlines)")
            except Exception as e:
                self.logger.error(f"Error analyzing sentiment from {source}: {e}")
                continue

        if sentiment_scores:
            overall_sentiment = np.mean(sentiment_scores)
            if len(sentiment_scores) >= 2:
                sentiment_std = np.std(sentiment_scores)
                if sentiment_std > 15:
                    overall_sentiment = overall_sentiment * 0.9 + 5
        else:
            overall_sentiment = 50
        sentiment_deviation = abs(overall_sentiment - 50)
        sentiment_strength = min(1.0, sentiment_deviation / 40)
        result = {
            'score': round(overall_sentiment, 2),
            'strength': round(sentiment_strength, 3),
            'sources_analyzed': len(sentiment_scores),
            'headlines_analyzed': total_headlines,
            'impact_weight': round(0.15 + (sentiment_strength * 0.10), 3),
            'sample_headlines': analyzed_headlines[:10]
        }
        self.logger.info(f"News sentiment: {result['score']:.1f} (strength: {result['strength']:.2f}, impact: {result['impact_weight']:.1%})")
        self.logger.info(f"Analyzed {total_headlines} headlines from {len(sentiment_scores)} sources")
        return result
        
    def calculate_component_score(self, symbol: str, component_info: Dict) -> Dict:
        """Calculate individual component score using distance-based scoring"""
        
        # Handle news sentiment as a special component
        if symbol == 'NEWS_SENTIMENT':
            news_sentiment = self.analyze_news_sentiment()
            return {
                'symbol': symbol,
                'name': component_info['name'],
                'score': news_sentiment['score'],
                'weight': component_info['weight'],
                'contribution': component_info['weight'] * news_sentiment['score'],
                'status': 'Active',
                'indicators': {
                    'sentiment_strength': news_sentiment['strength'],
                    'sources_analyzed': news_sentiment['sources_analyzed'],
                    'headlines_analyzed': news_sentiment['headlines_analyzed'],
                    'sample_headlines': news_sentiment.get('sample_headlines', [])
                },
                'type': component_info['type']
            }
        
    # Reuters RSS component removed in GDP-adjusted weighting revision
        
        data = self.get_market_data(symbol)
        
        if data is None:
            return {
                'symbol': symbol,
                'name': component_info['name'],
                'score': 50,
                'weight': component_info['weight'],
                'contribution': component_info['weight'] * 50,
                'status': 'No Data',
                'indicators': {},
                'type': component_info['type']
            }
            
        indicators = self.calculate_technical_indicators(data)
        
        if not indicators:
            return {
                'symbol': symbol,
                'name': component_info['name'],
                'score': 50,
                'weight': component_info['weight'],
                'contribution': component_info['weight'] * 50,
                'status': 'No Data',
                'indicators': {},
                'type': component_info['type']
            }
        
        # Use distance-based scoring with 50-day MA
        current_price = indicators.get('current_price')
        ma_50 = indicators.get('ma_50')
        
        if current_price and ma_50 and not pd.isna(current_price) and not pd.isna(ma_50):
            # Apply inverse logic for VIX and other reverse-scored instruments
            if component_info.get('inverse', False):
                score, diff_ratio = distance_based_score_reversed(current_price, ma_50, max_deviation=0.20)
            else:
                score, diff_ratio = distance_based_score(current_price, ma_50, max_deviation=0.20)
            
        else:
            # Fallback to simple calculation if MA data unavailable
            score = 50
            diff_ratio = 0
            
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        self.logger.info(f"{symbol}: Current={current_price:.2f}, Score={score:.1f}")
        
        return {
            'symbol': symbol,
            'name': component_info['name'],
            'score': score,
            'weight': component_info['weight'],
            'contribution': component_info['weight'] * score,
            'status': 'Active',
            'indicators': indicators,
            'type': component_info['type']
        }
        
    def calculate_index(self) -> Dict:
        """Calculate the complete Cloudy&Shiny Index"""
        self.logger.info("Starting Cloudy&Shiny Index calculation...")
        
        calculation_start = time.time()
        component_results = []
        total_weighted_score = 0
        total_weight = 0
        
        # Calculate individual component scores
        for symbol, info in self.components.items():
            component_result = self.calculate_component_score(symbol, info)
            component_results.append(component_result)
            
            if component_result['status'] == 'Active':
                total_weighted_score += component_result['contribution']
                total_weight += component_result['weight']
                
        # Calculate base index from components (now includes all sentiment sources)
        base_index = total_weighted_score / total_weight if total_weight > 0 else 50
        
        # No external adjustments needed - all sentiment is now in components
        final_index = base_index
        
        # Ensure final index stays within bounds
        final_index = max(0, min(100, final_index))
          # Determine market sentiment
        if final_index >= 75:
            sentiment = "Extreme Shiny"
            color = Fore.GREEN
        elif final_index >= 51:
            sentiment = "Shiny"
            color = Fore.LIGHTGREEN_EX
        elif final_index >= 50:
            sentiment = "Neutral"
            color = Fore.YELLOW
        elif final_index >= 25:
            sentiment = "Cloudy"
            color = Fore.LIGHTRED_EX
        else:
            sentiment = "Extreme Cloudy"
            color = Fore.RED
            
        calculation_time = time.time() - calculation_start
        
        result = {
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'index_value': round(final_index, 2),
            'base_index': round(base_index, 2),
            'sentiment': sentiment,
            'components': component_results,
            'calculation_time': round(calculation_time, 2),
            'active_components': len([c for c in component_results if c['status'] == 'Active']),
            'total_components': len(component_results)
        }
        
        # Log results with color
        self.logger.info(f"{color}Cloudy&Shiny Index: {final_index:.2f} ({sentiment}){Style.RESET_ALL}")
        self.logger.info(f"Base Index: {base_index:.2f} (All sentiment now integrated in components)")
        self.logger.info(f"Active components: {result['active_components']}/{result['total_components']}")
        self.logger.info(f"Calculation completed in {calculation_time:.2f} seconds")
        
        return result
        
    def save_results(self, result: Dict):
        """Save calculation results to multiple formats + rolling history & health"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to CSV
        csv_filename = f"data/cloudy_shiny_index_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Final Index', 'Base Index', 'Sentiment', 'Components Active'])
            writer.writerow([
                result['timestamp'],
                result['index_value'],
                result['base_index'],
                result['sentiment'],
                f"{result['active_components']}/{result['total_components']}"
            ])
            
            writer.writerow([])
            writer.writerow(['Component', 'Symbol', 'Score', 'Weight', 'Contribution', 'Status'])
            for comp in result['components']:
                writer.writerow([
                    comp.get('name', comp.get('symbol', 'Unknown')),
                    comp.get('symbol', 'Unknown'),
                    comp.get('score', 50),
                    comp.get('weight', 0),
                    comp.get('contribution', 0),
                    comp.get('status', 'Unknown')
                ])
                
        # Save to JSON for website
        json_filename = f"data/cloudy_shiny_index_{timestamp}.json"
        with open(json_filename, 'w') as jsonfile:
            json.dump(result, jsonfile, indent=2, default=str)
            
        # Update current data files
        os.makedirs('website/data', exist_ok=True)
        with open('website/data/current_index.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)

        # Rolling history (append & trim)
        history_path = 'website/data/history.json'
        history = {"series": []}
        if os.path.exists(history_path):
            try:
                with open(history_path) as fh:
                    history = json.load(fh) or {"series": []}
            except Exception:
                history = {"series": []}
        history.setdefault('series', [])
        history['series'].append({
            'timestamp': result['timestamp'],
            'index_value': result['index_value']
        })
        # keep last 500 points
        history['series'] = history['series'][-500:]
        with open(history_path, 'w') as fh:
            json.dump(history, fh, indent=2)

        # Health file
        health = {
            'last_run': result['timestamp'],
            'active_components': result['active_components'],
            'total_components': result['total_components'],
            'calculation_time': result['calculation_time']
        }
        with open('website/data/health.json', 'w') as fh:
            json.dump(health, fh, indent=2)

        # News sentiment standalone file
        news_component = next((c for c in result['components'] if c['symbol'] == 'NEWS_SENTIMENT'), None)
        if news_component:
            with open('website/data/news_sentiment.json', 'w') as fh:
                json.dump(news_component['indicators'] | {'score': news_component['score']}, fh, indent=2)

        # Copy current index into frontend public (dev convenience)
        try:
            os.makedirs('frontend/public/data', exist_ok=True)
            # Copy files needed for static GitHub Pages dashboard
            with open('frontend/public/data/current_index.json', 'w') as fpub:
                json.dump({
                    'timestamp': result['timestamp'],
                    'index_value': result['index_value'],
                    'sentiment': result['sentiment'],
                    'components': result['components'],
                    'active_components': result['active_components'],
                    'total_components': result['total_components']
                }, fpub, indent=2)
            # history
            if os.path.exists(history_path):
                import shutil
                shutil.copy2(history_path, 'frontend/public/data/history.json')
            # health
            if os.path.exists('website/data/health.json'):
                import shutil
                shutil.copy2('website/data/health.json', 'frontend/public/data/health.json')
            # news sentiment
            if os.path.exists('website/data/news_sentiment.json'):
                import shutil
                shutil.copy2('website/data/news_sentiment.json', 'frontend/public/data/news_sentiment.json')
        except Exception:
            pass
        self.logger.info(f"Results saved to {csv_filename} and {json_filename}; history & health updated")
        return csv_filename, json_filename

if __name__ == "__main__":
    calculator = CloudyShinyIndexCalculator()
    
    try:
        result = calculator.calculate_index()
        csv_file, json_file = calculator.save_results(result)
        
        print(f"\n{Fore.CYAN}=== CLOUDY&SHINY INDEX REPORT ==={Style.RESET_ALL}")
        print(f"Final Index: {Fore.YELLOW}{result['index_value']:.2f}{Style.RESET_ALL}")
        print(f"Base Index: {result['base_index']:.2f}")
        print(f"Sentiment: {Fore.GREEN if 'Shiny' in result['sentiment'] else Fore.RED}{result['sentiment']}{Style.RESET_ALL}")
        print(f"Active Components: {result['active_components']}/{result['total_components']}")
        print(f"Calculation Time: {result['calculation_time']:.2f}s")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Calculation interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error during calculation: {e}{Style.RESET_ALL}")
        logging.error(f"Calculation error: {e}", exc_info=True)
