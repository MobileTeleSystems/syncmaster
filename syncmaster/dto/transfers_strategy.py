# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Strategy:
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> Strategy:
        strategy_classes = {
            "full": FullStrategy,
            "incremental": IncrementalStrategy,
        }

        strategy_type = data.get("type")
        if strategy_type not in strategy_classes:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        return strategy_classes[strategy_type](**data)


@dataclass
class FullStrategy(Strategy):
    pass


@dataclass
class IncrementalStrategy(Strategy):
    increment_by: str
