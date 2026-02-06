from __future__ import annotations

import struct
import zlib
from pathlib import Path


def _save_png(path: Path, w: int, h: int, pixels: list[int]) -> None:
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(pixels[y * w * 3 : (y + 1) * w * 3])

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack("!I", len(data))
            + tag
            + data
            + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def _rect(w: int, h: int, color: tuple[int, int, int], bg: tuple[int, int, int] = (20, 20, 20)) -> list[int]:
    px = [bg[0], bg[1], bg[2]] * (w * h)
    for y in range(4, h - 4):
        for x in range(4, w - 4):
            i = (y * w + x) * 3
            px[i : i + 3] = list(color)
    return px


def _place(base: list[int], w: int, patch: list[int], pw: int, ph: int, ox: int, oy: int) -> list[int]:
    out = base[:]
    for y in range(ph):
        for x in range(pw):
            si = (y * pw + x) * 3
            di = ((oy + y) * w + (ox + x)) * 3
            out[di : di + 3] = patch[si : si + 3]
    return out


def create_mock_fixture_tree(base_dir: Path) -> tuple[Path, Path]:
    screens = base_dir / "screens"
    templates = base_dir / "templates"
    for d in [screens, templates / "home", templates / "erros", templates / "roleta"]:
        d.mkdir(parents=True, exist_ok=True)

    home = _rect(80, 40, (0, 200, 0))
    home_btn = _rect(60, 30, (200, 50, 0))
    conn = _rect(110, 35, (220, 0, 0))
    crash = _rect(100, 35, (120, 0, 120))

    _save_png(templates / "home" / "tela_home.png", 80, 40, home)
    _save_png(templates / "home" / "botao_home.png", 60, 30, home_btn)
    _save_png(templates / "erros" / "popup_erro_conexao.png", 110, 35, conn)
    _save_png(templates / "erros" / "app_crash.png", 100, 35, crash)
    _save_png(templates / "roleta" / "popup_roleta_disponivel.png", 90, 35, _rect(90, 35, (180, 180, 0)))
    _save_png(templates / "roleta" / "botao_roleta.png", 70, 30, _rect(70, 30, (0, 180, 180)))
    _save_png(templates / "roleta" / "botao_fechar.png", 50, 25, _rect(50, 25, (80, 80, 80)))

    w, h = 420, 300
    blank = [20, 20, 20] * (w * h)
    _save_png(screens / "screen_blank.png", w, h, blank)
    _save_png(screens / "screen_with_home.png", w, h, _place(blank, w, home, 80, 40, 160, 120))
    _save_png(screens / "screen_with_conn_error.png", w, h, _place(blank, w, conn, 110, 35, 140, 30))
    _save_png(screens / "screen_with_crash.png", w, h, _place(blank, w, crash, 100, 35, 150, 40))
    _save_png(screens / "screen_with_home_button.png", w, h, _place(blank, w, home_btn, 60, 30, 20, 240))
    home_and_button = _place(_place(blank, w, home, 80, 40, 160, 120), w, home_btn, 60, 30, 20, 240)
    _save_png(screens / "screen_home_and_button.png", w, h, home_and_button)
    _save_png(
        screens / "screen_with_roleta_popup.png",
        w,
        h,
        _place(blank, w, _rect(90, 35, (180, 180, 0)), 90, 35, 130, 50),
    )

    return screens, templates
