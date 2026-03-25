"""Общие утилиты для UI."""


def slider_value_for_step(val: int, min_v: int, max_v: int, step: int) -> int:
    """Приводит value к допустимому по сетке min_v + n*step (убирает предупреждение Streamlit о values/step/min/max)."""
    if step <= 0:
        return max(min_v, min(max_v, int(val)))
    n_max = (max_v - min_v) // step
    valid_max = min_v + n_max * step
    clamped = max(min_v, min(valid_max, int(val)))
    n = round((clamped - min_v) / step)
    return min_v + n * step
