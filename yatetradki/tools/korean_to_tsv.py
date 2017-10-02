"""
This script converts sample Korean-Russian sentences from format A to format B.

In Format A the korean part is the line that contains at least one Hangul
character. Russian parts do not contain Hangul.

Format A:

사업가. 치약.
Предприниматель. Зубная паста.

Format B (tsv):

korean\trussian

After conversion:

Front: 사업가. 치약.
Back: Предприниматель. Зубная паста.

"""

