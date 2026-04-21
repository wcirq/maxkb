# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： display_setting.py
    @date：2026/4/22 00:00
    @desc:
"""
from common.mixins.api_mixin import APIMixin
from common.result import ResultSerializer
from system_manage.serializers.display_setting import DisplaySettingSerializer


class DisplayResponse(ResultSerializer):
    def get_data(self):
        return DisplaySettingSerializer.Update()


class DisplaySettingAPI(APIMixin):
    @staticmethod
    def get_request():
        return DisplaySettingSerializer.Update()

    @staticmethod
    def get_response():
        return DisplayResponse
