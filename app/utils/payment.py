# app/utils/payment.py
# -*- coding: utf-8 -*-
"""
支付系统工具函数
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
import json
import logging
import hashlib
import hmac
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class PaymentMethod(Enum):
    """支付方式"""
    ALIPAY = "alipay"  # 支付宝
    WECHAT = "wechat"  # 微信支付
    BANK_CARD = "bank_card"  # 银行卡
    BALANCE = "balance"  # 余额支付
    POINTS = "points"  # 积分支付


class PaymentStatus(Enum):
    """支付状态"""
    PENDING = "pending"  # 待支付
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"  # 支付成功
    FAILED = "failed"  # 支付失败
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款
    PARTIAL_REFUNDED = "partial_refunded"  # 部分退款


class TransactionType(Enum):
    """交易类型"""
    RECHARGE = "recharge"  # 充值
    PURCHASE = "purchase"  # 购买
    REWARD = "reward"  # 打赏
    REFUND = "refund"  # 退款
    WITHDRAWAL = "withdrawal"  # 提现
    TRANSFER = "transfer"  # 转账


class CurrencyType(Enum):
    """货币类型"""
    CNY = "CNY"  # 人民币
    COINS = "COINS"  # 书币
    POINTS = "POINTS"  # 积分


@dataclass
class PaymentOrder:
    """支付订单"""
    id: Optional[str] = None
    user_id: int = 0
    amount: Decimal = Decimal('0.00')
    currency: CurrencyType = CurrencyType.CNY
    method: PaymentMethod = PaymentMethod.ALIPAY
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_type: TransactionType = TransactionType.PURCHASE
    subject: str = ""
    description: str = ""
    extra_data: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    third_party_order_id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = self._generate_order_id()
        if self.extra_data is None:
            self.extra_data = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.expires_at is None:
            self.expires_at = datetime.now() + timedelta(minutes=30)
    
    def _generate_order_id(self) -> str:
        """生成订单ID"""
        timestamp = str(int(time.time()))
        random_str = str(uuid.uuid4()).replace('-', '')[:8]
        return f"PAY{timestamp}{random_str}".upper()


class PaymentProcessor:
    """支付处理器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app_id = config.get("app_id")
        self.secret_key = config.get("secret_key")
        self.notify_url = config.get("notify_url")
        self.return_url = config.get("return_url")
    
    def create_payment(self, order: PaymentOrder) -> Dict[str, Any]:
        """创建支付"""
        raise NotImplementedError
    
    def query_payment(self, order_id: str) -> Dict[str, Any]:
        """查询支付状态"""
        raise NotImplementedError
    
    def cancel_payment(self, order_id: str) -> Dict[str, Any]:
        """取消支付"""
        raise NotImplementedError
    
    def refund_payment(
        self,
        order_id: str,
        refund_amount: Decimal,
        reason: str = ""
    ) -> Dict[str, Any]:
        """退款"""
        raise NotImplementedError
    
    def verify_callback(self, data: Dict[str, Any]) -> bool:
        """验证回调签名"""
        raise NotImplementedError


class AlipayProcessor(PaymentProcessor):
    """支付宝支付处理器"""
    
    def create_payment(self, order: PaymentOrder) -> Dict[str, Any]:
        """创建支付宝支付"""
        try:
            # 构建支付参数
            params = {
                "app_id": self.app_id,
                "method": "alipay.trade.app.pay",
                "charset": "utf-8",
                "sign_type": "RSA2",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0",
                "notify_url": self.notify_url,
                "biz_content": json.dumps({
                    "out_trade_no": order.id,
                    "total_amount": str(order.amount),
                    "subject": order.subject,
                    "body": order.description,
                    "timeout_express": "30m"
                })
            }
            
            # 生成签名
            sign = self._generate_sign(params)
            params["sign"] = sign
            
            # 构建支付字符串
            pay_string = "&".join([f"{k}={v}" for k, v in params.items()])
            
            return {
                "success": True,
                "pay_string": pay_string,
                "order_id": order.id
            }
            
        except Exception as e:
            logger.error(f"创建支付宝支付失败: {e}")
            return {"success": False, "error": str(e)}
    
    def query_payment(self, order_id: str) -> Dict[str, Any]:
        """查询支付宝支付状态"""
        try:
            # 模拟查询结果
            return {
                "success": True,
                "status": PaymentStatus.SUCCESS.value,
                "trade_no": f"alipay_{order_id}",
                "paid_amount": "10.00",
                "paid_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"查询支付宝支付状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    def cancel_payment(self, order_id: str) -> Dict[str, Any]:
        """取消支付宝支付"""
        try:
            # 模拟取消结果
            return {"success": True, "message": "支付已取消"}
            
        except Exception as e:
            logger.error(f"取消支付宝支付失败: {e}")
            return {"success": False, "error": str(e)}
    
    def refund_payment(
        self,
        order_id: str,
        refund_amount: Decimal,
        reason: str = ""
    ) -> Dict[str, Any]:
        """支付宝退款"""
        try:
            # 模拟退款结果
            return {
                "success": True,
                "refund_id": f"refund_{order_id}_{int(time.time())}",
                "refund_amount": str(refund_amount)
            }
            
        except Exception as e:
            logger.error(f"支付宝退款失败: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_callback(self, data: Dict[str, Any]) -> bool:
        """验证支付宝回调签名"""
        try:
            # 提取签名
            sign = data.pop("sign", "")
            sign_type = data.pop("sign_type", "")
            
            # 验证签名
            expected_sign = self._generate_sign(data)
            
            return sign == expected_sign
            
        except Exception as e:
            logger.error(f"验证支付宝回调签名失败: {e}")
            return False
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        try:
            # 排序参数
            sorted_params = sorted(params.items())
            
            # 构建签名字符串
            sign_string = "&".join([f"{k}={v}" for k, v in sorted_params if v])
            
            # 使用密钥签名（这里简化处理）
            signature = hmac.new(
                self.secret_key.encode(),
                sign_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"生成签名失败: {e}")
            return ""


class WechatProcessor(PaymentProcessor):
    """微信支付处理器"""
    
    def create_payment(self, order: PaymentOrder) -> Dict[str, Any]:
        """创建微信支付"""
        try:
            # 构建支付参数
            params = {
                "appid": self.app_id,
                "mch_id": self.config.get("mch_id"),
                "nonce_str": str(uuid.uuid4()).replace('-', ''),
                "body": order.subject,
                "out_trade_no": order.id,
                "total_fee": int(order.amount * 100),  # 微信支付金额单位为分
                "spbill_create_ip": "127.0.0.1",
                "notify_url": self.notify_url,
                "trade_type": "APP"
            }
            
            # 生成签名
            sign = self._generate_sign(params)
            params["sign"] = sign
            
            return {
                "success": True,
                "prepay_id": f"wx_prepay_{order.id}",
                "params": params
            }
            
        except Exception as e:
            logger.error(f"创建微信支付失败: {e}")
            return {"success": False, "error": str(e)}
    
    def query_payment(self, order_id: str) -> Dict[str, Any]:
        """查询微信支付状态"""
        try:
            # 模拟查询结果
            return {
                "success": True,
                "status": PaymentStatus.SUCCESS.value,
                "transaction_id": f"wx_{order_id}",
                "paid_amount": "10.00",
                "paid_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"查询微信支付状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    def cancel_payment(self, order_id: str) -> Dict[str, Any]:
        """取消微信支付"""
        try:
            # 模拟取消结果
            return {"success": True, "message": "支付已取消"}
            
        except Exception as e:
            logger.error(f"取消微信支付失败: {e}")
            return {"success": False, "error": str(e)}
    
    def refund_payment(
        self,
        order_id: str,
        refund_amount: Decimal,
        reason: str = ""
    ) -> Dict[str, Any]:
        """微信退款"""
        try:
            # 模拟退款结果
            return {
                "success": True,
                "refund_id": f"wx_refund_{order_id}_{int(time.time())}",
                "refund_amount": str(refund_amount)
            }
            
        except Exception as e:
            logger.error(f"微信退款失败: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_callback(self, data: Dict[str, Any]) -> bool:
        """验证微信回调签名"""
        try:
            # 提取签名
            sign = data.pop("sign", "")
            
            # 验证签名
            expected_sign = self._generate_sign(data)
            
            return sign == expected_sign
            
        except Exception as e:
            logger.error(f"验证微信回调签名失败: {e}")
            return False
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成微信签名"""
        try:
            # 排序参数
            sorted_params = sorted(params.items())
            
            # 构建签名字符串
            sign_string = "&".join([f"{k}={v}" for k, v in sorted_params if v])
            sign_string += f"&key={self.secret_key}"
            
            # MD5签名
            signature = hashlib.md5(sign_string.encode()).hexdigest().upper()
            
            return signature
            
        except Exception as e:
            logger.error(f"生成微信签名失败: {e}")
            return ""


class BalanceProcessor(PaymentProcessor):
    """余额支付处理器"""
    
    def create_payment(self, order: PaymentOrder) -> Dict[str, Any]:
        """创建余额支付"""
        try:
            # 检查用户余额
            user_balance = self._get_user_balance(order.user_id)
            
            if user_balance < order.amount:
                return {
                    "success": False,
                    "error": "余额不足",
                    "balance": str(user_balance),
                    "required": str(order.amount)
                }
            
            # 扣除余额
            success = self._deduct_balance(order.user_id, order.amount, order.id)
            
            if success:
                return {
                    "success": True,
                    "order_id": order.id,
                    "paid_amount": str(order.amount),
                    "remaining_balance": str(user_balance - order.amount)
                }
            else:
                return {"success": False, "error": "余额扣除失败"}
            
        except Exception as e:
            logger.error(f"创建余额支付失败: {e}")
            return {"success": False, "error": str(e)}
    
    def query_payment(self, order_id: str) -> Dict[str, Any]:
        """查询余额支付状态"""
        try:
            # 查询支付记录
            return {
                "success": True,
                "status": PaymentStatus.SUCCESS.value,
                "paid_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"查询余额支付状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    def cancel_payment(self, order_id: str) -> Dict[str, Any]:
        """取消余额支付"""
        try:
            # 余额支付通常是即时的，无法取消
            return {"success": False, "error": "余额支付无法取消"}
            
        except Exception as e:
            logger.error(f"取消余额支付失败: {e}")
            return {"success": False, "error": str(e)}
    
    def refund_payment(
        self,
        order_id: str,
        refund_amount: Decimal,
        reason: str = ""
    ) -> Dict[str, Any]:
        """余额退款"""
        try:
            # 获取订单信息
            order_info = self._get_order_info(order_id)
            if not order_info:
                return {"success": False, "error": "订单不存在"}
            
            # 退款到余额
            success = self._add_balance(
                order_info["user_id"],
                refund_amount,
                f"退款：{order_id}"
            )
            
            if success:
                return {
                    "success": True,
                    "refund_id": f"balance_refund_{order_id}_{int(time.time())}",
                    "refund_amount": str(refund_amount)
                }
            else:
                return {"success": False, "error": "退款失败"}
            
        except Exception as e:
            logger.error(f"余额退款失败: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_callback(self, data: Dict[str, Any]) -> bool:
        """验证余额支付回调"""
        # 余额支付不需要回调验证
        return True
    
    def _get_user_balance(self, user_id: int) -> Decimal:
        """获取用户余额"""
        try:
            # 这里应该从数据库查询用户余额
            # 暂时返回模拟数据
            return Decimal('100.00')
            
        except Exception as e:
            logger.error(f"获取用户余额失败: {e}")
            return Decimal('0.00')
    
    def _deduct_balance(self, user_id: int, amount: Decimal, order_id: str) -> bool:
        """扣除用户余额"""
        try:
            # 这里应该更新数据库中的用户余额
            logger.info(f"扣除用户 {user_id} 余额 {amount}，订单: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"扣除用户余额失败: {e}")
            return False
    
    def _add_balance(self, user_id: int, amount: Decimal, reason: str) -> bool:
        """增加用户余额"""
        try:
            # 这里应该更新数据库中的用户余额
            logger.info(f"增加用户 {user_id} 余额 {amount}，原因: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"增加用户余额失败: {e}")
            return False
    
    def _get_order_info(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单信息"""
        try:
            # 这里应该从数据库查询订单信息
            return {"user_id": 1, "amount": "10.00"}
            
        except Exception as e:
            logger.error(f"获取订单信息失败: {e}")
            return None


class PaymentManager:
    """支付管理器"""
    
    def __init__(self):
        self.processors = {}
        self._setup_processors()
    
    def _setup_processors(self):
        """设置支付处理器"""
        # 支付宝配置
        alipay_config = {
            "app_id": "your_alipay_app_id",
            "secret_key": "your_alipay_secret_key",
            "notify_url": "https://your-domain.com/api/payment/alipay/notify",
            "return_url": "https://your-domain.com/payment/return"
        }
        
        # 微信支付配置
        wechat_config = {
            "app_id": "your_wechat_app_id",
            "mch_id": "your_wechat_mch_id",
            "secret_key": "your_wechat_secret_key",
            "notify_url": "https://your-domain.com/api/payment/wechat/notify"
        }
        
        # 余额支付配置
        balance_config = {}
        
        # 注册处理器
        self.processors[PaymentMethod.ALIPAY] = AlipayProcessor(alipay_config)
        self.processors[PaymentMethod.WECHAT] = WechatProcessor(wechat_config)
        self.processors[PaymentMethod.BALANCE] = BalanceProcessor(balance_config)
    
    def create_order(
        self,
        user_id: int,
        amount: Union[Decimal, float, str],
        currency: CurrencyType,
        transaction_type: TransactionType,
        subject: str,
        description: str = "",
        extra_data: Optional[Dict[str, Any]] = None
    ) -> PaymentOrder:
        """创建支付订单"""
        try:
            # 转换金额为Decimal
            if isinstance(amount, (float, str)):
                amount = Decimal(str(amount)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
            
            order = PaymentOrder(
                user_id=user_id,
                amount=amount,
                currency=currency,
                transaction_type=transaction_type,
                subject=subject,
                description=description,
                extra_data=extra_data or {}
            )
            
            # 保存订单到数据库
            self._save_order(order)
            
            return order
            
        except Exception as e:
            logger.error(f"创建支付订单失败: {e}")
            raise
    
    def create_payment(
        self,
        order: PaymentOrder,
        payment_method: PaymentMethod
    ) -> Dict[str, Any]:
        """创建支付"""
        try:
            processor = self.processors.get(payment_method)
            if not processor:
                return {"success": False, "error": f"不支持的支付方式: {payment_method.value}"}
            
            # 更新订单支付方式
            order.method = payment_method
            self._update_order(order)
            
            # 创建支付
            result = processor.create_payment(order)
            
            # 更新订单状态
            if result.get("success"):
                order.status = PaymentStatus.PROCESSING
                if payment_method == PaymentMethod.BALANCE:
                    order.status = PaymentStatus.SUCCESS
                    order.paid_at = datetime.now()
            else:
                order.status = PaymentStatus.FAILED
            
            self._update_order(order)
            
            return result
            
        except Exception as e:
            logger.error(f"创建支付失败: {e}")
            return {"success": False, "error": str(e)}
    
    def query_payment_status(self, order_id: str) -> Dict[str, Any]:
        """查询支付状态"""
        try:
            order = self._get_order(order_id)
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            processor = self.processors.get(order.method)
            if not processor:
                return {"success": False, "error": "支付处理器不存在"}
            
            result = processor.query_payment(order_id)
            
            # 更新订单状态
            if result.get("success"):
                status = result.get("status")
                if status == PaymentStatus.SUCCESS.value:
                    order.status = PaymentStatus.SUCCESS
                    order.paid_at = datetime.fromisoformat(result.get("paid_at", datetime.now().isoformat()))
                    order.third_party_order_id = result.get("trade_no") or result.get("transaction_id")
                
                self._update_order(order)
            
            return result
            
        except Exception as e:
            logger.error(f"查询支付状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    def handle_payment_callback(
        self,
        payment_method: PaymentMethod,
        callback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理支付回调"""
        try:
            processor = self.processors.get(payment_method)
            if not processor:
                return {"success": False, "error": "支付处理器不存在"}
            
            # 验证回调签名
            if not processor.verify_callback(callback_data.copy()):
                return {"success": False, "error": "签名验证失败"}
            
            # 获取订单ID
            order_id = callback_data.get("out_trade_no")
            if not order_id:
                return {"success": False, "error": "订单ID不存在"}
            
            # 获取订单
            order = self._get_order(order_id)
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            # 更新订单状态
            trade_status = callback_data.get("trade_status") or callback_data.get("result_code")
            
            if trade_status in ["TRADE_SUCCESS", "SUCCESS"]:
                order.status = PaymentStatus.SUCCESS
                order.paid_at = datetime.now()
                order.third_party_order_id = (
                    callback_data.get("trade_no") or 
                    callback_data.get("transaction_id")
                )
                
                # 处理支付成功后的业务逻辑
                self._handle_payment_success(order)
            
            elif trade_status in ["TRADE_CLOSED", "FAIL"]:
                order.status = PaymentStatus.FAILED
            
            self._update_order(order)
            
            return {"success": True, "message": "回调处理成功"}
            
        except Exception as e:
            logger.error(f"处理支付回调失败: {e}")
            return {"success": False, "error": str(e)}
    
    def refund_order(
        self,
        order_id: str,
        refund_amount: Optional[Decimal] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """退款订单"""
        try:
            order = self._get_order(order_id)
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            if order.status != PaymentStatus.SUCCESS:
                return {"success": False, "error": "订单状态不允许退款"}
            
            # 默认全额退款
            if refund_amount is None:
                refund_amount = order.amount
            
            # 检查退款金额
            if refund_amount > order.amount:
                return {"success": False, "error": "退款金额超过订单金额"}
            
            processor = self.processors.get(order.method)
            if not processor:
                return {"success": False, "error": "支付处理器不存在"}
            
            # 执行退款
            result = processor.refund_payment(order_id, refund_amount, reason)
            
            # 更新订单状态
            if result.get("success"):
                if refund_amount == order.amount:
                    order.status = PaymentStatus.REFUNDED
                else:
                    order.status = PaymentStatus.PARTIAL_REFUNDED
                
                self._update_order(order)
                
                # 记录退款信息
                self._record_refund(order_id, refund_amount, reason, result.get("refund_id"))
            
            return result
            
        except Exception as e:
            logger.error(f"退款订单失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _save_order(self, order: PaymentOrder) -> bool:
        """保存订单到数据库"""
        try:
            # 这里应该保存到数据库
            logger.info(f"保存支付订单: {order.id}")
            return True
            
        except Exception as e:
            logger.error(f"保存订单失败: {e}")
            return False
    
    def _update_order(self, order: PaymentOrder) -> bool:
        """更新订单"""
        try:
            order.updated_at = datetime.now()
            # 这里应该更新数据库
            logger.info(f"更新支付订单: {order.id}, 状态: {order.status.value}")
            return True
            
        except Exception as e:
            logger.error(f"更新订单失败: {e}")
            return False
    
    def _get_order(self, order_id: str) -> Optional[PaymentOrder]:
        """获取订单"""
        try:
            # 这里应该从数据库查询
            # 暂时返回模拟数据
            return PaymentOrder(
                id=order_id,
                user_id=1,
                amount=Decimal('10.00'),
                currency=CurrencyType.CNY,
                method=PaymentMethod.ALIPAY,
                status=PaymentStatus.PENDING,
                transaction_type=TransactionType.PURCHASE,
                subject="测试订单"
            )
            
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            return None
    
    def _handle_payment_success(self, order: PaymentOrder) -> bool:
        """处理支付成功后的业务逻辑"""
        try:
            # 根据交易类型处理不同的业务逻辑
            if order.transaction_type == TransactionType.RECHARGE:
                # 充值：增加用户余额
                self._add_user_balance(order.user_id, order.amount)
            
            elif order.transaction_type == TransactionType.PURCHASE:
                # 购买：解锁内容或发放商品
                self._unlock_content(order.user_id, order.extra_data)
            
            elif order.transaction_type == TransactionType.REWARD:
                # 打赏：转账给作者
                self._transfer_reward(order.user_id, order.extra_data, order.amount)
            
            return True
            
        except Exception as e:
            logger.error(f"处理支付成功业务逻辑失败: {e}")
            return False
    
    def _add_user_balance(self, user_id: int, amount: Decimal) -> bool:
        """增加用户余额"""
        try:
            # 这里应该更新数据库
            logger.info(f"增加用户 {user_id} 余额 {amount}")
            return True
            
        except Exception as e:
            logger.error(f"增加用户余额失败: {e}")
            return False
    
    def _unlock_content(self, user_id: int, extra_data: Dict[str, Any]) -> bool:
        """解锁内容"""
        try:
            # 这里应该解锁用户购买的内容
            logger.info(f"为用户 {user_id} 解锁内容: {extra_data}")
            return True
            
        except Exception as e:
            logger.error(f"解锁内容失败: {e}")
            return False
    
    def _transfer_reward(
        self,
        user_id: int,
        extra_data: Dict[str, Any],
        amount: Decimal
    ) -> bool:
        """转账打赏"""
        try:
            # 这里应该将打赏金额转给作者
            author_id = extra_data.get("author_id")
            logger.info(f"用户 {user_id} 打赏作者 {author_id} 金额 {amount}")
            return True
            
        except Exception as e:
            logger.error(f"转账打赏失败: {e}")
            return False
    
    def _record_refund(
        self,
        order_id: str,
        refund_amount: Decimal,
        reason: str,
        refund_id: str
    ) -> bool:
        """记录退款信息"""
        try:
            # 这里应该记录退款信息到数据库
            logger.info(f"记录退款: 订单 {order_id}, 金额 {refund_amount}, 退款ID {refund_id}")
            return True
            
        except Exception as e:
            logger.error(f"记录退款信息失败: {e}")
            return False


# 全局支付管理器实例
payment_manager = PaymentManager()


def create_payment_order(
    user_id: int,
    amount: Union[Decimal, float, str],
    currency: CurrencyType,
    transaction_type: TransactionType,
    subject: str,
    description: str = "",
    extra_data: Optional[Dict[str, Any]] = None
) -> PaymentOrder:
    """创建支付订单的便捷函数"""
    return payment_manager.create_order(
        user_id=user_id,
        amount=amount,
        currency=currency,
        transaction_type=transaction_type,
        subject=subject,
        description=description,
        extra_data=extra_data
    )


def process_payment(
    order: PaymentOrder,
    payment_method: PaymentMethod
) -> Dict[str, Any]:
    """处理支付的便捷函数"""
    return payment_manager.create_payment(order, payment_method)