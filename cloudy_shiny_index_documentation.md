# The Cloudy & Shiny Market Index: Mathematical Framework and Implementation

## Abstract

The Cloudy & Shiny Index is a comprehensive market sentiment indicator that combines multiple asset classes, technical indicators, and external sentiment measures to produce a single numerical score representing market conditions. This document provides a complete mathematical framework for the index calculation, including the theoretical foundation, component weightings, scoring algorithms, and implementation details.

## Table of Contents

1. [Introduction](#introduction)
2. [Theoretical Foundation](#theoretical-foundation)
3. [Mathematical Framework](#mathematical-framework)
4. [Component Analysis](#component-analysis)
5. [External Sentiment Integration](#external-sentiment-integration)
6. [Interpretation Framework](#interpretation-framework)
7. [Technical Implementation](#technical-implementation)
8. [Validation and Backtesting](#validation-and-backtesting)
9. [Limitations and Future Enhancements](#limitations-and-future-enhancements)

## Introduction

The Cloudy & Shiny Index represents a novel approach to market sentiment analysis by combining diverse asset classes into a single, interpretable metric. The index name reflects its binary interpretation:
- **"Shiny"** conditions indicate favorable market sentiment (bullish)
- **"Cloudy"** conditions suggest unfavorable sentiment (bearish)

### Key Features
- Incorporates multiple asset classes with different risk characteristics
- Uses distance-based scoring relative to historical norms
- Includes both technical and fundamental sentiment measures
- Provides real-time updates with comprehensive logging

## Theoretical Foundation

### Asset Class Diversification Theory

The index is built on the principle that different asset classes respond differently to market conditions:

1. **Equity Risk Premium**: Stocks generally outperform during optimistic periods
2. **Flight to Quality**: Bonds and gold attract capital during uncertain times
3. **Volatility Clustering**: Market volatility tends to persist and signal regime changes
4. **Currency Strength**: Dollar strength often reflects risk-off sentiment

### Component Selection Rationale

**Total Weight = 1.0 (100%)**

- **US Equity (31.8%)**: SPY, QQQ
- **International Equity (35%)**: Shanghai, Nikkei, Hang Seng, DAX, CAC 40, BIST 100
- **Risk & Volatility (15%)**: VIX, TLT
- **Commodities & Safe Havens (10%)**: GLD, DXY

## Mathematical Framework

### Core Distance-Based Scoring Function

The fundamental scoring mechanism measures how far current prices deviate from their moving averages:

```
Score(P_t, MA_t) = 50 + 50 × (NormDiff(P_t, MA_t) / MaxDev)
```

Where:
- `NormDiff(P_t, MA_t) = (P_t - MA_t) / MA_t`
- `MaxDev = 0.20` (20% maximum expected deviation)
- `P_t` = Current price
- `MA_t` = 30-day moving average

**Key Properties:**
- Score at MA (0% difference): **50**
- 10% above MA: Score = **75**
- 10% below MA: Score = **25**
- 20% above MA: Score = **100**
- 20% below MA: Score = **0**

### Inverse Scoring for Contrarian Indicators

For assets with inverse relationships to market optimism (VIX, TLT, GLD, DXY):

```
Score_inverse(P_t, MA_t) = 50 - 50 × (NormDiff(P_t, MA_t) / MaxDev)
```

This ensures:
- Higher VIX values contribute negatively to the index
- Higher gold prices (flight to safety) reduce the index
- Higher Treasury prices (lower yields) indicate risk-off sentiment

### Technical Indicator Adjustments

The base distance score is adjusted by several technical indicators:

#### RSI Adjustment
- **RSI > 70 (overbought)**: -3 points
- **RSI < 30 (oversold)**: +3 points
- **40 ≤ RSI ≤ 60 (healthy)**: +2 points
- **Otherwise**: 0 points

#### Volume Confirmation
- **Volume/Average > 1.5 (high volume)**: +2 points
- **Volume/Average < 0.5 (low volume)**: -1 point
- **Otherwise**: 0 points

#### Short-term Momentum
- **Price > MA5 (and not inverse)**: +2 points
- **Price < MA5 (and not inverse)**: -2 points
- **Otherwise**: 0 points

### Final Component Score

```
S_i = max(0, min(100, S_base_i + RSI_adj_i + Vol_adj_i + Mom_adj_i))
```

### Index Aggregation

The final Cloudy & Shiny Index is computed as a weighted average:

```
CS Index = Σ(w_i × S_i) / Σ(w_i)
```

Where:
- `w_i` = weight of component i
- `S_i` = score of component i
- Sum over all active components

## Component Analysis

### Detailed Component Weights

| Symbol | Name | Type | Weight | Region |
|--------|------|------|--------|--------|
| SPY | S&P 500 | US Equity | 0.159 | US |
| QQQ | NASDAQ 100 | US Equity | 0.159 | US |
| 000001.SS | Shanghai Composite | International Equity | 0.205 | China |
| ^N225 | Nikkei 225 | International Equity | 0.046 | Japan |
| ^HSI | Hang Seng | International Equity | 0.004 | Hong Kong |
| XU100.IS | BIST 100 | International Equity | 0.012 | Turkey |
| ^GDAXI | DAX | International Equity | 0.051 | Germany |
| ^FCHI | CAC 40 | International Equity | 0.034 | France |
| ^VIX | Volatility Index | Risk (Inverse) | 0.10 | Global |
| TLT | US 20Y Treasury | Bonds (Inverse) | 0.05 | US |
| GLD | Gold | Commodity (Inverse) | 0.06 | Global |
| DX-Y.NYB | US Dollar Index | Currency | 0.04 | Global |
| NEWS_SENTIMENT | Aggregated News Sentiment | Sentiment | 0.08 | Global |

## External Sentiment Integration

### Fear & Greed Index
- Source: CNN Fear & Greed Index API
- Range: 0-100
- Integration: Used for validation and additional context

### News Sentiment Analysis
News sentiment blends weighted keyword scoring with an optional DistilBERT (SST-2) transformer model (averaged 50/50 when available). Sources:
- Yahoo Finance News
- MarketWatch
- CNBC Markets
- Reuters Business RSS (auxiliary, integrated but not separately weighted)

**Sentiment Scoring (Keyword Core):**
- Positive minus negative weighted keyword net mapped into 10–90 band (capped)
- Transformer probability blends into final 0–100 (neutral pivot 50) when available

**Positive Keywords:** gain, rise, up, bull, positive, strong, growth, rally
**Negative Keywords:** fall, drop, down, bear, negative, weak, decline, crash

## Interpretation Framework

### Index Ranges and Sentiment Classification

| Range | Sentiment | Market Condition |
|-------|-----------|------------------|
| ≥ 75 | Extreme Shiny | Strong Bull Market |
| 51-74 | Shiny | Bull Market |
| = 50 | Neutral | Balanced Market |
| 25-49 | Cloudy | Bear Market |
| < 25 | Extreme Cloudy | Strong Bear Market |

### Statistical Properties

- **Expected mean**: μ = 50 (neutral market conditions)
- **Theoretical range**: [0, 100]
- **Practical range**: [20, 80] (due to diversification effects)
- **Standard deviation**: σ ≈ 15 (empirically observed)

## Technical Implementation

### Data Sources
- **Yahoo Finance API**: Price data for all components
- **Alternative.me API**: Fear & Greed Index
- **Web Scraping**: News sentiment analysis

### Update Frequencies
- **Real-time**: Price data and technical indicators
- **Daily**: News sentiment analysis
- **API-dependent**: Fear & Greed Index

### Error Handling
The system includes comprehensive error handling with effective weight recalculation:

```
Component_Weight_effective = (w_i × DataAvailable) / Σ(w_j × DataAvailable)
```

## Output Structure

### Primary Outputs
1. **Index Value**: Final numerical score [0, 100]
2. **Sentiment Classification**: Text interpretation
3. **Component Breakdown**: Individual scores and contributions
4. **Active Components**: Number of components with valid data
5. **External Indicators**: Fear & Greed and News sentiment
6. **Calculation Time**: Performance metrics

### File Formats
1. **CSV Format**: `data/cloudy_shiny_index_YYYYMMDD_HHMMSS.csv`
2. **JSON Format**: `data/cloudy_shiny_index_YYYYMMDD_HHMMSS.json`
3. **Current Data**: `website/data/current_index.json`

## Validation and Backtesting

### Expected Performance Patterns
- **Bull market periods**: Index should trend above 55
- **Bear market periods**: Index should trend below 45
- **Market crashes**: Index should drop below 30
- **Market recoveries**: Index should show upward momentum

### Component Contribution Analysis
Regular analysis validates the weighting scheme:

```
Contribution_i = w_i × S_i
Relative_Contribution_i = Contribution_i / Σ(Contribution_j)
```

## Limitations and Future Enhancements

### Current Limitations
1. Fixed weighting scheme may not adapt to changing market conditions
2. News sentiment analysis uses simple keyword matching
3. Limited to major market hours due to data availability
4. Susceptible to data quality issues from external sources

### Potential Enhancements
1. **Dynamic Weighting**: Implement regime-dependent weights
2. **Machine Learning**: Use NLP for better sentiment analysis
3. **Additional Data Sources**: Include options data, insider trading
4. **Regional Variations**: Create region-specific indices

## Conclusion

The Cloudy & Shiny Index provides a mathematically rigorous framework for combining multiple market indicators into a single, interpretable sentiment measure. The distance-based scoring system, combined with technical adjustments and external sentiment validation, creates a robust indicator suitable for both quantitative analysis and intuitive interpretation.

The index's strength lies in its diversification across asset classes and its ability to adapt to different market conditions through its component weighting system. While limitations exist, the framework provides a solid foundation for market sentiment analysis and can be extended with additional data sources and analytical techniques.

---

*Generated on: June 24, 2025*
