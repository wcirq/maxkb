# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： display_setting.py
    @date：2026/4/22 00:00
    @desc:
"""
import base64
import mimetypes

from django.db.models import QuerySet
from rest_framework import serializers

from system_manage.models import SystemSetting, SettingType


DEFAULT_DISPLAY_SETTING = {
    'theme': '#3370FF',
    'icon': '',
    'loginLogo': '',
    'loginImage': '',
    'title': 'MaxKB',
    'slogan': '强大易用的企业级智能体平台',
    'showUserManual': True,
    'userManualUrl': 'https://maxkb.cn/docs/',
    'showForum': True,
    'forumUrl': 'https://bbs.fit2cloud.com/c/mk/11',
    'showProject': True,
    'projectUrl': 'https://github.com/1Panel-dev/MaxKB',
}


def file_to_data_url(file_obj):
    content_type = getattr(file_obj, 'content_type', None) or mimetypes.guess_type(
        getattr(file_obj, 'name', '')
    )[0] or 'application/octet-stream'
    content = file_obj.read()
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)
    encoded = base64.b64encode(content).decode('utf-8')
    return f'data:{content_type};base64,{encoded}'


class DisplaySettingSerializer(serializers.Serializer):
    @staticmethod
    def default_meta():
        return DEFAULT_DISPLAY_SETTING.copy()

    @staticmethod
    def one():
        system_setting = QuerySet(SystemSetting).filter(type=SettingType.DISPLAY.value).first()
        if system_setting is None:
            return DisplaySettingSerializer.default_meta()
        return {**DisplaySettingSerializer.default_meta(), **system_setting.meta}

    class Update(serializers.Serializer):
        theme = serializers.CharField(required=False, allow_blank=True)
        title = serializers.CharField(required=False, allow_blank=True)
        slogan = serializers.CharField(required=False, allow_blank=True)
        showUserManual = serializers.BooleanField(required=False)
        userManualUrl = serializers.CharField(required=False, allow_blank=True)
        showForum = serializers.BooleanField(required=False)
        forumUrl = serializers.CharField(required=False, allow_blank=True)
        showProject = serializers.BooleanField(required=False)
        projectUrl = serializers.CharField(required=False, allow_blank=True)

        def to_internal_value(self, data):
            mutable_data = {}
            field_names = set(self.fields.keys())
            for key in field_names:
                if key in ['icon', 'loginLogo', 'loginImage']:
                    continue
                if hasattr(data, 'get'):
                    value = data.get(key)
                    if value is not None:
                        mutable_data[key] = value
                elif key in data:
                    mutable_data[key] = data[key]
            return super().to_internal_value(mutable_data)

        def _get_asset_value(self, key, default_value=''):
            request = self.context.get('request')
            if request is not None and key in request.FILES:
                return file_to_data_url(request.FILES[key])
            if key in self.initial_data:
                value = self.initial_data.get(key)
                return value if isinstance(value, str) else ''
            return default_value

        def update_or_save(self):
            self.is_valid(raise_exception=True)
            system_setting = QuerySet(SystemSetting).filter(type=SettingType.DISPLAY.value).first()
            current_meta = DisplaySettingSerializer.one()
            meta = {**current_meta, **self.validated_data}

            for key in ['icon', 'loginLogo', 'loginImage']:
                meta[key] = self._get_asset_value(key, current_meta.get(key, ''))

            if system_setting is None:
                system_setting = SystemSetting(type=SettingType.DISPLAY.value)
            system_setting.meta = meta
            system_setting.save()
            return meta
