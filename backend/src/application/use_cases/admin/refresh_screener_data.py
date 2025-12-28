"""スクリーニングデータ更新 ユースケース"""

import json
from datetime import datetime, timezone

from src.application.dto.admin_dto import (
    RefreshJobError,
    RefreshJobInput,
    RefreshJobOutput,
    RefreshJobProgress,
    RefreshJobStatusOutput,
    RefreshJobTiming,
)
from src.application.interfaces.financial_data_gateway import FinancialDataGateway
from src.domain.entities.stock import Stock
from src.domain.repositories.refresh_job_repository import RefreshJob, RefreshJobRepository
from src.domain.repositories.stock_repository import StockRepository
from src.domain.services.rs_rating_calculator import RSRatingCalculator
from src.domain.value_objects.canslim_score import CANSLIMScore


class RefreshScreenerDataUseCase:
    """
    スクリーニングデータ更新 ユースケース

    指定された銘柄リストのスクリーニングデータを更新する。
    ジョブとして管理し、進捗を追跡可能にする。
    """

    def __init__(
        self,
        job_repository: RefreshJobRepository,
        stock_repository: StockRepository,
        financial_gateway: FinancialDataGateway,
        rs_calculator: RSRatingCalculator,
    ) -> None:
        self._job_repo = job_repository
        self._stock_repo = stock_repository
        self._financial_gateway = financial_gateway
        self._rs_calculator = rs_calculator

    async def start_refresh(self, input_: RefreshJobInput) -> RefreshJobOutput:
        """
        データ更新ジョブを開始

        Args:
            input_: ジョブ入力（銘柄リスト、ソース）

        Returns:
            RefreshJobOutput: 作成されたジョブ情報
        """
        # ジョブID生成
        now = datetime.now(timezone.utc)
        job_id = f"refresh_{now.strftime('%Y%m%d_%H%M%S')}"

        # ジョブを作成
        job = RefreshJob(
            job_id=job_id,
            status="pending",
            source=input_.source,
            total_symbols=len(input_.symbols),
            processed_count=0,
            succeeded_count=0,
            failed_count=0,
            errors=None,
            started_at=None,
            completed_at=None,
            created_at=now,
        )
        await self._job_repo.create(job)

        return RefreshJobOutput(
            job_id=job_id,
            status="pending",
            total_symbols=len(input_.symbols),
            started_at=None,
        )

    async def execute_refresh(self, job_id: str, symbols: list[str]) -> None:
        """
        データ更新を実行（バックグラウンドタスク用）

        Args:
            job_id: ジョブID
            symbols: 更新する銘柄リスト
        """
        # ジョブを取得して実行中に更新
        job = await self._job_repo.get_by_id(job_id)
        if job is None:
            return

        now = datetime.now(timezone.utc)
        job = RefreshJob(
            job_id=job.job_id,
            status="running",
            source=job.source,
            total_symbols=job.total_symbols,
            processed_count=0,
            succeeded_count=0,
            failed_count=0,
            errors=[],
            started_at=now,
            completed_at=None,
            created_at=job.created_at,
        )
        await self._job_repo.update(job)

        # S&P500の履歴を取得（RS Rating計算用）
        try:
            sp500_bars = await self._financial_gateway.get_sp500_history(period="1y")
            sp500_prices = [bar.close for bar in sp500_bars]
        except Exception:
            sp500_prices = []

        errors: list[dict] = []
        succeeded = 0
        failed = 0

        for i, symbol in enumerate(symbols):
            try:
                await self._process_single_symbol(symbol, sp500_prices)
                succeeded += 1
            except Exception as e:
                failed += 1
                errors.append({"symbol": symbol, "error": str(e)})

            # 進捗を更新（10銘柄ごと、または最後）
            if (i + 1) % 10 == 0 or i == len(symbols) - 1:
                job = RefreshJob(
                    job_id=job.job_id,
                    status="running",
                    source=job.source,
                    total_symbols=job.total_symbols,
                    processed_count=i + 1,
                    succeeded_count=succeeded,
                    failed_count=failed,
                    errors=errors if errors else None,
                    started_at=job.started_at,
                    completed_at=None,
                    created_at=job.created_at,
                )
                await self._job_repo.update(job)

        # 完了
        completed_at = datetime.now(timezone.utc)
        final_status = "completed" if failed == 0 else "completed"  # エラーがあっても完了扱い

        job = RefreshJob(
            job_id=job.job_id,
            status=final_status,
            source=job.source,
            total_symbols=job.total_symbols,
            processed_count=len(symbols),
            succeeded_count=succeeded,
            failed_count=failed,
            errors=errors if errors else None,
            started_at=job.started_at,
            completed_at=completed_at,
            created_at=job.created_at,
        )
        await self._job_repo.update(job)

    async def _process_single_symbol(
        self, symbol: str, sp500_prices: list[float]
    ) -> None:
        """単一銘柄のデータを処理"""
        # 株価データ取得
        quote = await self._financial_gateway.get_quote(symbol)
        if quote is None:
            raise ValueError(f"Quote not found for {symbol}")

        # 財務データ取得
        financials = await self._financial_gateway.get_financial_metrics(symbol)

        # 株価履歴取得（RS Rating計算用）
        history = await self._financial_gateway.get_price_history(symbol, period="1y")
        stock_prices = [bar.close for bar in history]

        # RS Rating計算
        rs_rating = 50  # デフォルト
        if sp500_prices and stock_prices:
            rs_result = self._rs_calculator.calculate_single(
                symbol=symbol,
                stock_prices=stock_prices,
                benchmark_prices=sp500_prices,
            )
            if rs_result:
                rs_rating = rs_result.rs_rating

        # CAN-SLIMスコア計算
        volume_ratio = quote.volume / quote.avg_volume if quote.avg_volume > 0 else 0
        distance_from_high = (
            ((quote.week_52_high - quote.price) / quote.week_52_high) * 100
            if quote.week_52_high > 0
            else 0
        )

        canslim_score = CANSLIMScore.calculate(
            eps_growth_quarterly=financials.eps_growth_quarterly if financials else None,
            eps_growth_annual=financials.eps_growth_annual if financials else None,
            distance_from_52w_high=distance_from_high,
            volume_ratio=volume_ratio,
            rs_rating=rs_rating,
            institutional_ownership=financials.institutional_ownership if financials else None,
        )

        # Stockエンティティを構築して保存
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
            eps_growth_quarterly=financials.eps_growth_quarterly if financials else None,
            eps_growth_annual=financials.eps_growth_annual if financials else None,
            rs_rating=rs_rating,
            institutional_ownership=financials.institutional_ownership if financials else None,
            canslim_score=canslim_score,
            updated_at=datetime.now(timezone.utc),
        )

        await self._stock_repo.save(stock)

    async def get_job_status(self, job_id: str) -> RefreshJobStatusOutput | None:
        """
        ジョブステータスを取得

        Args:
            job_id: ジョブID

        Returns:
            RefreshJobStatusOutput: ジョブステータス
        """
        job = await self._job_repo.get_by_id(job_id)
        if job is None:
            return None

        # 経過時間を計算
        now = datetime.now(timezone.utc)
        elapsed_seconds = 0.0
        estimated_remaining = None

        if job.started_at:
            # started_atがnaiveな場合はUTCとして扱う
            started = job.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            elapsed_seconds = (now - started).total_seconds()

            # 残り時間を推定
            if job.processed_count > 0 and job.total_symbols > job.processed_count:
                avg_time_per_symbol = elapsed_seconds / job.processed_count
                remaining_symbols = job.total_symbols - job.processed_count
                estimated_remaining = avg_time_per_symbol * remaining_symbols

        # 進捗
        percentage = 0.0
        if job.total_symbols > 0:
            percentage = (job.processed_count / job.total_symbols) * 100

        progress = RefreshJobProgress(
            total=job.total_symbols,
            processed=job.processed_count,
            succeeded=job.succeeded_count,
            failed=job.failed_count,
            percentage=round(percentage, 1),
        )

        timing = RefreshJobTiming(
            started_at=job.started_at,
            elapsed_seconds=round(elapsed_seconds, 1),
            estimated_remaining_seconds=round(estimated_remaining, 1) if estimated_remaining else None,
        )

        errors = []
        if job.errors:
            for err in job.errors:
                errors.append(RefreshJobError(symbol=err["symbol"], error=err["error"]))

        return RefreshJobStatusOutput(
            job_id=job.job_id,
            status=job.status,
            progress=progress,
            timing=timing,
            errors=errors,
        )

    async def cancel_job(self, job_id: str) -> bool:
        """
        ジョブをキャンセル

        Args:
            job_id: ジョブID

        Returns:
            bool: キャンセル成功したか
        """
        job = await self._job_repo.get_by_id(job_id)
        if job is None:
            return False

        if job.status not in ("pending", "running"):
            return False

        job = RefreshJob(
            job_id=job.job_id,
            status="cancelled",
            source=job.source,
            total_symbols=job.total_symbols,
            processed_count=job.processed_count,
            succeeded_count=job.succeeded_count,
            failed_count=job.failed_count,
            errors=job.errors,
            started_at=job.started_at,
            completed_at=datetime.now(timezone.utc),
            created_at=job.created_at,
        )
        await self._job_repo.update(job)
        return True
