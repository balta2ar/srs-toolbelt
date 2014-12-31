from io import StringIO


class Printer(object):
    """
    Has ref to:
        - token table
        - colorscheme table

    Knows how to:
        - mix colors with content

    Does not know:
        - anything about layout
    """
    def __init__(self, colorscheme=None):
        self._buffer = StringIO()
        self._colorscheme = colorscheme

    def setup(self, token_table):
        self._token_table = token_table

    def reset(self):
        self._buffer.close()
        self._buffer = StringIO()

    def produce(self, token, value=None, fmt=u'{0}', num=1):
        if value is None:
            value = self._token_table.get(token)
        if value is None:
            raise ValueError('Token {0} is missing from token table'
                             .format(token))
        return fmt.format(value) * num

    def swallow(self, text):
        if isinstance(text, list):
            return [self.swallow(x) for x in text]
        self._buffer.write(text)

    def spew(self, token, value=None, fmt=u'{0}', num=1):
        self.swallow(self.produce(token, value, fmt, num))

    def getvalue(self):
        return self._buffer.getvalue()

    def _get_position(self):
        """TEMPORARILY NOT USED"""
        lines = self.getvalue().splitlines()
        if not len(lines):
            return 0, 0
        return len(lines), len(lines[-1])

    def get_column(self):
        """TEMPORARILY NOT USED"""
        _, col = self._get_position()
        return col

    def get_row(self):
        """TEMPORARILY NOT USED"""
        # TODO: this gets broken when colored printer is on
        row, _ = self._get_position()
        return row


class ColoredPrinter(Printer):
    def produce(self, token, value=None, fmt=u'{0}', num=1):
        result = super(ColoredPrinter, self).produce(
            token, value, fmt, num)
        color = self._colorscheme.get(token)
        if color is None:
            return result
        # On how to process escape sequences in strings, see:
        # http://stackoverflow.com/a/4020824/258421
        return unicode(color.decode('string_escape')).format(result)
