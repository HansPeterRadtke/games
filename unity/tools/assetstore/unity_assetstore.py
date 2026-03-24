#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import secretstorage

CONFIG_PATH = Path('/home/hans/.config/unityhub/cloudConfig.json')
TOKENS_PATH = Path('/home/hans/.config/unityhub/encryptedTokens.json')
SAFE_STORAGE_LABEL = 'Chromium Safe Storage'
SAFE_STORAGE_APP = 'unityhub'
DEFAULT_STATE = Path('/data/src/github/games/unity/assetstore/metadata/download_state.json')
DEFAULT_CATALOG = Path('/data/src/github/games/unity/assetstore/metadata/my_assets.json')
AUTH_CACHE_PATH = Path('/data/src/github/games/unity/assetstore/metadata/auth_tokens.json')


def _load_cloud_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text())


def _get_safe_storage_password() -> str:
    bus = secretstorage.dbus_init()
    for collection in secretstorage.get_all_collections(bus):
        for item in collection.get_all_items():
            try:
                attrs = item.get_attributes()
                label = item.get_label()
            except Exception:
                continue
            if label == SAFE_STORAGE_LABEL and attrs.get('application') == SAFE_STORAGE_APP:
                return item.get_secret().decode('utf-8')
    raise RuntimeError('Could not find Unity Hub safe storage secret')


def _decrypt_tokens() -> dict[str, Any]:
    payload = json.loads(TOKENS_PATH.read_text())['tokens']['data']
    blob = bytes(payload)
    if blob[:3] not in (b'v10', b'v11'):
        raise RuntimeError(f'Unsupported token blob header: {blob[:3]!r}')
    password = _get_safe_storage_password()
    key = hashlib.pbkdf2_hmac('sha1', password.encode('utf-8'), b'saltysalt', 1, 16)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(b' ' * 16)).decryptor()
    plaintext = decryptor.update(blob[3:]) + decryptor.finalize()
    pad = plaintext[-1]
    plaintext = plaintext[:-pad]
    return json.loads(plaintext.decode('utf-8'))


def _load_auth_cache() -> dict[str, Any]:
    if AUTH_CACHE_PATH.exists():
        return json.loads(AUTH_CACHE_PATH.read_text())
    return {}


def _save_auth_cache(tokens: dict[str, Any]) -> None:
    AUTH_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUTH_CACHE_PATH.write_text(json.dumps(tokens, indent=2, sort_keys=True))


def _load_effective_tokens() -> dict[str, Any]:
    tokens = _decrypt_tokens()
    cached = _load_auth_cache()
    if cached.get('refreshToken') == tokens.get('refreshToken'):
        for key in ('accessToken', 'accessTokenExpiration', 'refreshToken', 'refreshTokenExpiration', 'unityToken', 'unityTokenExpiration'):
            if key in cached and cached[key]:
                tokens[key] = cached[key]
    return tokens


def _token_expired(tokens: dict[str, Any], skew_ms: int = 60_000) -> bool:
    expiry = int(tokens.get('accessTokenExpiration') or 0)
    now_ms = int(time.time() * 1000)
    return expiry <= now_ms + skew_ms


class UnityAssetStore:
    def __init__(self) -> None:
        self.config = _load_cloud_config()
        self.tokens = _load_effective_tokens()
        self.base = self.config['asset_store_api'].rstrip('/')
        self.session = requests.Session()
        if _token_expired(self.tokens):
            self.refresh_access_token()
        self.session.headers.update({'Authorization': f"Bearer {self.tokens['accessToken']}"})

    def refresh_access_token(self) -> None:
        refresh_token = self.tokens.get('refreshToken')
        if not refresh_token:
            raise RuntimeError('No Unity refresh token available')
        resp = requests.post(
            f"{self.config['core'].rstrip('/')}/api/login/refresh",
            json={'grant_type': 'refresh_token', 'refresh_token': refresh_token},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        self.tokens['accessToken'] = data['access_token']
        self.tokens['refreshToken'] = data.get('refresh_token', refresh_token)
        self.tokens['accessTokenExpiration'] = int(time.time() * 1000) + int(data.get('expires_in', 0)) * 1000
        _save_auth_cache(self.tokens)
        self.session.headers.update({'Authorization': f"Bearer {self.tokens['accessToken']}"})

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == 401:
            self.refresh_access_token()
            resp = self.session.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp

    def fetch_purchases(self, limit: int = 200) -> list[dict[str, Any]]:
        offset = 0
        results: list[dict[str, Any]] = []
        while True:
            resp = self._request(
                'GET',
                f'{self.base}/-/api/purchases',
                params={'offset': offset, 'limit': min(limit, 100), 'orderBy': 'purchased_date', 'order': 'desc'},
                timeout=60,
            )
            data = resp.json()
            chunk = data.get('results', [])
            results.extend(chunk)
            total = int(data.get('total', len(results)))
            if not chunk or len(results) >= total:
                break
            offset += len(chunk)
        return results

    def fetch_product(self, package_id: int) -> dict[str, Any]:
        resp = self._request('GET', f'{self.base}/-/api/product/{package_id}', timeout=60)
        return resp.json()

    def fetch_download_info(self, package_id: int) -> dict[str, Any]:
        resp = self._request('GET', f'{self.base}/-/api/legacy-package-download-info/{package_id}', timeout=60)
        return resp.json()


def sanitize_name(name: str) -> str:
    safe = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in name).strip('_')
    while '__' in safe:
        safe = safe.replace('__', '_')
    return safe or 'asset'


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def load_json(path: Path, default: Any) -> Any:
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_catalog(client: UnityAssetStore, catalog_path: Path) -> list[dict[str, Any]]:
    purchases = client.fetch_purchases()
    write_json(catalog_path, purchases)
    return purchases


def download_asset(client: UnityAssetStore, package_id: int, display_name: str, dest_dir: Path, state: dict[str, Any]) -> Path:
    info = client.fetch_download_info(package_id)
    download = info.get('result', {}).get('download', info)
    url = download['url']
    ext = '.unitypackage'
    final_name = f"{package_id}_{sanitize_name(display_name)}{ext}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    final_path = dest_dir / final_name
    tmp_path = final_path.with_suffix(final_path.suffix + '.part')

    if final_path.exists() and final_path.stat().st_size > 0:
        state[str(package_id)] = {'status': 'downloaded', 'path': str(final_path), 'size': final_path.stat().st_size, 'displayName': display_name}
        return final_path

    with client.session.get(url, stream=True, timeout=600) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get('content-length', '0') or 0)
        downloaded = 0
        with tmp_path.open('wb') as handle:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                downloaded += len(chunk)
                state[str(package_id)] = {
                    'status': 'downloading',
                    'path': str(tmp_path),
                    'displayName': display_name,
                    'downloaded': downloaded,
                    'total': total,
                    'updatedAt': time.time(),
                }
        tmp_path.replace(final_path)

    state[str(package_id)] = {'status': 'downloaded', 'path': str(final_path), 'size': final_path.stat().st_size, 'displayName': display_name, 'updatedAt': time.time()}
    return final_path


def cmd_list(args: argparse.Namespace) -> int:
    client = UnityAssetStore()
    purchases = save_catalog(client, args.catalog)
    for item in purchases:
        print(f"{item['packageId']}\t{item['displayName']}")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    client = UnityAssetStore()
    purchases = {int(item['packageId']): item for item in save_catalog(client, args.catalog)}
    package_id = int(args.package_id)
    if package_id not in purchases:
        raise SystemExit(f'Package {package_id} not in purchases')
    state = load_json(args.state, {})
    path = download_asset(client, package_id, purchases[package_id]['displayName'], args.dest, state)
    write_json(args.state, state)
    print(path)
    return 0


def cmd_download_all(args: argparse.Namespace) -> int:
    client = UnityAssetStore()
    purchases = save_catalog(client, args.catalog)
    if args.package_ids:
        wanted = {int(x) for x in args.package_ids.split(',') if x.strip()}
        purchases = [item for item in purchases if int(item['packageId']) in wanted]
    state = load_json(args.state, {})
    for item in purchases:
        package_id = int(item['packageId'])
        display_name = item['displayName']
        if args.skip_existing and str(package_id) in state and state[str(package_id)].get('status') == 'downloaded':
            continue
        try:
            print(f"START\t{package_id}\t{display_name}", flush=True)
            path = download_asset(client, package_id, display_name, args.dest, state)
            write_json(args.state, state)
            print(f"DONE\t{package_id}\t{path}", flush=True)
        except Exception as exc:
            state[str(package_id)] = {'status': 'error', 'displayName': display_name, 'error': str(exc), 'updatedAt': time.time()}
            write_json(args.state, state)
            print(f"ERROR\t{package_id}\t{display_name}\t{exc}", file=sys.stderr, flush=True)
            if args.stop_on_error:
                return 1
            time.sleep(3)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Unity Asset Store helper')
    sub = parser.add_subparsers(dest='cmd', required=True)

    list_p = sub.add_parser('list')
    list_p.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    list_p.set_defaults(func=cmd_list)

    dl_p = sub.add_parser('download')
    dl_p.add_argument('package_id', type=int)
    dl_p.add_argument('--dest', type=Path, default=Path('/data/src/github/games/unity/assetstore/downloads'))
    dl_p.add_argument('--state', type=Path, default=DEFAULT_STATE)
    dl_p.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    dl_p.set_defaults(func=cmd_download)

    all_p = sub.add_parser('download-all')
    all_p.add_argument('--package-ids', default='')
    all_p.add_argument('--dest', type=Path, default=Path('/data/src/github/games/unity/assetstore/downloads'))
    all_p.add_argument('--state', type=Path, default=DEFAULT_STATE)
    all_p.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    all_p.add_argument('--skip-existing', action='store_true')
    all_p.add_argument('--stop-on-error', action='store_true')
    all_p.set_defaults(func=cmd_download_all)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
