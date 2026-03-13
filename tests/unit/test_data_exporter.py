"""
数据导出器单元测试
"""
import pytest
import json
import csv
import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import datetime

from src.utils.data_exporter import DataExporter


class TestDataExporter:
    """数据导出器测试"""

    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        return [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "type": "ETF",
                "nav": 3.56,
                "price": 3.58,
                "spread_pct": 0.56,
                "yield_pct": 0.20,
                "is_opportunity": False,
            },
            {
                "code": "161005",
                "name": "富国天惠LOF",
                "type": "LOF",
                "nav": 1.56,
                "price": 1.60,
                "spread_pct": 2.56,
                "yield_pct": 1.50,
                "is_opportunity": True,
            },
        ]

    def test_export_to_csv_success(self, sample_data, tmp_path):
        """测试CSV导出成功"""
        file_path = tmp_path / "test_export.csv"
        result = DataExporter.export_to_csv(sample_data, str(file_path))

        assert result is True
        assert file_path.exists()

        # 验证CSV内容
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["code"] == "510300"
        assert rows[1]["code"] == "161005"

    def test_export_to_csv_empty_data(self, tmp_path):
        """测试空数据CSV导出"""
        file_path = tmp_path / "empty.csv"
        result = DataExporter.export_to_csv([], str(file_path))

        assert result is False
        assert not file_path.exists()

    def test_export_to_json_success(self, sample_data, tmp_path):
        """测试JSON导出成功"""
        file_path = tmp_path / "test_export.json"
        result = DataExporter.export_to_json(sample_data, str(file_path))

        assert result is True
        assert file_path.exists()

        # 验证JSON内容
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        assert len(loaded_data) == 2
        assert loaded_data[0]["code"] == "510300"
        assert loaded_data[1]["code"] == "161005"

    def test_export_to_json_empty_data(self, tmp_path):
        """测试空数据JSON导出"""
        file_path = tmp_path / "empty.json"
        result = DataExporter.export_to_json([], str(file_path))

        assert result is False
        assert not file_path.exists()

    def test_export_to_json_with_decimal(self, tmp_path):
        """测试带Decimal类型的JSON导出"""
        data = [
            {
                "code": "510300",
                "nav": Decimal("3.56"),
                "price": Decimal("3.58"),
            }
        ]
        file_path = tmp_path / "decimal_export.json"
        result = DataExporter.export_to_json(data, str(file_path))

        assert result is True

        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        assert loaded_data[0]["nav"] == 3.56
        assert loaded_data[0]["price"] == 3.58

    def test_export_to_html_success(self, sample_data, tmp_path):
        """测试HTML导出成功"""
        file_path = tmp_path / "test_report.html"
        result = DataExporter.export_to_html(sample_data, str(file_path))

        assert result is True
        assert file_path.exists()

        # 验证HTML内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "510300" in content
        assert "161005" in content
        assert "沪深300ETF" in content
        assert "<!DOCTYPE html>" in content

    def test_export_to_html_empty_data(self, tmp_path):
        """测试空数据HTML导出"""
        file_path = tmp_path / "empty.html"
        result = DataExporter.export_to_html([], str(file_path))

        assert result is False
        assert not file_path.exists()

    def test_export_auto_format_csv(self, sample_data, tmp_path):
        """测试自动识别CSV格式"""
        file_path = tmp_path / "auto.csv"
        result = DataExporter.export(sample_data, str(file_path))

        assert result is True
        assert file_path.exists()

    def test_export_auto_format_json(self, sample_data, tmp_path):
        """测试自动识别JSON格式"""
        file_path = tmp_path / "auto.json"
        result = DataExporter.export(sample_data, str(file_path))

        assert result is True
        assert file_path.exists()

    def test_export_auto_format_html(self, sample_data, tmp_path):
        """测试自动识别HTML格式"""
        file_path = tmp_path / "auto.html"
        result = DataExporter.export(sample_data, str(file_path))

        assert result is True
        assert file_path.exists()

    def test_get_supported_formats(self):
        """测试获取支持的格式"""
        formats = DataExporter.get_supported_formats()

        assert "csv" in formats
        assert "json" in formats
        assert "excel" in formats
        assert "html" in formats

    def test_make_serializable_with_datetime(self):
        """测试datetime序列化"""
        now = datetime.now()
        data = [
            {
                "code": "510300",
                "timestamp": now,
            }
        ]

        result = DataExporter._make_serializable(data)

        assert result[0]["timestamp"] == now.isoformat()

    def test_generate_html_report_structure(self, sample_data):
        """测试HTML报告结构"""
        html = DataExporter._generate_html_report(sample_data, "测试报告")

        # 验证关键结构
        assert "<html" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "<table>" in html
        assert "<header>" in html
        assert "<footer>" in html
        assert "测试报告" in html


class TestDataExporterEdgeCases:
    """数据导出器边界情况测试"""

    def test_export_with_special_characters(self, tmp_path):
        """测试特殊字符导出"""
        data = [
            {
                "code": "510300",
                "name": "沪深300ETF (A类)",
                "description": '包含"引号"和\'单引号\'',
            }
        ]
        file_path = tmp_path / "special.csv"
        result = DataExporter.export_to_csv(data, str(file_path))

        assert result is True

    def test_export_with_none_values(self, tmp_path):
        """测试None值导出"""
        data = [
            {
                "code": "510300",
                "name": None,
                "nav": 3.56,
            }
        ]
        file_path = tmp_path / "none_values.json"
        result = DataExporter.export_to_json(data, str(file_path))

        assert result is True

        with open(file_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded[0]["name"] is None

    def test_export_large_dataset(self, tmp_path):
        """测试大数据集导出"""
        large_data = [
            {
                "code": f"5{i:05d}",
                "name": f"测试基金{i}",
                "nav": 1.0 + i * 0.001,
                "price": 1.0 + i * 0.001 * 1.02,
            }
            for i in range(1000)
        ]
        file_path = tmp_path / "large.csv"
        result = DataExporter.export_to_csv(large_data, str(file_path))

        assert result is True

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
