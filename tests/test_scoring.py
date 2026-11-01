import os
import sys
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIENT_DIR = os.path.join(ROOT_DIR, "client")
SHARED_DIR = os.path.join(ROOT_DIR, "shared")

for p in [CLIENT_DIR, os.path.join(CLIENT_DIR, "logic"), SHARED_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from scoring import check_answer, get_unit_options, get_key_specs, get_quiz_specs


def test_check_answer_number_exact_and_tolerance():
    spec = {"name": "Мощность", "type": "number", "answer": "22", "unit": "Вт", "tolerance": 5}
    assert check_answer(spec, "22", "Вт") is True
    assert check_answer(spec, "20", "Вт") is True
    assert check_answer(spec, "27", "Вт") is True
    assert check_answer(spec, "30", "Вт") is False
    assert check_answer(spec, "22", "кВт") is False  # Wrong unit


def test_check_answer_range():
    spec = {"name": "Диапазон", "type": "range", "answer": "390-645", "unit": "МГц"}
    assert check_answer(spec, "390-645", "МГц") is True
    assert check_answer(spec, "391-644", "МГц") is True  # Within +-1
    assert check_answer(spec, "380-645", "МГц") is False


def test_check_answer_choice():
    spec = {"name": "Модуляция", "type": "choice", "answer": "QPSK", "options": ["BPSK", "QPSK"]}
    assert check_answer(spec, "QPSK") is True
    assert check_answer(spec, "qpsk") is True  # Case insensitive
    assert check_answer(spec, "BPSK") is False


def test_check_answer_invalid_inputs():
    spec = {"name": "Мощность", "type": "number", "answer": "22", "unit": "Вт", "tolerance": 0}
    assert check_answer(spec, "") is False
    assert check_answer(spec, "abc", "Вт") is False
    assert check_answer(spec, None, "Вт") is False
