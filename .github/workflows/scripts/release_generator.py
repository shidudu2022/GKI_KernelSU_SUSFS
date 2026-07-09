#!/usr/bin/env python3
import json
import urllib.request
import ssl
import sys
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from config import KERNEL_VERSION


class ReleaseGenerator:
    def __init__(self):
        self.matrix_path = Path(__file__).parent.parent / "config" / "matrix.json"
        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def load_matrix(self) -> dict:
        with open(self.matrix_path, 'r') as f:
            return json.load(f)

    def _fetch_json(self, url: str) -> dict:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Python'})
            with urllib.request.urlopen(req, context=self.ssl_ctx) as response:
                return json.loads(response.read())
        except Exception:
            return {}

    def get_ksu_info(self) -> tuple:
        ksu_tag, ksu_commit = "latest", "unknown"
        tags = self._fetch_json("https://api.github.com/repos/SukiSU-Ultra/SukiSU-Ultra/git/refs/tags")
        if tags:
            ksu_tag = tags[-1]['ref'].split('/')[-1]
        ref = self._fetch_json("https://api.github.com/repos/SukiSU-Ultra/SukiSU-Ultra/git/ref/heads/main")
        if ref:
            ksu_commit = ref['object']['sha'][:7]
        return ksu_tag, ksu_commit

    def generate_body(self) -> str:
        matrix = self.load_matrix()
        ksu_tag, ksu_commit = self.get_ksu_info()
        configs = [f"- Android {k.split('-')[0].replace('android', '')} (Kernel {k.split('-')[1]})" for k in sorted(matrix.keys())]
        return '\n'.join([
            f"## GKI Kernel with SukiSU & SUSFS {KERNEL_VERSION}", "",
            "### SukiSU Info",
            f"- Tag: `{ksu_tag}`",
            f"- Commit: `{ksu_commit}`", "",
            "### Supported Configurations",
            *configs, "",
            "### Features",
            f"- SUSFS {KERNEL_VERSION}", "- Manual Syscall Hooks", "- Magic Mount Support", "- BBR Support", "- LZ4KD Support",
        ])

    def generate_single_body(
        self,
        android_version: str,
        kernel_version: str,
        sub_level: str,
        os_patch_level: str,
        kernelsu_version: str = "Stable(标准)",
        use_zram: bool = False,
        use_kpm: bool = True,
        build_timestamp: str = "",
    ) -> str:
        ksu_tag, ksu_commit = self.get_ksu_info()
        lines = [
            f"## GKI Kernel {android_version}-{kernel_version}.{sub_level}-{os_patch_level}",
            "",
            "### Build Info",
            f"- Android: `{android_version}`",
            f"- Kernel: `{kernel_version}`",
            f"- Sub Level: `{sub_level}`",
            f"- OS Patch: `{os_patch_level}`",
            f"- SUSFS: `{KERNEL_VERSION}`",
            f"- SukiSU: `{kernelsu_version}`",
            f"- SukiSU Tag: `{ksu_tag}`",
            f"- SukiSU Commit: `{ksu_commit}`",
            f"- ZRAM: `{'enabled' if use_zram else 'disabled'}`",
            f"- KPM: `{'enabled' if use_kpm else 'disabled'}`",
        ]
        if build_timestamp:
            lines.append(f"- Build Timestamp: `{build_timestamp}`")
        lines.extend([
            "",
            "### Files",
            "- `*-AnyKernel3.zip` — KernelSU 刷入包",
            "- `*-boot.img` — 原始 boot 镜像",
            "- `*-boot-gz.img` — gzip 压缩 boot",
            "- `*-boot-lz4.img` — lz4 压缩 boot",
            "- `SHA256SUMS.txt` — 文件校验",
        ])
        return '\n'.join(lines)

    def save_body(self, output_path: str = "RELEASE_BODY.md", **kwargs):
        body = self.generate_single_body(**kwargs) if kwargs else self.generate_body()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(body)
        print(body)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="生成 Release 说明")
    parser.add_argument("output", nargs="?", default="RELEASE_BODY.md")
    parser.add_argument("--android", default=None)
    parser.add_argument("--kernel", default=None)
    parser.add_argument("--sub-level", default=None)
    parser.add_argument("--os-patch", default=None)
    parser.add_argument("--ksu-version", default="Stable(标准)")
    parser.add_argument("--zram", action="store_true")
    parser.add_argument("--no-kpm", action="store_true")
    parser.add_argument("--build-timestamp", default="")
    args = parser.parse_args()

    gen = ReleaseGenerator()
    if args.android:
        gen.save_body(
            args.output,
            android_version=args.android,
            kernel_version=args.kernel,
            sub_level=args.sub_level,
            os_patch_level=args.os_patch,
            kernelsu_version=args.ksu_version,
            use_zram=args.zram,
            use_kpm=not args.no_kpm,
            build_timestamp=args.build_timestamp,
        )
    else:
        gen.save_body(args.output)
