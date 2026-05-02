"""任务调度模块 - 任务拆解、调度、执行监控、重试"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict, List, Callable

from .decision import Decision
from .exception_handler import with_exception_handling
from .perception import PerceivedMessage
from storage.log_manager import get_logger


logger = get_logger("TaskScheduler")


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskResult:
    """任务结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """任务"""
    task_id: str
    name: str
    tool_name: str
    status: TaskStatus = TaskStatus.PENDING
    input_data: Any = None
    result: Optional[TaskResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class TaskChain:
    """任务链（一系列按顺序执行的任务）"""
    chain_id: str
    tasks: List[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    perceived_message: Optional[PerceivedMessage] = None
    decision: Optional[Decision] = None
    created_at: datetime = field(default_factory=datetime.now)
    current_task_index: int = 0
    shared_data: Dict[str, Any] = field(default_factory=dict)


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        """初始化任务调度器"""
        self.task_chains: Dict[str, TaskChain] = {}
        self.tool_handlers: Dict[str, Callable] = {}

    def register_tool(self, tool_name: str, handler: Callable):
        """注册工具处理器

        Args:
            tool_name: 工具名称
            handler: 处理器函数（异步）
        """
        self.tool_handlers[tool_name] = handler
        logger.info(f"注册工具处理器: {tool_name}")

    def build_task_chain(
        self,
        message: PerceivedMessage,
        decision: Decision,
    ) -> TaskChain:
        """构建任务链

        Args:
            message: 感知到的消息
            decision: 决策结果

        Returns:
            任务链
        """
        import uuid

        chain_id = f"chain_{uuid.uuid4().hex[:8]}"
        chain = TaskChain(
            chain_id=chain_id,
            perceived_message=message,
            decision=decision,
        )

        # 构建任务列表
        for index, tool_name in enumerate(decision.tool_sequence):
            task = Task(
                task_id=f"{chain_id}_task_{index}",
                name=f"{tool_name}_task",
                tool_name=tool_name,
            )
            chain.tasks.append(task)

        # 初始数据
        chain.shared_data["raw_message"] = message
        chain.shared_data["intent"] = decision.intent

        logger.info(f"构建任务链: {chain_id}, 包含{len(chain.tasks)}个任务")
        return chain

    async def execute_task_chain(self, chain: TaskChain) -> TaskResult:
        """执行任务链

        Args:
            chain: 任务链

        Returns:
            最终结果
        """
        chain.status = TaskStatus.RUNNING
        self.task_chains[chain.chain_id] = chain

        logger.info(f"开始执行任务链: {chain.chain_id}")

        final_result = TaskResult(success=False, error="未执行任何任务")

        try:
            # 逐个执行任务
            for i in range(chain.current_task_index, len(chain.tasks)):
                task = chain.tasks[i]
                chain.current_task_index = i

                # 执行单个任务
                result = await self._execute_task(task, chain)

                if not result.success:
                    task.status = TaskStatus.FAILED
                    task.result = result
                    chain.status = TaskStatus.FAILED
                    final_result = result
                    logger.error(f"任务链执行失败: {chain.chain_id} at task {i}")
                    break

                task.status = TaskStatus.COMPLETED
                task.result = result

            else:
                # 所有任务完成
                chain.status = TaskStatus.COMPLETED
                final_result = TaskResult(
                    success=True,
                    data=chain.shared_data,
                )
                logger.info(f"任务链执行成功: {chain.chain_id}")

        except Exception as e:
            chain.status = TaskStatus.FAILED
            final_result = TaskResult(
                success=False,
                error=f"任务链执行异常: {str(e)}",
            )
            logger.error(f"任务链执行异常: {chain.chain_id}", exc_info=True)

        finally:
            chain.completed_at = datetime.now()

        return final_result

    @with_exception_handling(max_retries=3, module="TaskScheduler")
    async def _execute_task(self, task: Task, chain: TaskChain) -> TaskResult:
        """执行单个任务

        Args:
            task: 任务
            chain: 任务链

        Returns:
            任务结果
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        logger.info(f"执行任务: {task.task_id} ({task.tool_name})")

        try:
            # 获取工具处理器
            handler = self.tool_handlers.get(task.tool_name)
            if not handler:
                return TaskResult(
                    success=False,
                    error=f"未找到工具处理器: {task.tool_name}",
                )

            # 执行任务
            if asyncio.iscoroutinefunction(handler):
                result = await handler(task, chain)
            else:
                result = handler(task, chain)

            # 确保结果是TaskResult类型
            if not isinstance(result, TaskResult):
                if isinstance(result, tuple) and len(result) == 2:
                    # 兼容 (success, data) 格式
                    success, data = result
                    result = TaskResult(success=success, data=data)
                else:
                    # 其他情况假设成功
                    result = TaskResult(success=True, data=result)

            task.result = result
            task.completed_at = datetime.now()

            logger.info(f"任务完成: {task.task_id}, success={result.success}")

            return result

        except Exception as e:
            task.retry_count += 1
            logger.error(f"任务执行失败: {task.task_id} - {e}", exc_info=True)
            return TaskResult(
                success=False,
                error=str(e),
            )

    def get_task_chain(self, chain_id: str) -> Optional[TaskChain]:
        """获取任务链

        Args:
            chain_id: 任务链ID

        Returns:
            任务链对象
        """
        return self.task_chains.get(chain_id)

    def cancel_task_chain(self, chain_id: str) -> bool:
        """取消任务链

        Args:
            chain_id: 任务链ID

        Returns:
            是否成功
        """
        chain = self.task_chains.get(chain_id)
        if chain and chain.status == TaskStatus.RUNNING:
            chain.status = TaskStatus.CANCELLED
            logger.warning(f"取消任务链: {chain_id}")
            return True
        return False


# 全局任务调度器实例
_task_scheduler: Optional[TaskScheduler] = None


def init_task_scheduler() -> TaskScheduler:
    """初始化任务调度器"""
    global _task_scheduler
    _task_scheduler = TaskScheduler()
    return _task_scheduler


def get_task_scheduler() -> TaskScheduler:
    """获取任务调度器实例"""
    if _task_scheduler is None:
        raise RuntimeError("任务调度器未初始化，请先调用 init_task_scheduler()")
    return _task_scheduler
