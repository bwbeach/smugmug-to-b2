#
# File: util
#

from typing import Callable, Generic, Iterable, Iterator, Union, TypeVar


K = TypeVar('K')
T = TypeVar('T')


class Reader(Generic[T, K]):
    """
    Holds the current value from an iterable in '.current'.
    None indicates no more values.

    advance() moves to the next value.
    """
    _iterator: Iterator[T]
    _current: Union[T, None]
    _key: Callable[[T], K]

    def __init__(self, iterable: Iterable[T], key: Callable[[T], K]):
        self._iterator = iter(iterable)
        self._current = self._next()
        self._key = key

    @property
    def current(self) -> T:
        return self._current

    def advance(self) -> None:
        """
        Moves to the next value.  Should only be called if there is a current value.
        """
        assert self._current is not None
        new_current = self._next()
        assert new_current is None or self._key(self._current) < self._key(new_current), (self._current, new_current)
        self._current = new_current

    def _next(self) -> Union[T, None]:
        """
        Returns the next value from the iterator, or None if there
        are no more values.
        """
        try:
            return next(self._iterator)
        except StopIteration:
            return None


def ordered_zip(iterable_a, iterable_b, key=None):
    """
    Zips two iterables, matching keys.

    The inputs must be sorted.  There will be one pair generated for each
    key.  The value on one side or the other may be None, indicating that
    the input didn't have a value with that key.
    """

    # Default is that the items themselves are the keys
    key = key or (lambda x: x)

    # Make a reader for each of the inputs to hold the current value.
    a = Reader(iterable_a, key)
    b = Reader(iterable_b, key)

    while a.current is not None or b.current is not None:
        if a.current is None:
            yield None, b.current
            b.advance()
        elif b.current is None:
            yield a.current, None
            a.advance()
        else:
            key_a = key(a.current)
            key_b = key(b.current)
            # print()
            # print('A: ' + key_a)
            # print('B: ' + key_b)
            if key_a < key_b:
                yield a.current, None
                a.advance()
            elif key_a == key_b:
                yield a.current, b.current
                a.advance()
                b.advance()
            else:
                yield None, b.current
                b.advance()
