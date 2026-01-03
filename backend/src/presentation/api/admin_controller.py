"""管理者API"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.application.use_cases.admin.refresh_screener_data import (
    RefreshScreenerDataUseCase,
)
from src.jobs.flows.refresh_screener import RefreshScreenerFlow, RefreshScreenerInput
from src.presentation.dependencies import (
    get_refresh_screener_flow,
    get_refresh_screener_use_case,
)
from src.presentation.schemas.admin import (
    CancelJobResponse,
    RefreshJobErrorSchema,
    RefreshJobProgressSchema,
    RefreshJobRequest,
    RefreshJobResponse,
    RefreshJobStatusResponse,
    RefreshJobTimingSchema,
)
from src.presentation.schemas.common import ApiResponse

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


async def _run_refresh_flow(
    flow: RefreshScreenerFlow,
    input_: RefreshScreenerInput,
) -> None:
    """
    バックグラウンドでフローを実行

    Note:
        FastAPI BackgroundTasksで実行される。
        エラーはログに出力する。
    """
    try:
        result = await flow.run(input_)
        logger.info(
            f"Refresh flow completed: job_id={result.job_id}, "
            f"duration={result.duration_seconds:.1f}s, "
            f"steps={len(result.steps)}"
        )
        for step in result.steps:
            logger.info(f"  - {step.job_name}: {step.message}")
    except Exception as e:
        logger.error(f"Refresh flow failed: {e}", exc_info=True)


@router.post(
    "/screener/refresh",
    response_model=ApiResponse[RefreshJobResponse],
    summary="スクリーニングデータ更新開始",
    description="指定した銘柄のスクリーニングデータを更新するジョブを開始する",
)
async def start_refresh(
    request: RefreshJobRequest,
    background_tasks: BackgroundTasks,
    flow: RefreshScreenerFlow = Depends(get_refresh_screener_flow),
) -> ApiResponse[RefreshJobResponse]:
    """
    スクリーニングデータ更新を開始

    フローをバックグラウンドで実行し、即座にレスポンスを返す。
    """
    try:
        # 入力を構築
        input_ = RefreshScreenerInput(
            source=request.source,
            symbols=request.symbols,
        )

        # シンボル数を取得（レスポンス用）
        if request.symbols:
            total_symbols = len(request.symbols)
        else:
            symbols = await flow.symbol_provider.get_symbols(request.source)
            total_symbols = len(symbols)

        # バックグラウンドタスクとして実行を登録
        background_tasks.add_task(_run_refresh_flow, flow, input_)

        # レスポンス
        response = RefreshJobResponse(
            job_id="pending",  # フローはバックグラウンドで実行されるため仮ID
            status="started",
            total_symbols=total_symbols,
            started_at=None,
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        logger.error(f"Failed to start refresh: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start refresh job: {e}",
        )


@router.get(
    "/screener/refresh/{job_id}/status",
    response_model=ApiResponse[RefreshJobStatusResponse],
    summary="ジョブステータス取得",
    description="指定したジョブの進捗状況を取得する",
)
async def get_job_status(
    job_id: str,
    use_case: RefreshScreenerDataUseCase = Depends(get_refresh_screener_use_case),
) -> ApiResponse[RefreshJobStatusResponse]:
    """
    ジョブの進捗状況を取得

    Args:
        job_id: ジョブID

    Returns:
        ジョブの進捗状況
    """
    try:
        status = await use_case.get_job_status(job_id)
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}",
            )

        # DTOからスキーマに変換
        response = RefreshJobStatusResponse(
            job_id=status.job_id,
            status=status.status,
            progress=RefreshJobProgressSchema(
                total=status.progress.total,
                processed=status.progress.processed,
                succeeded=status.progress.succeeded,
                failed=status.progress.failed,
                percentage=status.progress.percentage,
            ),
            timing=RefreshJobTimingSchema(
                started_at=status.timing.started_at,
                elapsed_seconds=status.timing.elapsed_seconds,
                estimated_remaining_seconds=status.timing.estimated_remaining_seconds,
            ),
            errors=[
                RefreshJobErrorSchema(symbol=e.symbol, error=e.error)
                for e in status.errors
            ],
        )

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {e}",
        )


@router.delete(
    "/screener/refresh/{job_id}",
    response_model=ApiResponse[CancelJobResponse],
    summary="ジョブキャンセル",
    description="実行中または保留中のジョブをキャンセルする",
)
async def cancel_job(
    job_id: str,
    use_case: RefreshScreenerDataUseCase = Depends(get_refresh_screener_use_case),
) -> ApiResponse[CancelJobResponse]:
    """
    ジョブをキャンセル

    Args:
        job_id: ジョブID

    Returns:
        キャンセル結果
    """
    try:
        cancelled = await use_case.cancel_job(job_id)

        if not cancelled:
            raise HTTPException(
                status_code=400,
                detail=f"Job cannot be cancelled: {job_id} (not found or already completed)",
            )

        response = CancelJobResponse(
            message=f"Job {job_id} has been cancelled",
        )

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {e}",
        )
