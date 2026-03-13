"""
测试东方财富 API 接口
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.data_sources.eastmoney_api import EastMoneyAPI


class TestEastMoneyAPI:
    """测试 EastMoneyAPI 类"""

    @pytest.fixture
    def api(self):
        return EastMoneyAPI()

    @patch("requests.Session.get")
    def test_get_fund_list_success(self, mock_get, api):
        """测试获取基金列表成功"""
        # 模拟响应数据
        # var r = [["000001","HXCZ","华夏成长","混合型","HUAXIACHENGZHANG"], ...];
        mock_response = Mock()
        mock_response.text = 'var r = [["510300","HS300ETF","沪深300ETF","股票型","HUSHEN300ETF"],["161005","FGTHLOF","富国天惠LOF","混合型","FUGUOTIANHUILOF"]];'
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        funds = api.get_fund_list()

        assert len(funds) == 2
        assert funds[0]["code"] == "510300"
        assert funds[0]["name"] == "沪深300ETF"
        assert funds[1]["code"] == "161005"
        assert funds[1]["name"] == "富国天惠LOF"

    @patch("requests.Session.get")
    def test_get_fund_list_parse_error(self, mock_get, api):
        """测试解析错误"""
        mock_response = Mock()
        mock_response.text = 'invalid data'
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        funds = api.get_fund_list()
        assert len(funds) == 0

    @patch("requests.Session.get")
    def test_get_fund_valuation_success(self, mock_get, api):
        """测试获取估值成功"""
        mock_response = Mock()
        # jsonpgz({"fundcode":"510300","name":"...","jzrq":"2023-01-01","dwjz":"3.56","gsz":"3.58","gszzl":"0.56","gztime":"2023-01-02 15:00"});
        json_data = {
            "fundcode": "510300",
            "name": "沪深300ETF",
            "jzrq": "2023-01-01",
            "dwjz": "3.56",
            "gsz": "3.58",
            "gszzl": "0.56",
            "gztime": "2023-01-02 15:00"
        }
        mock_response.text = f'jsonpgz({json.dumps(json_data)});'
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        valuation = api.get_fund_valuation("510300")

        assert valuation is not None
        assert valuation["fundcode"] == "510300"
        assert valuation["nav"] == 3.56
        assert valuation["est_nav"] == 3.58

    @patch("requests.Session.get")
    def test_get_realtime_quotes_success(self, mock_get, api):
        """测试批量获取行情成功"""
        mock_response = Mock()
        # 模拟 push2 接口返回
        response_data = {
            "data": {
                "diff": {
                    "0": {
                        "f12": "510300",
                        "f14": "沪深300ETF",
                        "f2": 3.58,
                        "f3": 0.56,
                        "f5": 1000000,
                        "f6": 3580000.0,
                        "f18": 3.56  # prev_close
                    },
                    "1": {
                        "f12": "161005",
                        "f14": "富国天惠LOF",
                        "f2": 1.60,
                        "f3": 1.2,
                        "f5": 500000,
                        "f6": 800000.0,
                        "f18": 1.58
                    }
                }
            }
        }
        mock_response.json.return_value = response_data
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        quotes = api.get_realtime_quotes(["510300", "161005"])

        assert len(quotes) == 2
        assert quotes[0]["code"] == "510300"
        assert quotes[0]["price"] == 3.58
        assert quotes[1]["code"] == "161005"
        assert quotes[1]["price"] == 1.60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
