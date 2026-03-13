"""
数据导出工具 - 支持多种导出格式
"""
import csv
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class DataExporter:
    """数据导出器 - 支持CSV、JSON、Excel格式"""

    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], file_path: str) -> bool:
        """
        导出数据到CSV文件

        Args:
            data: 数据列表
            file_path: 文件路径

        Returns:
            bool: 是否成功
        """
        if not data:
            logger.warning("没有数据可导出")
            return False

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"数据已导出到CSV: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False

    @staticmethod
    def export_to_json(data: List[Dict[str, Any]], file_path: str, 
                       pretty: bool = True) -> bool:
        """
        导出数据到JSON文件

        Args:
            data: 数据列表
            file_path: 文件路径
            pretty: 是否格式化输出

        Returns:
            bool: 是否成功
        """
        if not data:
            logger.warning("没有数据可导出")
            return False

        try:
            # 转换数据类型（处理Decimal等）
            serializable_data = DataExporter._make_serializable(data)

            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(serializable_data, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(serializable_data, f, ensure_ascii=False)

            logger.info(f"数据已导出到JSON: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            return False

    @staticmethod
    def export_to_excel(data: List[Dict[str, Any]], file_path: str,
                        sheet_name: str = "基金数据") -> bool:
        """
        导出数据到Excel文件

        Args:
            data: 数据列表
            file_path: 文件路径
            sheet_name: 工作表名称

        Returns:
            bool: 是否成功
        """
        if not data:
            logger.warning("没有数据可导出")
            return False

        try:
            import pandas as pd

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 导出到Excel
            df.to_excel(file_path, sheet_name=sheet_name, index=False)

            logger.info(f"数据已导出到Excel: {file_path}")
            return True

        except ImportError:
            logger.error("需要安装openpyxl库来导出Excel: pip install openpyxl")
            return False
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            return False

    @staticmethod
    def export_to_html(data: List[Dict[str, Any]], file_path: str,
                       title: str = "基金套利监控报告") -> bool:
        """
        导出数据到HTML报告

        Args:
            data: 数据列表
            file_path: 文件路径
            title: 报告标题

        Returns:
            bool: 是否成功
        """
        if not data:
            logger.warning("没有数据可导出")
            return False

        try:
            html_content = DataExporter._generate_html_report(data, title)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"数据已导出到HTML: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出HTML失败: {e}")
            return False

    @staticmethod
    def _make_serializable(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将数据转换为可序列化格式"""
        from decimal import Decimal

        result = []
        for item in data:
            serializable_item = {}
            for key, value in item.items():
                if isinstance(value, Decimal):
                    serializable_item[key] = float(value)
                elif isinstance(value, datetime):
                    serializable_item[key] = value.isoformat()
                else:
                    serializable_item[key] = value
            result.append(serializable_item)
        return result

    @staticmethod
    def _generate_html_report(data: List[Dict[str, Any]], title: str) -> str:
        """生成HTML报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 计算统计信息
        total = len(data)
        opportunities = sum(1 for item in data if item.get("is_opportunity"))

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #0d6efd 0%, #6610f2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        header p {{
            opacity: 0.9;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #0d6efd;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background: #f1f3f4;
        }}
        .positive {{
            color: #dc3545;
            font-weight: 600;
        }}
        .negative {{
            color: #198754;
            font-weight: 600;
        }}
        .opportunity {{
            background: #fff3cd;
        }}
        footer {{
            padding: 20px;
            text-align: center;
            color: #6c757d;
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p>生成时间: {timestamp}</p>
        </header>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{total}</div>
                <div class="stat-label">基金总数</div>
            </div>
            <div class="stat">
                <div class="stat-value">{opportunities}</div>
                <div class="stat-label">套利机会</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>代码</th>
                    <th>名称</th>
                    <th>类型</th>
                    <th>净值</th>
                    <th>价格</th>
                    <th>价差%</th>
                    <th>收益率%</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
"""
        for item in data:
            code = item.get("code") or item.get("fund_code", "")
            name = item.get("name", "")
            fund_type = item.get("type", "")
            nav = item.get("nav", 0)
            price = item.get("price", 0)
            spread_pct = item.get("spread_pct", 0)
            yield_pct = item.get("yield_pct", 0)
            is_opportunity = item.get("is_opportunity", False)

            spread_class = "positive" if spread_pct > 0 else "negative" if spread_pct < 0 else ""
            row_class = "opportunity" if is_opportunity else ""
            status = "✅ 有机会" if is_opportunity else "—"

            html += f"""                <tr class="{row_class}">
                    <td>{code}</td>
                    <td>{name}</td>
                    <td>{fund_type}</td>
                    <td>{nav:.4f}</td>
                    <td>{price:.4f}</td>
                    <td class="{spread_class}">{spread_pct:+.2f}%</td>
                    <td>{yield_pct:.2f}%</td>
                    <td>{status}</td>
                </tr>
"""

        html += """            </tbody>
        </table>

        <footer>
            <p>本报告由基金套利监控系统自动生成，仅供参考，不构成投资建议。</p>
        </footer>
    </div>
</body>
</html>"""

        return html

    @staticmethod
    def get_supported_formats() -> Dict[str, str]:
        """
        获取支持的导出格式

        Returns:
            Dict: {格式ID: 格式名称}
        """
        return {
            "csv": "CSV文件 (*.csv)",
            "json": "JSON文件 (*.json)",
            "excel": "Excel文件 (*.xlsx)",
            "html": "HTML报告 (*.html)",
        }

    @staticmethod
    def export(data: List[Dict[str, Any]], file_path: str,
               format_type: Optional[str] = None) -> bool:
        """
        导出数据到文件

        Args:
            data: 数据列表
            file_path: 文件路径
            format_type: 格式类型，如果为None则从文件扩展名推断

        Returns:
            bool: 是否成功
        """
        if not format_type:
            # 从文件扩展名推断格式
            suffix = Path(file_path).suffix.lower()
            format_map = {
                ".csv": "csv",
                ".json": "json",
                ".xlsx": "excel",
                ".xls": "excel",
                ".html": "html",
                ".htm": "html",
            }
            format_type = format_map.get(suffix, "csv")

        export_methods = {
            "csv": DataExporter.export_to_csv,
            "json": DataExporter.export_to_json,
            "excel": DataExporter.export_to_excel,
            "html": DataExporter.export_to_html,
        }

        export_method = export_methods.get(format_type)
        if export_method:
            return export_method(data, file_path)
        else:
            logger.error(f"不支持的导出格式: {format_type}")
            return False
