"""管理者API"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from src.adapters.database import get_db
from src.jobs.flows.refresh_screener import RefreshScreenerFlow
from src.queries import FlowExecutionQuery, JobExecutionQuery
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


def get_flow_query(db: Session = Depends(get_db)) -> FlowExecutionQuery:
    """FlowExecutionQuery の依存性解決"""
    return FlowExecutionQuery(db)


def get_job_query(db: Session = Depends(get_db)) -> JobExecutionQuery:
    """JobExecutionQuery の依存性解決"""
    return JobExecutionQuery(db)


async def _run_refresh_flow(flow: RefreshScreenerFlow) -> None:
    """バックグラウンドでフローを実行"""
    try:
        result = await flow.run()
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
    description="S&P 500銘柄のスクリーニングデータを更新するジョブを開始する",
)
async def start_refresh(
    _request: RefreshJobRequest,
    background_tasks: BackgroundTasks,
    flow: RefreshScreenerFlow = Depends(get_refresh_screener_flow),
) -> ApiResponse[RefreshJobResponse]:
    """スクリーニングデータ更新を開始"""
    try:
        background_tasks.add_task(_run_refresh_flow, flow)

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
)
async def get_flow_status(
    flow_id: str,
    flow_query: FlowExecutionQuery = Depends(get_flow_query),
    job_query: JobExecutionQuery = Depends(get_job_query),
) -> ApiResponse[FlowStatusResponse]:
    """フローの進捗状況を取得"""
    try:
        flow = flow_query.get_by_id(flow_id)
        if flow is None:
            raise HTTPException(status_code=404, detail=f"Flow not found: {flow_id}")

        jobs = job_query.get_by_flow_id(flow_id)

        response = FlowStatusResponse(
            flow_id=flow.flow_id,
            flow_name=flow.flow_name,
            status=flow.status,
            total_jobs=flow.total_jobs,
            completed_jobs=flow.completed_jobs,
            current_job=flow.current_job,
            started_at=flow.started_at,
            completed_at=flow.completed_at,
            jobs=[
                JobExecutionSchema(
                    job_name=job.job_name,
                    status=job.status,
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
        raise HTTPException(status_code=500, detail=f"Failed to get flow status: {e}")


@router.get(
    "/screener/refresh/latest",
    response_model=ApiResponse[list[FlowStatusResponse]],
    summary="最新フロー一覧取得",
)
async def get_latest_flows(
    limit: int = 10,
    flow_query: FlowExecutionQuery = Depends(get_flow_query),
    job_query: JobExecutionQuery = Depends(get_job_query),
) -> ApiResponse[list[FlowStatusResponse]]:
    """最新のフロー実行一覧を取得"""
    try:
        flows = flow_query.get_latest(limit=limit)

        responses = []
        for flow in flows:
            jobs = job_query.get_by_flow_id(flow.flow_id)
            responses.append(
                FlowStatusResponse(
                    flow_id=flow.flow_id,
                    flow_name=flow.flow_name,
                    status=flow.status,
                    total_jobs=flow.total_jobs,
                    completed_jobs=flow.completed_jobs,
                    current_job=flow.current_job,
                    started_at=flow.started_at,
                    completed_at=flow.completed_at,
                    jobs=[
                        JobExecutionSchema(
                            job_name=job.job_name,
                            status=job.status,
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
        raise HTTPException(status_code=500, detail=f"Failed to get latest flows: {e}")


@router.delete(
    "/screener/refresh/{flow_id}",
    response_model=ApiResponse[CancelJobResponse],
    summary="フローキャンセル",
)
async def cancel_flow(_flow_id: str) -> ApiResponse[CancelJobResponse]:
    """フローをキャンセル（未実装）"""
    raise HTTPException(
        status_code=501,
        detail="Flow cancellation is not implemented yet",
    )
