# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations


def on_page_content(
    html,  # noqa: ARG001
    page,
    **kwargs,  # noqa: ARG001
):
    # https://github.com/mkdocs/mkdocs/issues/3532
    # https://github.com/pypa/hatch/pull/1239
    if title := page._title_from_render:  # noqa: SLF001
        page.meta["title"] = title
