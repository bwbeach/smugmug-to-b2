#
# File: util
#

class Reader:
    """
    Holds the current value from an iterable in '.current'.
    None indicates no more values.

    advance() moves to the next value.
    """
    def __init__(self, iterable, key):
        self._iterator = iter(iterable)
        self.current = self._next()
        self.key = key

    def advance(self):
        """
        Moves to the next value.  Should only be called if there is a current value.
        """
        assert self.current is not None
        new_current = self._next()
        assert new_current is None or self.key(self.current) < self.key(new_current), (self.current, new_current)
        self.current = new_current

    def _next(self):
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
