import pytest

from smugmug_to_b2.util import Reader, ordered_zip
from typing import TypeVar


T = TypeVar('T')


def identity(x: T) -> T:
    return x


def test_reader_normal():
    reader = Reader([1, 2, 3], identity)
    assert 1 == reader.current
    reader.advance()
    assert 2 == reader.current
    reader.advance()
    assert 3 == reader.current
    reader.advance()
    assert None is reader.current


def test_reader_out_of_order():
    reader = Reader([2, 1], identity)
    with pytest.raises(AssertionError):
        reader.advance()


def test_ordered_zip_empty():
    assert [] == list(ordered_zip([], []))


def test_ordered_zip_only_left():
    assert [(1, None), (2, None)] == list(ordered_zip([1, 2], []))


def test_ordered_zip_only_right():
    assert [(None, 1), (None, 2)] == list(ordered_zip([], [1, 2]))


def test_ordered_zip_some_match():
    assert (
        [(1, None), (None, 2), (3, 3), (4, None), (None, 5), (6, 6)] ==
        list(ordered_zip([1, 3, 4, 6], [2, 3, 5, 6]))
    )


def test_ordered_zip_key():
    assert (
        [(0, 1), (2, 2), (5, 4)] ==
        list(ordered_zip([0, 2, 5], [1, 2, 4], lambda n: n // 2))
    )
