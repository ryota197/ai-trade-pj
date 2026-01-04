"""管理者API"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.postgres_flow_execution_repository import (
    PostgresFlowExecutionRepository,
)
from src.infrastructure.repositories.postgres_job_execution_repository import (
    PostgresJobExecutionRepository,
)
from src.jobs.flows.refresh_screener import RefreshScreenerFlow, RefreshScreenerInput
from src.jobs.lib import FlowExecutionRepository, JobExecutionRepository
from src.presentation.dependencies import get_refresh_screener_flow
from src.presentation.schemas.admin import (
    CancelJobResponse,
    FlowStatusResponse,
    JobExecutionSchema,
    RefreshJobRequest,
    RefreshJobResponse,
)
from src.presentation.schemas.common import ApiResponse

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


def get_flow_repository(db: Session = Depends(get_db)) -> FlowExecutionRepository:
    """FlowExecutionRepository の依存性解決"""
    return PostgresFlowExecutionRepository(db)


def get_job_repository(db: Session = Depends(get_db)) -> JobExecutionRepository:
    """JobExecutionRepository の依存性解決"""
    return PostgresJobExecutionRepository(db)


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
            f"Refresh flow completed: flow_id={result.flow_id}, "
            f"duration={result.duration_seconds:.1f}s"
        )
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
    進捗は GET /screener/refresh/{flow_id}/status で取得可能。
    """
    try:
        # 入力を構築
        input_ = RefreshScreenerInput(
            source=request.source,
            symbols=request.symbols,
        )

        # バックグラウンドタスクとして実行を登録
        background_tasks.add_task(_run_refresh_flow, flow, input_)

        # レスポンス（flow_id はバックグラウンドで生成されるため "pending"）
        response = RefreshJobResponse(
            flow_id="pending",
            status="started",
            message="Refresh flow started in background. Check latest flow status.",
        )

        return ApiResponse(success=True, data=response)

    except Exception as e:
        logger.error(f"Failed to start refresh: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start refresh job: {e}",
        )


@router.get(
    "/screener/refresh/{flow_id}/status",
    response_model=ApiResponse[FlowStatusResponse],
    summary="フローステータス取得",
    description="指定したフローの進捗状況を取得する",
)
async def get_flow_status(
    flow_id: str,
    flow_repo: FlowExecutionRepository = Depends(get_flow_repository),
    job_repo: JobExecutionRepository = Depends(get_job_repository),
) -> ApiResponse[FlowStatusResponse]:
    """
    フローの進捗状況を取得

    Args:
        flow_id: フローID

    Returns:
        フローの進捗状況と各ジョブの状態
    """
    try:
        flow = flow_repo.get_by_id(flow_id)
        if flow is None:
            raise HTTPException(
                status_code=404,
                detail=f"Flow not found: {flow_id}",
            )

        # ジョブ一覧を取得
        jobs = job_repo.get_by_flow_id(flow_id)

        response = FlowStatusResponse(
            flow_id=flow.flow_id,
            flow_name=flow.flow_name,
            status=flow.status.value,
            total_jobs=flow.total_jobs,
            completed_jobs=flow.completed_jobs,
            current_job=flow.current_job,
            started_at=flow.started_at,
            completed_at=flow.completed_at,
            jobs=[
                JobExecutionSchema(
                    job_name=job.job_name,
                    status=job.status.value,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    error_message=job.error_message,
                )
                for job in jobs
            ],
        )

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get flow status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get flow status: {e}",
        )


@router.get(
    "/screener/refresh/latest",
    response_model=ApiResponse[list[FlowStatusResponse]],
    summary="最新フロー一覧取得",
    description="最新のフロー実行一覧を取得する",
)
async def get_latest_flows(
    limit: int = 10,
    flow_repo: FlowExecutionRepository = Depends(get_flow_repository),
    job_repo: JobExecutionRepository = Depends(get_job_repository),
) -> ApiResponse[list[FlowStatusResponse]]:
    """
    最新のフロー実行一覧を取得

    Args:
        limit: 取得件数（デフォルト10件）

    Returns:
        フロー実行一覧
    """
    try:
        flows = flow_repo.get_latest(limit=limit)

        responses = []
        for flow in flows:
            jobs = job_repo.get_by_flow_id(flow.flow_id)
            responses.append(
                FlowStatusResponse(
                    flow_id=flow.flow_id,
                    flow_name=flow.flow_name,
                    status=flow.status.value,
                    total_jobs=flow.total_jobs,
                    completed_jobs=flow.completed_jobs,
                    current_job=flow.current_job,
                    started_at=flow.started_at,
                    completed_at=flow.completed_at,
                    jobs=[
                        JobExecutionSchema(
                            job_name=job.job_name,
                            status=job.status.value,
                            started_at=job.started_at,
                            completed_at=job.completed_at,
                            error_message=job.error_message,
                        )
                        for job in jobs
                    ],
                )
            )

        return ApiResponse(success=True, data=responses)

    except Exception as e:
        logger.error(f"Failed to get latest flows: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get latest flows: {e}",
        )


@router.delete(
    "/screener/refresh/{flow_id}",
    response_model=ApiResponse[CancelJobResponse],
    summary="フローキャンセル",
    description="実行中または保留中のフローをキャンセルする（未実装）",
)
async def cancel_flow(
    flow_id: str,
) -> ApiResponse[CancelJobResponse]:
    """
    フローをキャンセル

    Note:
        現在は未実装。バックグラウンドタスクのキャンセルは複雑なため、
        Phase 2 以降で実装予定。
    """
    raise HTTPException(
        status_code=501,
        detail="Flow cancellation is not implemented yet",
    )
