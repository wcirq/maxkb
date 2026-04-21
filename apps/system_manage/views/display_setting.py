# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： display_setting.py
    @date：2026/4/22 00:00
    @desc:
"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth import TokenAuth, AnonymousAuthentication
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.result import result
from system_manage.api.display_setting import DisplaySettingAPI
from system_manage.serializers.display_setting import DisplaySettingSerializer


class DisplaySettingView(APIView):
    def get_authenticators(self):
        if self.request.method == 'GET':
            return [AnonymousAuthentication()]
        return [TokenAuth()]

    @extend_schema(
        methods=['GET'],
        summary=_('Get appearance settings'),
        description=_('Get appearance settings'),
        operation_id=_('Get appearance settings'),  # type: ignore
        responses=DisplaySettingAPI.get_response(),
        tags=[_('Appearance Settings')]  # type: ignore
    )
    def get(self, request: Request):
        return result.success(DisplaySettingSerializer.one())

    @extend_schema(
        methods=['PUT'],
        summary=_('Create or update appearance settings'),
        description=_('Create or update appearance settings'),
        operation_id=_('Create or update appearance settings'),  # type: ignore
        request=DisplaySettingAPI.get_request(),
        responses=DisplaySettingAPI.get_response(),
        tags=[_('Appearance Settings')]  # type: ignore
    )
    @has_permissions(PermissionConstants.APPEARANCE_SETTINGS_EDIT, RoleConstants.ADMIN)
    def put(self, request: Request):
        return result.success(
            DisplaySettingSerializer.Update(data=request.data, context={'request': request}).update_or_save()
        )
