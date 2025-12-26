# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

VERSION_FILE = Path(__file__).parent / "VERSION"
_raw_version = VERSION_FILE.read_text().strip()
# version always contain only release number like 0.0.1
__version__ = ".".join(_raw_version.split(".")[:3])
# version tuple always contains only integer parts, like (0, 0, 1)
__version_tuple__ = tuple(map(int, __version__.split(".")))  # noqa: RUF048
