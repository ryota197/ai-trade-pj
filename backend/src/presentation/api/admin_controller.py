"""管理者API"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.application.dto.admin_dto import RefreshJobInput
from src.application.use_cases.admin.refresh_screener_data import (
    RefreshScreenerDataUseCase,
)
from src.presentation.dependencies import get_refresh_screener_use_case
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


@router.post(
    "/screener/refresh",
    response_model=ApiResponse[RefreshJobResponse],
    summary="スクリーニングデータ更新開始",
    description="指定した銘柄のスクリーニングデータを更新するジョブを開始する",
)
async def start_refresh(
    request: RefreshJobRequest,
    background_tasks: BackgroundTasks,
    use_case: RefreshScreenerDataUseCase = Depends(get_refresh_screener_use_case),
) -> ApiResponse[RefreshJobResponse]:
    """スクリーニングデータ更新を開始"""
    try:
        # 入力DTOを構築
        input_dto = RefreshJobInput(
            symbols=request.symbols,
            source=request.source,
        )

        # ジョブを開始
        result = await use_case.start_refresh(input_dto)

        # バックグラウンドタスクとして実行を登録
        background_tasks.add_task(
            use_case.execute_refresh,
            result.job_id,
            request.symbols,
        )

        # レスポンス
        response = RefreshJobResponse(
            job_id=result.job_id,
            status="started",
            total_symbols=result.total_symbols,
            started_at=result.started_at,
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start refresh job: {e}",
        )


@router.get(
    "/screener/refresh/{job_id}/status",
    response_model=ApiResponse[RefreshJobStatusResponse],
    summary="ジョブステータス取得",
    description="リフレッシュジョブの進捗状況を取得する",
)
async def get_job_status(
    job_id: str,
    use_case: RefreshScreenerDataUseCase = Depends(get_refresh_screener_use_case),
) -> ApiResponse[RefreshJobStatusResponse]:
    """ジョブステータスを取得"""
    try:
        result = await use_case.get_job_status(job_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}",
            )

        # スキーマに変換
        progress = RefreshJobProgressSchema(
            total=result.progress.total,
            processed=result.progress.processed,
            succeeded=result.progress.succeeded,
            failed=result.progress.failed,
            percentage=result.progress.percentage,
        )

        timing = RefreshJobTimingSchema(
            started_at=result.timing.started_at,
            elapsed_seconds=result.timing.elapsed_seconds,
            estimated_remaining_seconds=result.timing.estimated_remaining_seconds,
        )

        errors = [
            RefreshJobErrorSchema(symbol=err.symbol, error=err.error)
            for err in result.errors
        ]

        response = RefreshJobStatusResponse(
            job_id=result.job_id,
            status=result.status,
            progress=progress,
            timing=timing,
            errors=errors,
        )

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {e}",
        )


@router.delete(
    "/screener/refresh/{job_id}",
    response_model=ApiResponse[CancelJobResponse],
    summary="ジョブキャンセル",
    description="実行中のリフレッシュジョブをキャンセルする",
)
async def cancel_job(
    job_id: str,
    use_case: RefreshScreenerDataUseCase = Depends(get_refresh_screener_use_case),
) -> ApiResponse[CancelJobResponse]:
    """ジョブをキャンセル"""
    try:
        success = await use_case.cancel_job(job_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job: {job_id}. Job may not exist or is already completed.",
            )

        response = CancelJobResponse(message=f"Job {job_id} cancelled successfully")
        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {e}",
        )
