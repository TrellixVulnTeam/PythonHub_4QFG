"""Convert a Decimal Number to a Binary Number."""


def decimal_to_binary(num):

    """
        Convert a Integer Decimal Number to a Binary Number as str.
        >>> decimal_to_binary(0)
        '0b0'
        >>> decimal_to_binary(2)
        '0b10'
        >>> decimal_to_binary(7)
        '0b111'
        >>> decimal_to_binary(35)
        '0b100011'
        >>> # negatives work too
        >>> decimal_to_binary(-2)
        '-0b10'
        >>> # other floats will error
        >>> decimal_to_binary(16.16) # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: 'float' object cannot be interpreted as an integer
        >>> # strings will error as well
        >>> decimal_to_binary('0xfffff') # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: 'str' object cannot be interpreted as an integer
    """

    if type(num) == float:
        raise TypeError("'float' object cannot be interpreted as an integer")
    if type(num) == str:
        raise TypeError("'str' object cannot be interpreted as an integer")

    if num == 0:
        return "0b0"

    negative = False

    if num < 0:
        negative = True
        num = -num

    binary = []
    while num > 0:
        binary.insert(0, num % 2)
        num >>= 1

    if negative:
        return "-0b" + "".join(str(e) for e in binary)

    return "0b" + "".join(str(e) for e in binary)


if __name__ == "__main__":
    import doctest

    d = decimal_to_binary(12)
    print(d)

    doctest.testmod()
