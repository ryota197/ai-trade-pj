"""スクリーニングデータ更新 ユースケース"""

from datetime import date, datetime, timezone
from decimal import Decimal

from src.application.dto.admin_dto import (
    RefreshJobError,
    RefreshJobInput,
    RefreshJobOutput,
    RefreshJobProgress,
    RefreshJobStatusOutput,
    RefreshJobTiming,
)
from src.application.interfaces.financial_data_gateway import FinancialDataGateway
from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository
from src.domain.services.rs_calculator import PriceBar, RSCalculator
from src.infrastructure.repositories.postgres_refresh_job_repository import (
    RefreshJob,
    RefreshJobRepository,
)


class RefreshScreenerDataUseCase:
    """
    スクリーニングデータ更新 ユースケース

    指定された銘柄リストのスクリーニングデータを更新する。
    ジョブとして管理し、進捗を追跡可能にする。
    """

    def __init__(
        self,
        job_repository: RefreshJobRepository,
        stock_repository: CANSLIMStockRepository,
        financial_gateway: FinancialDataGateway,
        rs_calculator: RSCalculator | None = None,
    ) -> None:
        self._job_repo = job_repository
        self._stock_repo = stock_repository
        self._financial_gateway = financial_gateway
        self._rs_calculator = rs_calculator or RSCalculator()

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

    async def execute_refresh(
        self,
        job_id: str,
        symbols: list[str],
        target_date: date | None = None,
    ) -> None:
        """
        データ更新を実行（バックグラウンドタスク用）

        Args:
            job_id: ジョブID
            symbols: 更新する銘柄リスト
            target_date: 対象日（デフォルトは今日）
        """
        if target_date is None:
            target_date = date.today()

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

        # S&P500の履歴を取得（RS計算用）
        benchmark_bars: list[PriceBar] = []
        try:
            sp500_history = await self._financial_gateway.get_sp500_history(period="1y")
            benchmark_bars = [PriceBar(close=bar.close) for bar in sp500_history]
        except Exception:
            pass

        errors: list[dict] = []
        succeeded = 0
        failed = 0

        for i, symbol in enumerate(symbols):
            try:
                await self._process_single_symbol(symbol, target_date, benchmark_bars)
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

        job = RefreshJob(
            job_id=job.job_id,
            status="completed",
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
        self,
        symbol: str,
        target_date: date,
        benchmark_bars: list[PriceBar],
    ) -> None:
        """単一銘柄のデータを処理（Job 1: 価格データ取得）"""
        # 株価データ取得
        quote = await self._financial_gateway.get_quote(symbol)
        if quote is None:
            raise ValueError(f"Quote not found for {symbol}")

        # 財務データ取得
        financials = await self._financial_gateway.get_financial_metrics(symbol)

        # 株価履歴取得（RS計算用）
        stock_bars: list[PriceBar] = []
        try:
            history = await self._financial_gateway.get_price_history(
                symbol, period="1y"
            )
            stock_bars = [PriceBar(close=bar.close) for bar in history]
        except Exception:
            pass

        # 相対強度を計算
        relative_strength: Decimal | None = None
        if stock_bars and benchmark_bars:
            relative_strength = self._rs_calculator.calculate(stock_bars, benchmark_bars)

        # CANSLIMStockを構築して保存
        stock = CANSLIMStock(
            symbol=symbol.upper(),
            date=target_date,
            name=symbol,  # TODO: 名前取得
            industry=None,
            price=Decimal(str(quote.price)),
            change_percent=Decimal(str(quote.change_percent)),
            volume=quote.volume,
            avg_volume_50d=quote.avg_volume,
            market_cap=quote.market_cap,
            week_52_high=Decimal(str(quote.week_52_high)) if quote.week_52_high else None,
            week_52_low=Decimal(str(quote.week_52_low)) if quote.week_52_low else None,
            eps_growth_quarterly=(
                Decimal(str(financials.eps_growth_quarterly))
                if financials and financials.eps_growth_quarterly
                else None
            ),
            eps_growth_annual=(
                Decimal(str(financials.eps_growth_annual))
                if financials and financials.eps_growth_annual
                else None
            ),
            institutional_ownership=(
                Decimal(str(financials.institutional_ownership))
                if financials and financials.institutional_ownership
                else None
            ),
            relative_strength=relative_strength,
            # RS Rating と CAN-SLIM スコアは Job 2, Job 3 で計算
            rs_rating=None,
            canslim_score=None,
            updated_at=datetime.now(timezone.utc),
        )

        self._stock_repo.save(stock)

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
            estimated_remaining_seconds=(
                round(estimated_remaining, 1) if estimated_remaining else None
            ),
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
