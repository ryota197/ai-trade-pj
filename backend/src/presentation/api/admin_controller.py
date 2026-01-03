"""管理者API"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.jobs.flows.refresh_screener import RefreshScreenerFlow, RefreshScreenerInput
from src.presentation.dependencies import get_refresh_screener_flow
from src.presentation.schemas.admin import (
    RefreshJobRequest,
    RefreshJobResponse,
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
