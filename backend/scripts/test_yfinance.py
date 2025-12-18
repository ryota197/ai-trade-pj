"""yfinance gateway テストスクリプト"""

import sys
sys.path.insert(0, "/Users/ooiryouta/dev/ai-trade-app/backend")

from src.infrastructure.gateways.yfinance_gateway import YFinanceGateway


def test_quote():
    """株価取得テスト"""
    print("=== Quote Test ===")
    gateway = YFinanceGateway()

    symbols = ["AAPL", "MSFT", "GOOGL"]
    for symbol in symbols:
        try:
            quote = gateway.get_quote(symbol)
            print(f"\n{quote.symbol}:")
            print(f"  Price: ${quote.price:.2f}")
            print(f"  Change: ${quote.change:.2f} ({quote.change_percent:.2f}%)")
            print(f"  Volume: {quote.volume:,}")
            if quote.market_cap:
                print(f"  Market Cap: ${quote.market_cap:,.0f}")
            if quote.pe_ratio:
                print(f"  P/E Ratio: {quote.pe_ratio:.2f}")
        except Exception as e:
            print(f"\n{symbol}: Error - {e}")


def test_history():
    """過去データ取得テスト"""
    print("\n=== History Test ===")
    gateway = YFinanceGateway()

    symbol = "AAPL"
    try:
        history = gateway.get_history(symbol, period="5d", interval="1d")
        print(f"\n{symbol} - Last 5 days:")
        for h in history:
            print(f"  {h.date.strftime('%Y-%m-%d')}: Open=${h.open:.2f}, Close=${h.close:.2f}, Volume={h.volume:,}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_quote()
    test_history()
    print("\n=== Test Complete ===")
