# Finviz MCP Server - Tools Reference

## 🔍 Screening Tools

### `earnings_screener`
Basic screening for scheduled earnings announcement stocks

**Parameters:**
- `earnings_date` (required): Earnings announcement date (`today_after`, `tomorrow_before`, `this_week`, `within_2_weeks`)
- `market_cap`: Market capitalization filter (`small`, `mid`, `large`, `mega`)
- `min_price`: Minimum stock price
- `min_volume`: Minimum trading volume
- `sectors`: Target sectors

### `volume_surge_screener`
Screening for stocks with surging volume and price increase

**Parameters:**
- `market_cap`: Market capitalization filter (default: `smallover`)
- `min_price`: Minimum stock price (default: 10)
- `min_relative_volume`: Minimum relative volume ratio (default: 1.5)
- `min_price_change`: Minimum price change rate (default: 2.0%)
- `sma_filter`: Moving average filter (default: `above_sma200`)

### `trend_reversion_screener`
Screening for trend reversal candidate stocks

**Parameters:**
- `market_cap`: Market capitalization filter (default: `mid_large`)
- `eps_growth_qoq`: Minimum EPS growth rate (QoQ)
- `revenue_growth_qoq`: Minimum revenue growth rate (QoQ)
- `rsi_max`: Maximum RSI value
- `sectors`, `exclude_sectors`: Sector filter

### `uptrend_screener`
Screening for uptrend stocks

**Parameters:**
- `trend_type`: Trend type (`strong_uptrend`, `breakout`, `momentum`)
- `sma_period`: Moving average period (`20`, `50`, `200`)
- `relative_volume`: 相対出来高最低値
- `price_change`: 価格変化率最低値

### `dividend_growth_screener`
Screening for dividend growth stocks

**Parameters:**
- `min_dividend_yield`, `max_dividend_yield`: Dividend yield range
- `min_dividend_growth`: Minimum dividend growth rate
- `min_roe`: Minimum ROE
- `max_debt_equity`: Maximum debt-to-equity ratio

### `etf_screener`
ETF strategy screening

**Parameters:**
- `strategy_type`: Strategy type (`long`, `short`)
- `asset_class`: Asset class (`equity`, `bond`, `commodity`, `currency`)
- `min_aum`: Minimum assets under management
- `max_expense_ratio`: Maximum expense ratio

## 📈 Earnings-related Screening

### `earnings_premarket_screener`
Stocks rising after pre-market earnings announcements

**Parameters:**
- `earnings_timing`: Earnings announcement timing (default: `today_before`)
- `min_price_change`: Minimum price change rate (default: 2.0%)
- `include_premarket_data`: Include pre-market trading data
- `max_results`: Maximum results (default: 60)

### `earnings_afterhours_screener`
Stocks rising after after-hours earnings announcements

**Parameters:**
- `earnings_timing`: Earnings announcement timing (default: `today_after`)
- `min_afterhours_change`: Minimum after-hours price change rate (default: 2.0%)
- `include_afterhours_data`: Include after-hours trading data
- `max_results`: Maximum results (default: 60)

### `earnings_trading_screener`
Earnings trading target stocks (focus on upward revisions and surprises)

**Parameters:**
- `earnings_window`: Earnings announcement window (default: `yesterday_after_today_before`)
- `earnings_revision`: Earnings forecast revision filter (default: `eps_revenue_positive`)
- `price_trend`: Price trend filter (default: `positive_change`)
- `sort_by`: Sort key (default: `eps_surprise`)

### `earnings_winners_screener`
Screening for earnings winners (detailed list including weekly performance, EPS surprise, sales surprise)

**Parameters:**
- `earnings_period`: Earnings announcement period (default: `this_week`)
- `market_cap`: Market capitalization filter (default: `smallover`)
- `min_price`: Minimum stock price (default: $10)
- `min_avg_volume`: Minimum average volume (default: o500 = 500,000 or more)
- `min_eps_growth_qoq`: Minimum EPS growth rate QoQ (%) (default: 10%)
- `min_eps_revision`: Minimum EPS forecast revision rate (%) (default: 5%)
- `min_sales_growth_qoq`: Minimum sales growth rate QoQ (%) (default: 5%)
- `min_weekly_performance`: Weekly performance filter (default: 5to-1w)
- `sma200_filter`: Above 200-day moving average filter (default: True)
- `target_sectors`: Target sectors (default: 6 major sectors)
- `max_results`: Maximum results (default: 50)
- `sort_by`: Sort key (`performance_1w`, `eps_growth_qoq`, `eps_surprise`, `price_change`, `volume`)
- `sort_order`: Sort order (`asc`, `desc`)

### `upcoming_earnings_screener`
Screening for next week's scheduled earnings stocks (for pre-earnings trend preparation)

**Parameters:**
- `earnings_period`: Earnings announcement period (default: `next_week`)
- `market_cap`: Market capitalization filter (default: `smallover`)
- `min_price`: Minimum stock price (default: $10)
- `min_avg_volume`: Minimum average volume (default: 500,000)
- `target_sectors`: Target sectors (8 sectors)
- `max_results`: Maximum results (default: 100)
- `sort_by`: Sort key (`earnings_date`, `market_cap`, `target_price_upside`, `volatility`)
- `include_chart_view`: Include weekly chart view (default: True)
- `earnings_calendar_format`: Output in earnings calendar format (default: False)

## 📊 Fundamental Analysis

### `get_stock_fundamentals`
Get fundamental data for individual stocks

**Parameters:**
- `ticker` (required): Stock ticker
- `data_fields`: List of data fields to retrieve

### `get_multiple_stocks_fundamentals`
Batch retrieve fundamental data for multiple stocks

**Parameters:**
- `tickers` (required): List of stock tickers
- `data_fields`: List of data fields to retrieve

## 📄 SECファイリング分析

### `get_sec_filings`
指定銘柄のSECファイリングリストを取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `form_types`: フォームタイプフィルタ (例: `["10-K", "10-Q", "8-K"]`)
- `days_back`: 過去何日分のファイリング (デフォルト: 30)
- `max_results`: 最大取得件数 (デフォルト: 50)
- `sort_by`: ソート基準 (`filing_date`, `report_date`, `form`)
- `sort_order`: ソート順序 (`asc`, `desc`)

### `get_major_sec_filings`
主要SECファイリング（10-K, 10-Q, 8-K等）を取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分のファイリング (デフォルト: 90)

### `get_insider_sec_filings`
インサイダー取引関連SECファイリング（フォーム3, 4, 5等）を取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分のファイリング (デフォルト: 30)

### `get_sec_filing_summary`
指定期間のSECファイリング概要とサマリーを取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分の概要 (デフォルト: 90)

## 📰 ニュース分析

### `get_stock_news`
銘柄関連ニュースの取得

**パラメータ:**
- `ticker` (必須): 銘柄ティッカー
- `days_back`: 過去何日分のニュース (デフォルト: 7)
- `news_type`: ニュースタイプ (`all`, `earnings`, `analyst`, `insider`, `general`)

### `get_market_news`
市場全体のニュースを取得

**パラメータ:**
- `days_back`: 過去何日分のニュース (デフォルト: 3)
- `max_items`: 最大取得件数 (デフォルト: 20)

### `get_sector_news`
特定セクターのニュースを取得

**パラメータ:**
- `sector` (必須): セクター名
- `days_back`: 過去何日分のニュース (デフォルト: 5)
- `max_items`: 最大取得件数 (デフォルト: 15)

## 🏭 セクター・業界分析

### `get_sector_performance`
セクター別パフォーマンス分析

**パラメータ:**
- `timeframe`: 分析期間 (`1d`, `1w`, `1m`, `3m`, `6m`, `1y`)
- `sectors`: 対象セクターのリスト

### `get_industry_performance`
業界別パフォーマンス分析

**パラメータ:**
- `timeframe`: 分析期間 (`1d`, `1w`, `1m`, `3m`, `6m`, `1y`)
- `industries`: 対象業界のリスト

### `get_country_performance`
国別市場パフォーマンス分析

**パラメータ:**
- `timeframe`: 分析期間 (`1d`, `1w`, `1m`, `3m`, `6m`, `1y`)
- `countries`: 対象国のリスト

### `get_market_overview`
市場全体の概要を取得

**パラメータ:** なし

## 📉 テクニカル分析

### `get_relative_volume_stocks`
相対出来高異常銘柄の検出

**パラメータ:**
- `min_relative_volume` (必須): 最低相対出来高
- `min_price`: 最低株価
- `sectors`: 対象セクター
- `max_results`: 最大取得件数 (デフォルト: 50)

### `technical_analysis_screener`
テクニカル分析ベースのスクリーニング

**パラメータ:**
- `rsi_min`, `rsi_max`: RSI範囲
- `price_vs_sma20`, `price_vs_sma50`, `price_vs_sma200`: 移動平均線との関係 (`above`, `below`)
- `min_price`: 最低株価
- `min_volume`: 最低出来高
- `sectors`: 対象セクター
- `max_results`: 最大取得件数 (デフォルト: 50)

## 🔧 ユーティリティ

### `get_capitalization_performance`
時価総額別パフォーマンス分析

**パラメータ:** なし

### `get_sector_specific_industry_performance`
特定セクター内の業界別パフォーマンス分析

**パラメータ:**
- `sector` (必須): セクター名
- `timeframe`: 分析期間 (`1d`, `1w`, `1m`, `3m`, `6m`, `1y`)

## 📋 使用例

### 基本的なスクリーニング
```python
# 決算発表予定銘柄を検索
earnings_screener(
    earnings_date="today_after",
    market_cap="large",
    min_price=50
)

# 出来高急増銘柄を検索
volume_surge_screener(
    min_relative_volume=3.0,
    min_price_change=5.0
)
```

### 決算関連分析
```python
# 決算勝ち組銘柄を分析
earnings_winners_screener(
    earnings_period="this_week",
    sort_by="eps_surprise"
)

# 来週決算予定を確認
upcoming_earnings_screener(
    earnings_period="next_week",
    include_chart_view=True
)
```

### ファンダメンタル分析
```python
# 個別銘柄の詳細データ
get_stock_fundamentals(ticker="AAPL")

# 複数銘柄の比較
get_multiple_stocks_fundamentals(
    tickers=["AAPL", "MSFT", "GOOGL"]
)
``` 