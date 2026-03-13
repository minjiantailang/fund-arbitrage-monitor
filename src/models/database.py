"""
数据库模型和连接管理
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """SQLite数据库管理类"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 默认数据库路径：用户数据目录
            data_dir = Path.home() / ".fund_arbitrage_monitor"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "fund_data.db")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 创建基金基本信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS funds (
                        code TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,  -- ETF, LOF
                        pinyin TEXT,         -- 拼音简写
                        exchange TEXT,       -- 交易所
                        currency TEXT DEFAULT 'CNY',
                        management_fee REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 检查并添加 pinyin 字段（用于平滑升级现有数据库）
                try:
                    cursor.execute("SELECT pinyin FROM funds LIMIT 1")
                except sqlite3.OperationalError:
                    logger.info("正在升级数据库：为 funds 表添加 pinyin 字段")
                    cursor.execute("ALTER TABLE funds ADD COLUMN pinyin TEXT")

                # 创建基金价格表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fund_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fund_code TEXT NOT NULL,
                        nav REAL,           -- 单位净值
                        price REAL,         -- 市场价格
                        spread_pct REAL,    -- 价差百分比
                        yield_pct REAL,     -- 收益率（扣除费用）
                        volume BIGINT,      -- 成交量
                        amount REAL,        -- 成交额
                        timestamp TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (fund_code) REFERENCES funds(code),
                        UNIQUE(fund_code, timestamp)
                    )
                """)

                # 创建套利机会记录表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fund_code TEXT NOT NULL,
                        opportunity_type TEXT NOT NULL,  -- ETF, LOF
                        nav REAL NOT NULL,
                        price REAL NOT NULL,
                        spread_pct REAL NOT NULL,
                        yield_pct REAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (fund_code) REFERENCES funds(code)
                    )
                """)

                # 创建用户配置表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建索引以提高查询性能
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_fund_prices_code_time ON fund_prices(fund_code, timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_fund_prices_timestamp ON fund_prices(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_arbitrage_timestamp ON arbitrage_opportunities(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_arbitrage_spread ON arbitrage_opportunities(spread_pct)")

                conn.commit()
                logger.info(f"数据库初始化完成: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    def save_fund(self, fund_data: Dict[str, Any]) -> bool:
        """
        保存或更新基金信息

        Args:
            fund_data: 基金数据字典，必须包含code, name, type字段

        Returns:
            bool: 操作是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO funds
                    (code, name, type, exchange, currency, management_fee, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    fund_data["code"],
                    fund_data["name"],
                    fund_data["type"],
                    fund_data.get("exchange"),
                    fund_data.get("currency", "CNY"),
                    fund_data.get("management_fee", 0.0),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"保存基金信息失败: {e}")
            return False

    def save_fund_price(self, price_data: Dict[str, Any]) -> bool:
        """
        保存基金价格数据

        Args:
            price_data: 价格数据字典，必须包含fund_code, nav, price, timestamp字段

        Returns:
            bool: 操作是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO fund_prices
                    (fund_code, nav, price, spread_pct, yield_pct, volume, amount, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    price_data["fund_code"],
                    price_data.get("nav"),
                    price_data.get("price"),
                    price_data.get("spread_pct"),
                    price_data.get("yield_pct"),
                    price_data.get("volume"),
                    price_data.get("amount"),
                    price_data["timestamp"]
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"保存基金价格失败: {e}")
            return False

    def save_arbitrage_opportunity(self, opportunity_data: Dict[str, Any]) -> bool:
        """
        保存套利机会记录

        Args:
            opportunity_data: 套利机会数据字典

        Returns:
            bool: 操作是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO arbitrage_opportunities
                    (fund_code, opportunity_type, nav, price, spread_pct, yield_pct, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    opportunity_data["fund_code"],
                    opportunity_data["opportunity_type"],
                    float(opportunity_data["nav"]),
                    float(opportunity_data["price"]),
                    float(opportunity_data["spread_pct"]),
                    float(opportunity_data["yield_pct"]),
                    opportunity_data["timestamp"]
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"保存套利机会失败: {e}")
            return False

    def save_fund_data(self, fund_data_list: List[Dict[str, Any]]) -> bool:
        """
        批量保存基金数据（基金信息和价格）

        Args:
            fund_data_list: 基金数据列表，每个元素包含基金信息和价格

        Returns:
            bool: 操作是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for fund_data in fund_data_list:
                    # 保存基金信息
                    fund_info = {
                        "code": fund_data["code"],
                        "name": fund_data["name"],
                        "type": fund_data["type"],
                        "exchange": fund_data.get("exchange"),
                        "currency": fund_data.get("currency", "CNY"),
                        "management_fee": fund_data.get("management_fee", 0.0)
                    }

                    cursor.execute("""
                        INSERT OR REPLACE INTO funds
                        (code, name, type, exchange, currency, management_fee, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        fund_info["code"],
                        fund_info["name"],
                        fund_info["type"],
                        fund_info["exchange"],
                        fund_info["currency"],
                        float(fund_info["management_fee"]),
                        fund_data.get("timestamp")  # 使用价格时间戳作为更新时间
                    ))

                    # 保存基金价格
                    if "nav" in fund_data and "price" in fund_data:
                        price_info = {
                            "fund_code": fund_data["code"],
                            "nav": float(fund_data["nav"]),
                            "price": float(fund_data["price"]),
                            "spread_pct": float(fund_data.get("spread_pct", 0.0)),
                            "yield_pct": float(fund_data.get("yield_pct", 0.0)),
                            "volume": fund_data.get("volume", 0),
                            "amount": float(fund_data.get("amount", 0.0)),
                            "timestamp": fund_data.get("timestamp")
                        }

                        cursor.execute("""
                            INSERT OR REPLACE INTO fund_prices
                            (fund_code, nav, price, spread_pct, yield_pct, volume, amount, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            price_info["fund_code"],
                            price_info["nav"],
                            price_info["price"],
                            price_info["spread_pct"],
                            price_info["yield_pct"],
                            price_info["volume"],
                            price_info["amount"],
                            price_info["timestamp"]
                        ))

                conn.commit()
                return True

        except sqlite3.Error as e:
            logger.error(f"批量保存基金数据失败: {e}")
            return False
        except KeyError as e:
            logger.error(f"基金数据缺少必要字段: {e}")
            return False

    def save_arbitrage_opportunities(self, opportunities: List[Dict[str, Any]]) -> bool:
        """
        批量保存套利机会

        Args:
            opportunities: 套利机会列表

        Returns:
            bool: 操作是否成功
        """
        success = True
        for opportunity in opportunities:
            if not self.save_arbitrage_opportunity(opportunity):
                success = False
        return success

    def get_funds(self, fund_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取基金列表

        Args:
            fund_type: 基金类型筛选（ETF/LOF），None表示获取所有

        Returns:
            List[Dict]: 基金列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if fund_type:
                    cursor.execute("SELECT * FROM funds WHERE type = ? ORDER BY code", (fund_type,))
                else:
                    cursor.execute("SELECT * FROM funds ORDER BY code")

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"获取基金列表失败: {e}")
            return []

    def get_fund_prices(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取基金价格数据（按时间倒序）

        Args:
            limit: 返回记录数限制
            offset: 偏移量

        Returns:
            List[Dict]: 基金价格数据列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, f.code, f.name, f.type
                    FROM fund_prices p
                    JOIN funds f ON p.fund_code = f.code
                    ORDER BY p.timestamp DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"获取基金价格失败: {e}")
            return []

    def get_latest_prices(self, fund_codes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取最新价格数据

        Args:
            fund_codes: 基金代码列表，None表示获取所有

        Returns:
            List[Dict]: 最新价格数据列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if fund_codes:
                    placeholders = ",".join(["?"] * len(fund_codes))
                    query = f"""
                        SELECT p.*, f.code, f.name, f.type
                        FROM fund_prices p
                        JOIN funds f ON p.fund_code = f.code
                        WHERE p.fund_code IN ({placeholders})
                        AND p.timestamp = (
                            SELECT MAX(timestamp)
                            FROM fund_prices
                            WHERE fund_code = p.fund_code
                        )
                        ORDER BY p.spread_pct DESC
                    """
                    cursor.execute(query, fund_codes)
                else:
                    cursor.execute("""
                        SELECT p.*, f.code, f.name, f.type
                        FROM fund_prices p
                        JOIN funds f ON p.fund_code = f.code
                        WHERE p.timestamp = (
                            SELECT MAX(timestamp)
                            FROM fund_prices
                            WHERE fund_code = p.fund_code
                        )
                        ORDER BY p.spread_pct DESC
                    """)

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"获取最新价格失败: {e}")
            return []

    def get_price_history(self, fund_code: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取基金价格历史数据

        Args:
            fund_code: 基金代码
            days: 获取最近多少天的数据

        Returns:
            List[Dict]: 价格历史数据
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM fund_prices
                    WHERE fund_code = ?
                    AND timestamp >= datetime('now', ?)
                    ORDER BY timestamp DESC
                """, (fund_code, f"-{days} days"))

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"获取价格历史失败: {e}")
            return []

    def get_arbitrage_opportunities(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取套利机会记录

        Args:
            limit: 返回记录数限制
            offset: 偏移量

        Returns:
            List[Dict]: 套利机会记录列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.*, f.code, f.name, f.type
                    FROM arbitrage_opportunities a
                    JOIN funds f ON a.fund_code = f.code
                    ORDER BY a.timestamp DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"获取套利机会失败: {e}")
            return []

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取用户配置

        Args:
            key: 配置键
            default: 默认值

        Returns:
            Optional[str]: 配置值
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result["value"] if result else default
        except sqlite3.Error as e:
            logger.error(f"获取配置失败: {e}")
            return default

    def set_setting(self, key: str, value: str, description: Optional[str] = None) -> bool:
        """
        设置用户配置

        Args:
            key: 配置键
            value: 配置值
            description: 配置描述

        Returns:
            bool: 操作是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_settings (key, value, description, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (key, value, description, datetime.now().isoformat()))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"设置配置失败: {e}")
            return False

    def clean_old_data(self, days: int = 30) -> bool:
        """
        清理指定天数前的旧数据

        Args:
            days: 保留最近多少天的数据

        Returns:
            bool: 操作是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 清理fund_prices表中的旧数据
                cursor.execute("""
                    DELETE FROM fund_prices
                    WHERE timestamp < datetime('now', ?)
                """, (f"-{days} days",))

                # 清理arbitrage_opportunities表中的旧数据
                cursor.execute("""
                    DELETE FROM arbitrage_opportunities
                    WHERE timestamp < datetime('now', ?)
                """, (f"-{days} days",))

                conn.commit()

                deleted_count = cursor.rowcount
                logger.info(f"清理了 {deleted_count} 条 {days} 天前的旧数据")
                return True

        except sqlite3.Error as e:
            logger.error(f"清理旧数据失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # 基金总数
                cursor.execute("SELECT COUNT(*) FROM funds")
                stats["total_funds"] = cursor.fetchone()[0]

                # ETF数量
                cursor.execute("SELECT COUNT(*) FROM funds WHERE type = 'ETF'")
                stats["etf_count"] = cursor.fetchone()[0]

                # LOF数量
                cursor.execute("SELECT COUNT(*) FROM funds WHERE type = 'LOF'")
                stats["lof_count"] = cursor.fetchone()[0]

                # 价格记录数
                cursor.execute("SELECT COUNT(*) FROM fund_prices")
                stats["price_records"] = cursor.fetchone()[0]

                # 套利机会记录数
                cursor.execute("SELECT COUNT(*) FROM arbitrage_opportunities")
                stats["opportunity_records"] = cursor.fetchone()[0]

                # 最新更新时间
                cursor.execute("SELECT MAX(timestamp) FROM fund_prices")
                last_update = cursor.fetchone()[0]
                stats["last_update"] = last_update if last_update else "无数据"

                return stats

        except sqlite3.Error as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_funds": 0,
                "etf_count": 0,
                "lof_count": 0,
                "price_records": 0,
                "opportunity_records": 0,
                "last_update": "获取失败"
            }

    def _get_connection(self) -> sqlite3.Connection:
        """获取一个新的数据库连接（线程安全）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def close(self):
        """关闭数据库连接（兼容性方法，实际无操作）"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 全局数据库实例
_db_instance: Optional[Database] = None


def get_database(db_path: Optional[str] = None) -> Database:
    """
    获取数据库实例（单例模式）

    Args:
        db_path: 数据库文件路径

    Returns:
        Database: 数据库实例
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance