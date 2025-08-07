# app/utils/statistics.py
# -*- coding: utf-8 -*-
"""
统计分析工具函数
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import logging
from datetime import datetime, timedelta, date
from collections import defaultdict, Counter
import json
import math

logger = logging.getLogger(__name__)


class StatisticsPeriod(Enum):
    """统计周期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class MetricType(Enum):
    """指标类型"""
    COUNT = "count"  # 计数
    SUM = "sum"  # 求和
    AVERAGE = "average"  # 平均值
    MAX = "max"  # 最大值
    MIN = "min"  # 最小值
    RATE = "rate"  # 比率
    GROWTH = "growth"  # 增长率


class StatisticsCalculator:
    """统计计算器"""
    
    @staticmethod
    def calculate_growth_rate(current_value: float, previous_value: float) -> float:
        """计算增长率"""
        try:
            if previous_value == 0:
                return 100.0 if current_value > 0 else 0.0
            
            growth_rate = ((current_value - previous_value) / previous_value) * 100
            return round(growth_rate, 2)
            
        except Exception as e:
            logger.error(f"计算增长率失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_conversion_rate(converted: int, total: int) -> float:
        """计算转化率"""
        try:
            if total == 0:
                return 0.0
            
            rate = (converted / total) * 100
            return round(rate, 2)
            
        except Exception as e:
            logger.error(f"计算转化率失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_retention_rate(
        retained_users: int,
        total_users: int
    ) -> float:
        """计算留存率"""
        try:
            if total_users == 0:
                return 0.0
            
            rate = (retained_users / total_users) * 100
            return round(rate, 2)
            
        except Exception as e:
            logger.error(f"计算留存率失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_average(values: List[Union[int, float]]) -> float:
        """计算平均值"""
        try:
            if not values:
                return 0.0
            
            return round(sum(values) / len(values), 2)
            
        except Exception as e:
            logger.error(f"计算平均值失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_percentile(values: List[Union[int, float]], percentile: float) -> float:
        """计算百分位数"""
        try:
            if not values:
                return 0.0
            
            sorted_values = sorted(values)
            index = (percentile / 100) * (len(sorted_values) - 1)
            
            if index.is_integer():
                return sorted_values[int(index)]
            else:
                lower_index = int(index)
                upper_index = lower_index + 1
                weight = index - lower_index
                
                return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
            
        except Exception as e:
            logger.error(f"计算百分位数失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_standard_deviation(values: List[Union[int, float]]) -> float:
        """计算标准差"""
        try:
            if len(values) < 2:
                return 0.0
            
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
            
            return round(math.sqrt(variance), 2)
            
        except Exception as e:
            logger.error(f"计算标准差失败: {e}")
            return 0.0


class UserStatistics:
    """用户统计"""
    
    def __init__(self):
        self.calculator = StatisticsCalculator()
    
    def get_user_overview(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取用户概览统计"""
        try:
            # 这里应该从数据库查询实际数据
            # 暂时返回模拟数据
            
            total_users = 10000
            new_users = 500
            active_users = 3000
            previous_period_users = 9500
            
            return {
                "total_users": total_users,
                "new_users": new_users,
                "active_users": active_users,
                "growth_rate": self.calculator.calculate_growth_rate(
                    total_users, previous_period_users
                ),
                "activity_rate": self.calculator.calculate_conversion_rate(
                    active_users, total_users
                ),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户概览统计失败: {e}")
            return {}
    
    def get_user_registration_trend(
        self,
        start_date: date,
        end_date: date,
        period: StatisticsPeriod = StatisticsPeriod.DAILY
    ) -> Dict[str, Any]:
        """获取用户注册趋势"""
        try:
            # 生成日期范围
            date_range = self._generate_date_range(start_date, end_date, period)
            
            # 模拟注册数据
            trend_data = []
            for date_point in date_range:
                registrations = 50 + (hash(str(date_point)) % 100)  # 模拟数据
                trend_data.append({
                    "date": date_point.isoformat(),
                    "registrations": registrations
                })
            
            total_registrations = sum(item["registrations"] for item in trend_data)
            
            return {
                "trend_data": trend_data,
                "total_registrations": total_registrations,
                "average_daily": self.calculator.calculate_average(
                    [item["registrations"] for item in trend_data]
                ),
                "period": period.value
            }
            
        except Exception as e:
            logger.error(f"获取用户注册趋势失败: {e}")
            return {"trend_data": [], "total_registrations": 0}
    
    def get_user_activity_analysis(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取用户活跃度分析"""
        try:
            # 模拟活跃度数据
            activity_data = {
                "daily_active_users": 3000,
                "weekly_active_users": 8000,
                "monthly_active_users": 15000,
                "session_duration": {
                    "average": 25.5,  # 分钟
                    "median": 18.0,
                    "percentile_90": 45.0
                },
                "page_views_per_session": {
                    "average": 12.3,
                    "median": 8.0,
                    "percentile_90": 25.0
                },
                "bounce_rate": 35.2,  # 百分比
                "return_rate": 68.5   # 百分比
            }
            
            return activity_data
            
        except Exception as e:
            logger.error(f"获取用户活跃度分析失败: {e}")
            return {}
    
    def get_user_retention_analysis(
        self,
        cohort_date: date,
        periods: int = 30
    ) -> Dict[str, Any]:
        """获取用户留存分析"""
        try:
            # 模拟留存数据
            initial_users = 1000
            retention_data = []
            
            for day in range(1, periods + 1):
                # 模拟留存率递减
                retention_rate = max(10, 100 - (day * 2.5))
                retained_users = int(initial_users * (retention_rate / 100))
                
                retention_data.append({
                    "day": day,
                    "retained_users": retained_users,
                    "retention_rate": round(retention_rate, 2)
                })
            
            return {
                "cohort_date": cohort_date.isoformat(),
                "initial_users": initial_users,
                "retention_data": retention_data,
                "day_1_retention": retention_data[0]["retention_rate"] if retention_data else 0,
                "day_7_retention": retention_data[6]["retention_rate"] if len(retention_data) > 6 else 0,
                "day_30_retention": retention_data[29]["retention_rate"] if len(retention_data) > 29 else 0
            }
            
        except Exception as e:
            logger.error(f"获取用户留存分析失败: {e}")
            return {}
    
    def get_user_demographics(self) -> Dict[str, Any]:
        """获取用户人口统计"""
        try:
            # 模拟人口统计数据
            demographics = {
                "age_distribution": {
                    "18-25": 25.5,
                    "26-35": 35.2,
                    "36-45": 22.8,
                    "46-55": 12.3,
                    "55+": 4.2
                },
                "gender_distribution": {
                    "male": 45.8,
                    "female": 52.1,
                    "other": 2.1
                },
                "location_distribution": {
                    "北京": 15.2,
                    "上海": 12.8,
                    "广州": 8.5,
                    "深圳": 7.9,
                    "其他": 55.6
                },
                "device_distribution": {
                    "mobile": 78.5,
                    "desktop": 18.2,
                    "tablet": 3.3
                }
            }
            
            return demographics
            
        except Exception as e:
            logger.error(f"获取用户人口统计失败: {e}")
            return {}
    
    def _generate_date_range(
        self,
        start_date: date,
        end_date: date,
        period: StatisticsPeriod
    ) -> List[date]:
        """生成日期范围"""
        try:
            date_range = []
            current_date = start_date
            
            if period == StatisticsPeriod.DAILY:
                while current_date <= end_date:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)
            
            elif period == StatisticsPeriod.WEEKLY:
                while current_date <= end_date:
                    date_range.append(current_date)
                    current_date += timedelta(weeks=1)
            
            elif period == StatisticsPeriod.MONTHLY:
                while current_date <= end_date:
                    date_range.append(current_date)
                    # 简化处理，每月按30天计算
                    current_date += timedelta(days=30)
            
            return date_range
            
        except Exception as e:
            logger.error(f"生成日期范围失败: {e}")
            return []


class NovelStatistics:
    """小说统计"""
    
    def __init__(self):
        self.calculator = StatisticsCalculator()
    
    def get_novel_overview(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取小说概览统计"""
        try:
            # 模拟小说统计数据
            overview = {
                "total_novels": 50000,
                "new_novels": 1200,
                "active_novels": 25000,
                "completed_novels": 15000,
                "total_chapters": 2500000,
                "new_chapters": 15000,
                "total_words": 125000000000,  # 1250亿字
                "new_words": 750000000,      # 7.5亿字
                "average_words_per_novel": 2500000,
                "average_chapters_per_novel": 50,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"获取小说概览统计失败: {e}")
            return {}
    
    def get_novel_category_statistics(self) -> Dict[str, Any]:
        """获取小说分类统计"""
        try:
            # 模拟分类统计数据
            category_stats = {
                "distribution": {
                    "玄幻": {"count": 12000, "percentage": 24.0},
                    "都市": {"count": 8500, "percentage": 17.0},
                    "历史": {"count": 6000, "percentage": 12.0},
                    "科幻": {"count": 5500, "percentage": 11.0},
                    "武侠": {"count": 4500, "percentage": 9.0},
                    "言情": {"count": 7000, "percentage": 14.0},
                    "其他": {"count": 6500, "percentage": 13.0}
                },
                "popularity_ranking": [
                    {"category": "玄幻", "avg_views": 15000, "avg_favorites": 800},
                    {"category": "言情", "avg_views": 12000, "avg_favorites": 950},
                    {"category": "都市", "avg_views": 10000, "avg_favorites": 600},
                    {"category": "科幻", "avg_views": 8500, "avg_favorites": 550},
                    {"category": "历史", "avg_views": 7500, "avg_favorites": 450},
                    {"category": "武侠", "avg_views": 7000, "avg_favorites": 400},
                    {"category": "其他", "avg_views": 5000, "avg_favorites": 300}
                ]
            }
            
            return category_stats
            
        except Exception as e:
            logger.error(f"获取小说分类统计失败: {e}")
            return {}
    
    def get_reading_statistics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取阅读统计"""
        try:
            # 模拟阅读统计数据
            reading_stats = {
                "total_views": 50000000,
                "unique_readers": 800000,
                "total_reading_time": 25000000,  # 分钟
                "average_reading_time": 31.25,   # 分钟
                "chapters_read": 8000000,
                "completion_rate": 15.5,         # 百分比
                "popular_reading_times": {
                    "morning": 15.2,    # 8-12点
                    "afternoon": 25.8,  # 12-18点
                    "evening": 45.5,    # 18-24点
                    "night": 13.5       # 0-8点
                },
                "device_usage": {
                    "mobile": 82.5,
                    "desktop": 15.2,
                    "tablet": 2.3
                },
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
            return reading_stats
            
        except Exception as e:
            logger.error(f"获取阅读统计失败: {e}")
            return {}
    
    def get_author_statistics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取作者统计"""
        try:
            # 模拟作者统计数据
            author_stats = {
                "total_authors": 15000,
                "active_authors": 8000,
                "new_authors": 500,
                "productive_authors": 2000,  # 本期有更新的作者
                "average_novels_per_author": 3.3,
                "average_updates_per_author": 12.5,
                "top_authors": [
                    {
                        "author_id": 1,
                        "name": "知名作者1",
                        "novels_count": 15,
                        "total_views": 5000000,
                        "total_favorites": 250000
                    },
                    {
                        "author_id": 2,
                        "name": "知名作者2",
                        "novels_count": 8,
                        "total_views": 3500000,
                        "total_favorites": 180000
                    }
                ],
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
            return author_stats
            
        except Exception as e:
            logger.error(f"获取作者统计失败: {e}")
            return {}
    
    def get_novel_ranking(
        self,
        ranking_type: str = "views",
        period: StatisticsPeriod = StatisticsPeriod.WEEKLY,
        limit: int = 50
    ) -> Dict[str, Any]:
        """获取小说排行榜"""
        try:
            # 模拟排行榜数据
            rankings = []
            
            for i in range(1, limit + 1):
                novel_data = {
                    "rank": i,
                    "novel_id": i,
                    "title": f"热门小说{i}",
                    "author": f"作者{i}",
                    "category": ["玄幻", "都市", "历史", "科幻"][i % 4],
                    "views": 100000 - (i * 1000),
                    "favorites": 5000 - (i * 50),
                    "comments": 1000 - (i * 10),
                    "rating": round(5.0 - (i * 0.02), 2),
                    "growth_rate": round(50.0 - (i * 0.5), 2)
                }
                rankings.append(novel_data)
            
            return {
                "rankings": rankings,
                "ranking_type": ranking_type,
                "period": period.value,
                "total_count": len(rankings),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取小说排行榜失败: {e}")
            return {"rankings": []}


class RevenueStatistics:
    """收入统计"""
    
    def __init__(self):
        self.calculator = StatisticsCalculator()
    
    def get_revenue_overview(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取收入概览"""
        try:
            # 模拟收入数据
            overview = {
                "total_revenue": 1250000.00,      # 总收入
                "subscription_revenue": 800000.00, # 订阅收入
                "purchase_revenue": 300000.00,     # 购买收入
                "reward_revenue": 150000.00,       # 打赏收入
                "average_revenue_per_user": 125.00,
                "paying_users": 10000,
                "conversion_rate": 12.5,           # 付费转化率
                "revenue_growth_rate": 15.8,       # 收入增长率
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"获取收入概览失败: {e}")
            return {}
    
    def get_revenue_trend(
        self,
        start_date: date,
        end_date: date,
        period: StatisticsPeriod = StatisticsPeriod.DAILY
    ) -> Dict[str, Any]:
        """获取收入趋势"""
        try:
            # 生成日期范围
            date_range = self._generate_date_range(start_date, end_date, period)
            
            # 模拟收入趋势数据
            trend_data = []
            base_revenue = 10000
            
            for i, date_point in enumerate(date_range):
                # 模拟收入波动
                daily_revenue = base_revenue + (i * 100) + (hash(str(date_point)) % 2000)
                
                trend_data.append({
                    "date": date_point.isoformat(),
                    "total_revenue": daily_revenue,
                    "subscription_revenue": daily_revenue * 0.6,
                    "purchase_revenue": daily_revenue * 0.25,
                    "reward_revenue": daily_revenue * 0.15
                })
            
            total_revenue = sum(item["total_revenue"] for item in trend_data)
            
            return {
                "trend_data": trend_data,
                "total_revenue": total_revenue,
                "average_daily_revenue": self.calculator.calculate_average(
                    [item["total_revenue"] for item in trend_data]
                ),
                "period": period.value
            }
            
        except Exception as e:
            logger.error(f"获取收入趋势失败: {e}")
            return {"trend_data": [], "total_revenue": 0}
    
    def get_payment_method_analysis(self) -> Dict[str, Any]:
        """获取支付方式分析"""
        try:
            # 模拟支付方式数据
            payment_analysis = {
                "distribution": {
                    "alipay": {"count": 5500, "amount": 687500.00, "percentage": 55.0},
                    "wechat": {"count": 3200, "amount": 400000.00, "percentage": 32.0},
                    "bank_card": {"count": 800, "amount": 100000.00, "percentage": 8.0},
                    "balance": {"count": 500, "amount": 62500.00, "percentage": 5.0}
                },
                "success_rates": {
                    "alipay": 98.5,
                    "wechat": 97.8,
                    "bank_card": 95.2,
                    "balance": 99.9
                },
                "average_transaction_amount": {
                    "alipay": 125.00,
                    "wechat": 125.00,
                    "bank_card": 125.00,
                    "balance": 125.00
                }
            }
            
            return payment_analysis
            
        except Exception as e:
            logger.error(f"获取支付方式分析失败: {e}")
            return {}
    
    def _generate_date_range(
        self,
        start_date: date,
        end_date: date,
        period: StatisticsPeriod
    ) -> List[date]:
        """生成日期范围"""
        try:
            date_range = []
            current_date = start_date
            
            if period == StatisticsPeriod.DAILY:
                while current_date <= end_date:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)
            
            elif period == StatisticsPeriod.WEEKLY:
                while current_date <= end_date:
                    date_range.append(current_date)
                    current_date += timedelta(weeks=1)
            
            elif period == StatisticsPeriod.MONTHLY:
                while current_date <= end_date:
                    date_range.append(current_date)
                    current_date += timedelta(days=30)
            
            return date_range
            
        except Exception as e:
            logger.error(f"生成日期范围失败: {e}")
            return []


class StatisticsManager:
    """统计管理器"""
    
    def __init__(self):
        self.user_stats = UserStatistics()
        self.novel_stats = NovelStatistics()
        self.revenue_stats = RevenueStatistics()
        self.calculator = StatisticsCalculator()
    
    def get_dashboard_overview(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取仪表板概览"""
        try:
            # 获取各模块统计数据
            user_overview = self.user_stats.get_user_overview(start_date, end_date)
            novel_overview = self.novel_stats.get_novel_overview(start_date, end_date)
            revenue_overview = self.revenue_stats.get_revenue_overview(start_date, end_date)
            
            # 组合仪表板数据
            dashboard = {
                "users": user_overview,
                "novels": novel_overview,
                "revenue": revenue_overview,
                "key_metrics": {
                    "total_users": user_overview.get("total_users", 0),
                    "active_users": user_overview.get("active_users", 0),
                    "total_novels": novel_overview.get("total_novels", 0),
                    "total_revenue": revenue_overview.get("total_revenue", 0),
                    "paying_users": revenue_overview.get("paying_users", 0)
                },
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "generated_at": datetime.now().isoformat()
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"获取仪表板概览失败: {e}")
            return {}
    
    def generate_report(
        self,
        report_type: str,
        start_date: date,
        end_date: date,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """生成统计报告"""
        try:
            report_data = {}
            
            if report_type == "user":
                report_data = {
                    "overview": self.user_stats.get_user_overview(start_date, end_date),
                    "registration_trend": self.user_stats.get_user_registration_trend(start_date, end_date),
                    "activity_analysis": self.user_stats.get_user_activity_analysis(start_date, end_date),
                    "demographics": self.user_stats.get_user_demographics()
                }
            
            elif report_type == "novel":
                report_data = {
                    "overview": self.novel_stats.get_novel_overview(start_date, end_date),
                    "category_statistics": self.novel_stats.get_novel_category_statistics(),
                    "reading_statistics": self.novel_stats.get_reading_statistics(start_date, end_date),
                    "author_statistics": self.novel_stats.get_author_statistics(start_date, end_date)
                }
            
            elif report_type == "revenue":
                report_data = {
                    "overview": self.revenue_stats.get_revenue_overview(start_date, end_date),
                    "trend": self.revenue_stats.get_revenue_trend(start_date, end_date),
                    "payment_analysis": self.revenue_stats.get_payment_method_analysis()
                }
            
            elif report_type == "comprehensive":
                report_data = self.get_dashboard_overview(start_date, end_date)
            
            # 添加报告元信息
            report_data["report_info"] = {
                "type": report_type,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "generated_at": datetime.now().isoformat(),
                "format": format_type
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"生成统计报告失败: {e}")
            return {}


# 全局统计管理器实例
statistics_manager = StatisticsManager()


def get_statistics_overview(
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """获取统计概览的便捷函数"""
    return statistics_manager.get_dashboard_overview(start_date, end_date)


def generate_statistics_report(
    report_type: str,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """生成统计报告的便捷函数"""
    return statistics_manager.generate_report(report_type, start_date, end_date)