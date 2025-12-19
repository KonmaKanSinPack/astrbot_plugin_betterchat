from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.provider import ProviderRequest
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionController,
)

@register("astrbot_plugin_betterchat", "兔子", "更好的聊天。", "v0.1.0")
class BetterChat_Plugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.is_listening = False

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    # @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    # async def on_all_message(self, event: AstrMessageEvent):
    #     if self.is_listening:
    #         logger.info("插件处于监听状态，忽略消息。")
    #         return
        
    #     self.is_listening = True
    #     yield event.plain_result(f"收到消息: {event.message_str}")
    #     # logger.info(f"event: {event}, request: {req}")
    #     hole_msgs = ""
    #     try:
    #         @session_waiter(timeout=4, record_history_chains=False)
    #         async def wait_for_response(controller: SessionController, event: AstrMessageEvent):
    #             nonlocal hole_msgs
    #             cur_msg = event.message_str
    #             hole_msgs += f"{cur_msg}\n"
                
    #             controller.keep(timeout=4, reset_timeout=True)

    #         try:
    #             await wait_for_response(event)
    #         except TimeoutError:
    #             logger.info("No more messages received within timeout.")
    #             logger.info(f"Collected messages:\n{hole_msgs}")
    #             event.message_str = hole_msgs
    #             hole_msgs = ""
    #             yield event.plain_result(f"send msg")
    #         except Exception as e:
    #             yield event.plain_result("发生内部错误，请联系管理员: " + str(e))
    #         finally:
    #             self.is_listening = False
    #             event.stop_event()
    #     except Exception as e:
    #         yield event.plain_result("发生错误，请联系管理员: " + str(e))

    @filter.on_llm_request()
    async def my_hook(self, event: AstrMessageEvent, req: ProviderRequest):
        if self.is_listening:
            logger.info("插件处于监听状态，忽略消息。")
            return
        logger.info(f"收到消息: {event.message_str}")
        hole_msgs = ""
        try:
            @session_waiter(timeout=4, record_history_chains=False)
            async def wait_for_response(controller: SessionController, event: AstrMessageEvent):
                cur_msg = event.message_str
                hole_msgs += f"{cur_msg}\n"
                
                controller.keep(timeout=4, reset_timeout=True)

            try:
                await wait_for_response(event)
            except TimeoutError:
                logger.info("No more messages received within timeout.")
                logger.info(f"Collected messages:\n{hole_msgs}")
                req.prompt = f"{req.prompt}\n[{hole_msgs}]"
                hole_msgs = ""
                yield event.plain_result(f"send msg")
            except Exception as e:
                yield event.plain_result("发生错误，请联系管理员: " + str(e))
            finally:
                self.is_listening = False
                event.stop_event()
        except Exception as e:
            yield event.plain_result("发生错误，请联系管理员: " + str(e))

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
