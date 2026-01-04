"""フロー・ジョブ実行リポジトリインターフェース"""

from abc import ABC, abstractmethod

from src.jobs.lib.models import FlowExecution, JobExecution


class FlowExecutionRepository(ABC):
    """フロー実行リポジトリ"""

    @abstractmethod
    def create(self, flow: FlowExecution) -> FlowExecution:
        """フローを作成"""
        pass

    @abstractmethod
    def get_by_id(self, flow_id: str) -> FlowExecution | None:
        """フローIDで取得"""
        pass

    @abstractmethod
    def update(self, flow: FlowExecution) -> FlowExecution:
        """フローを更新"""
        pass

    @abstractmethod
    def get_latest(self, limit: int = 10) -> list[FlowExecution]:
        """最新のフローを取得"""
        pass


class JobExecutionRepository(ABC):
    """ジョブ実行リポジトリ"""

    @abstractmethod
    def create(self, job: JobExecution) -> JobExecution:
        """ジョブを作成"""
        pass

    @abstractmethod
    def get(self, flow_id: str, job_name: str) -> JobExecution | None:
        """複合主キーでジョブを取得"""
        pass

    @abstractmethod
    def get_by_flow_id(self, flow_id: str) -> list[JobExecution]:
        """フローIDで全ジョブを取得"""
        pass

    @abstractmethod
    def update(self, job: JobExecution) -> JobExecution:
        """ジョブを更新（flow_id, job_name で識別）"""
        pass
