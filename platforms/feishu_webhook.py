"""
飞书 Webhook 服务器 - 使用 lark-oapi SDK
用于接收飞书的事件回调
"""

from typing import Optional, Dict, Any, Callable

from aiohttp import web
from aiohttp.web import Request

from lark_oapi import EventDispatcherHandler, RawRequest, RawResponse
from storage.log_manager import get_logger

logger = get_logger("FeishuWebhook")


class FeishuWebhookServer:
    """
    飞书 Webhook 服务器
    """

    def __init__(
        self,
        verification_token: str = "",
        encrypt_key: str = "",
        message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.verification_token = verification_token
        self.encrypt_key = encrypt_key
        self.message_callback = message_callback
        self.app = web.Application()
        self._runner: Optional[web.AppRunner] = None
        self._setup_event_handlers()
        self._setup_routes()

    def _setup_event_handlers(self):
        """设置事件处理器"""
        # 创建事件分发器
        self._event_handler = EventDispatcherHandler.builder(
            self.encrypt_key,
            self.verification_token,
        ).build()

        # 注册消息接收事件
        def handle_message(ctx, data):
            logger.info(f"Received message event: {data}")
            if self.message_callback:
                # 将数据转换为字典格式
                event_dict = self._event_to_dict(data)
                self.message_callback(event_dict)

        self._event_handler.register_p2_im_message_receive_v1(handle_message)

        # 注册自定义事件处理器作为备用
        def handle_custom(ctx, data):
            logger.debug(f"Received custom event: {data}")
            if self.message_callback:
                event_dict = self._event_to_dict(data)
                self.message_callback(event_dict)

        self._event_handler.register_p2_customized_event(handle_custom)
        self._event_handler.register_p1_customized_event(handle_custom)

    def _event_to_dict(self, event: Any) -> Dict[str, Any]:
        """将事件对象转换为字典"""
        if hasattr(event, '__dict__'):
            return event.__dict__
        elif hasattr(event, 'dict'):
            return event.dict()
        elif isinstance(event, dict):
            return event
        else:
            return {'data': str(event)}

    def _setup_routes(self):
        """设置路由"""
        self.app.router.add_post("/feishu/webhook", self._handle_webhook)
        self.app.router.add_get("/health", self._handle_health_check)

    async def _handle_health_check(self, request: Request):
        """健康检查端点"""
        return web.json_response({"status": "ok"})

    async def _handle_webhook(self, request: Request):
        """处理 Webhook 请求"""
        try:
            body_bytes = await request.read()
            
            # 构建 RawRequest
            raw_request = RawRequest()
            raw_request.body = body_bytes
            
            # 使用事件分发器处理请求
            raw_response = self._event_handler.do(raw_request)
            
            # 构建响应
            resp = web.Response(
                body=raw_response.body,
                status=200,
                content_type='application/json'
            )
            
            return resp

        except Exception as e:
            logger.error(f"Webhook 处理异常: {e}", exc_info=True)
            return web.json_response(
                {"code": 500, "msg": "内部错误"}, 
                status=500
            )

    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """启动 Webhook 服务器"""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, host, port)
        await site.start()
        logger.info(f"飞书 Webhook 服务器已启动: http://{host}:{port}/feishu/webhook")
        logger.info(f"健康检查: http://{host}:{port}/health")

    async def stop(self):
        """停止 Webhook 服务器"""
        if self._runner:
            await self._runner.cleanup()
            logger.info("飞书 Webhook 服务器已停止")


def create_webhook_server(
    verification_token: str = "",
    encrypt_key: str = "",
    message_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> FeishuWebhookServer:
    """创建 Webhook 服务器工厂函数"""
    return FeishuWebhookServer(
        verification_token=verification_token,
        encrypt_key=encrypt_key,
        message_callback=message_callback,
    )
