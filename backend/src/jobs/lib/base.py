"""ジョブ基底クラス"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class JobResult:
    """ジョブ実行結果"""

    success: bool
    message: str
    data: dict | None = None


class Job(ABC, Generic[TInput, TOutput]):
    """
    ジョブ基底クラス

    すべてのジョブはこのクラスを継承する。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """ジョブ識別名"""
        pass

    @abstractmethod
    async def execute(self, input_: TInput) -> TOutput:
        """
        ジョブ実行（サブクラスで実装）

        Args:
            input_: ジョブ入力

        Returns:
            TOutput: ジョブ出力
        """
        pass
