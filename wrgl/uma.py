import re
from typing import Union, Dict, Tuple, Callable

import requests
from requests.exceptions import HTTPError

from wrgl.serialize import json_dumps


class UMAClient:
    _rsc_uri: str = ""
    _client_id: str = ""
    _client_secret: str = ""
    _access_token: str = ""
    rpt: str = ""

    def __init__(self, rsc_uri: str, client_id: str, client_secret: str) -> None:
        """
        :param str rsc_uri: the URI of the UMA resource
        :param str client_id: Keycloak client id
        :param str client_secret: Keycloak client secret
        """
        self._rsc_uri = rsc_uri.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret

    def _headers(self, headers=None) -> Union[Dict, None]:
        if self.rpt:
            if headers is None:
                headers = dict()
            headers["Authorization"] = "Bearer " + self.rpt
        return headers

    def _extract_uma_ticket(
        self, resp: requests.Response
    ) -> Tuple[Union[str, None], Union[str, None]]:
        auth_header = resp.headers.get("WWW-Authenticate", "")
        if auth_header.startswith("UMA "):
            parts = auth_header.split(",")
            values = dict()
            for s in parts:
                key, value = tuple(s.strip().split("="))
                values[key] = value.strip('"')
            return values.get("as_uri", None), values.get("ticket", None)
        return None, None

    def _discover_uma_config(self, as_uri: str) -> Dict:
        resp = requests.get(as_uri.rstrip("/") + "/.well-known/uma2-configuration")
        resp.raise_for_status()
        return resp.json()

    def _fetch_access_token(self, token_endpoint: str) -> None:
        resp = requests.post(
            token_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        resp.raise_for_status()
        resp_data = resp.json()
        self._access_token = resp_data["access_token"]
        return

    def _fetch_rpt(self, token_endpoint: str, uma_ticket: str) -> None:
        resp = requests.post(
            token_endpoint,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
                "ticket": uma_ticket,
            },
            headers={"Authorization": "Bearer " + self._access_token},
        )
        resp.raise_for_status()
        resp_data = resp.json()
        self.rpt = resp_data["access_token"]
        return

    def _ensure_rpt(self, as_uri: str, uma_ticket: str) -> None:
        uma_config = self._discover_uma_config(as_uri)
        token_endpoint = uma_config["token_endpoint"]
        if not self._access_token:
            self._fetch_access_token(token_endpoint)
        try:
            self._fetch_rpt(token_endpoint, uma_ticket)
        except HTTPError as e:
            if e.response.status_code == 401:
                self._fetch_access_token(token_endpoint)
                self._fetch_rpt(token_endpoint, uma_ticket)
            else:
                raise

    def _do_request(
        self,
        method: str,
        url: str,
        params=None,
        headers=None,
        create_request_args: Union[Callable[..., Dict], None] = None,
        *args,
        **kwargs
    ) -> requests.Response:
        if create_request_args is not None:
            args_dict = create_request_args()
            args_dict["headers"] = self._headers(args_dict.get("headers", None))
            return requests.request(method, url, **args_dict)
        if params is not None:
            params = {k: v for k, v in params.items() if v}
        return requests.request(
            method, url, params=params, headers=self._headers(headers), *args, **kwargs
        )

    def request(
        self,
        method: str,
        path: str,
        params=None,
        headers=None,
        create_request_args: Union[Callable[..., Dict], None] = None,
        *args,
        **kwargs
    ) -> requests.Response:
        """Make a request

        :param str method: HTTP verb
        :param str path: path relative to rsc_uri
        :param dict params: optional, query parameters
        :param dict headers: optional, HTTP headers
        :param func create_request_args: optional. If defined, this function is called to generate request arguments. Useful when request need to be retried.
        :param list args: extra positional arguments passed to requests.request. Ignored if create_request_args is defined.
        :param dict kwargs: extra keyword arguments passed to requests.request. Ignored if create_request_args is defined.

        :rtype: requests.Response
        """
        url = self._rsc_uri + path
        resp = self._do_request(
            method, url, params, headers, create_request_args, *args, **kwargs
        )
        if resp.status_code == 401:
            as_uri, uma_ticket = self._extract_uma_ticket(resp)
            if uma_ticket is not None:
                self._ensure_rpt(as_uri, uma_ticket)
                resp = self._do_request(
                    method, url, params, headers, create_request_args, *args, **kwargs
                )
        resp.raise_for_status()
        return resp

    def get(
        self, path: str, params=None, headers=None, *args, **kwargs
    ) -> requests.Response:
        """Make a get request

        :param str path: path relative to rsc_uri
        :param dict params: optional, query parameters
        :param dict headers: optional, HTTP headers
        :param list args: extra positional arguments passed to requests.request. Ignored if create_request_args is defined.
        :param dict kwargs: extra keyword arguments passed to requests.request. Ignored if create_request_args is defined.

        :rtype: requests.Response
        """
        return self.request(
            "GET", path, params=params, headers=headers, *args, **kwargs
        )

    def post(
        self,
        path: str,
        params=None,
        headers=None,
        create_request_args: Union[Callable[..., Dict], None] = None,
        *args,
        **kwargs
    ) -> requests.Response:
        """Make a post request

        :param str path: path relative to rsc_uri
        :param dict params: optional, query parameters
        :param dict headers: optional, HTTP headers
        :param func create_request_args: optional. If defined, this function is called to generate request arguments. Useful when request need to be retried.
        :param list args: extra positional arguments passed to requests.request. Ignored if create_request_args is defined.
        :param dict kwargs: extra keyword arguments passed to requests.request. Ignored if create_request_args is defined.

        :rtype: requests.Response
        """
        return self.request(
            "POST",
            path,
            params=params,
            headers=headers,
            create_request_args=create_request_args,
            *args,
            **kwargs
        )
