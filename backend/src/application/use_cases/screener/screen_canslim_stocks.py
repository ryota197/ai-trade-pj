"""CAN-SLIMスクリーニング ユースケース"""

from datetime import datetime

from src.application.dto.screener_dto import (
    ScreenerFilterInput,
    ScreenerResultOutput,
    StockSummaryOutput,
)
from src.application.interfaces.financial_data_gateway import FinancialDataGateway
from src.domain.repositories.stock_repository import (
    ScreenerFilter,
    StockRepository,
)
from src.domain.services.relative_strength_calculator import RelativeStrengthCalculator
from src.domain.value_objects.canslim_score import CANSLIMScore


class ScreenCANSLIMStocksUseCase:
    """
    CAN-SLIMスクリーニング ユースケース

    CAN-SLIM条件に基づいて銘柄をスクリーニングし、
    投資候補を抽出する。
    """

    def __init__(
        self,
        stock_repository: StockRepository,
        financial_gateway: FinancialDataGateway,
        rs_calculator: RelativeStrengthCalculator,
    ) -> None:
        self._stock_repo = stock_repository
        self._financial_gateway = financial_gateway
        self._rs_calculator = rs_calculator

    async def execute(
        self,
        filter_input: ScreenerFilterInput,
    ) -> ScreenerResultOutput:
        """
        CAN-SLIM条件でスクリーニングを実行

        Args:
            filter_input: スクリーニング条件

        Returns:
            ScreenerResultOutput: スクリーニング結果
        """
        # 入力DTOからドメインフィルターに変換
        domain_filter = ScreenerFilter(
            min_rs_rating=filter_input.min_rs_rating,
            min_eps_growth_quarterly=filter_input.min_eps_growth_quarterly,
            min_eps_growth_annual=filter_input.min_eps_growth_annual,
            max_distance_from_52w_high=filter_input.max_distance_from_52w_high,
            min_volume_ratio=filter_input.min_volume_ratio,
            min_canslim_score=filter_input.min_canslim_score,
            min_market_cap=filter_input.min_market_cap,
            max_market_cap=filter_input.max_market_cap,
            symbols=filter_input.symbols,
        )

        # リポジトリからスクリーニング結果を取得
        result = await self._stock_repo.screen(
            filter_=domain_filter,
            limit=filter_input.limit,
            offset=filter_input.offset,
        )

        # 出力DTOに変換
        stock_outputs = [
            StockSummaryOutput(
                symbol=stock.symbol,
                name=stock.name,
                price=stock.price,
                change_percent=stock.change_percent,
                rs_rating=stock.rs_rating,
                canslim_score=stock.canslim_total_score,
                volume_ratio=0.0,  # サマリーには含まれない
                distance_from_52w_high=0.0,  # サマリーには含まれない
            )
            for stock in result.stocks
        ]

        return ScreenerResultOutput(
            total_count=result.total_count,
            stocks=stock_outputs,
            filter_applied=filter_input,
            screened_at=datetime.now(),
        )

    async def refresh_stock_data(
        self,
        symbols: list[str],
    ) -> int:
        """
        指定銘柄の株価・財務データを更新

        Args:
            symbols: 更新するシンボルのリスト

        Returns:
            int: 更新された銘柄数
        """
        # S&P500の履歴を取得（RS Rating計算用）
        sp500_bars = await self._financial_gateway.get_sp500_history(period="1y")
        sp500_prices = [bar.close for bar in sp500_bars]

        updated_count = 0

        for symbol in symbols:
            try:
                # 株価データ取得
                quote = await self._financial_gateway.get_quote(symbol)
                if quote is None:
                    continue

                # 財務データ取得
                financials = await self._financial_gateway.get_financial_metrics(symbol)

                # 株価履歴取得（RS Rating計算用）
                history = await self._financial_gateway.get_price_history(
                    symbol, period="1y"
                )
                stock_prices = [bar.close for bar in history]

                # RS Rating計算
                _, rs_rating = self._rs_calculator.calculate_from_prices(
                    stock_prices=stock_prices,
                    benchmark_prices=sp500_prices,
                )

                # CAN-SLIMスコア計算
                volume_ratio = (
                    quote.volume / quote.avg_volume if quote.avg_volume > 0 else 0
                )
                distance_from_high = (
                    ((quote.week_52_high - quote.price) / quote.week_52_high) * 100
                    if quote.week_52_high > 0
                    else 0
                )

                canslim_score = CANSLIMScore.calculate(
                    eps_growth_quarterly=(
                        financials.eps_growth_quarterly if financials else None
                    ),
                    eps_growth_annual=(
                        financials.eps_growth_annual if financials else None
                    ),
                    distance_from_52w_high=distance_from_high,
                    volume_ratio=volume_ratio,
                    rs_rating=rs_rating,
                    institutional_ownership=(
                        financials.institutional_ownership if financials else None
                    ),
                )

                # Stockエンティティを構築して保存
                from src.domain.entities.stock import Stock

                stock = Stock(
                    symbol=symbol,
                    name=symbol,  # 名前は別途取得が必要
                    price=quote.price,
                    change_percent=quote.change_percent,
                    volume=quote.volume,
                    avg_volume=quote.avg_volume,
                    market_cap=quote.market_cap,
                    pe_ratio=quote.pe_ratio,
                    week_52_high=quote.week_52_high,
                    week_52_low=quote.week_52_low,
                    eps_growth_quarterly=(
                        financials.eps_growth_quarterly if financials else None
                    ),
                    eps_growth_annual=(
                        financials.eps_growth_annual if financials else None
                    ),
                    rs_rating=rs_rating,
                    institutional_ownership=(
                        financials.institutional_ownership if financials else None
                    ),
                    canslim_score=canslim_score,
                    updated_at=datetime.now(),
                )

                await self._stock_repo.save(stock)
                updated_count += 1

            except Exception:
                # 個別銘柄のエラーは無視して続行
                continue

        return updated_count
