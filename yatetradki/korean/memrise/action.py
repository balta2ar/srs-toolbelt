from yatetradki.korean.memrise.types import DiffActionCreateLevel
from yatetradki.korean.memrise.types import DiffActionChangeLevel
from yatetradki.korean.memrise.types import DiffActionDeleteLevel
from yatetradki.korean.memrise.types import DiffActionCreateWord
from yatetradki.korean.memrise.types import DiffActionChangeWord
from yatetradki.korean.memrise.types import DiffActionDeleteWord


def contains_deletions(actions):
    for action in actions:
        if isinstance(action, (DiffActionDeleteLevel, DiffActionDeleteWord)):
            return True
    return False


def pretty_print_action(action):
    if isinstance(action, DiffActionCreateLevel):
        return '+#%s' % action.level_name

    if isinstance(action, DiffActionChangeLevel):
        return '*#%s ===> #%s' % (action.level_name, action.new_level_name)

    if isinstance(action, DiffActionDeleteLevel):
        return '-#%s' % action.level_name

    if isinstance(action, DiffActionCreateWord):
        return '+%s; %s' % (action.pair.word, action.pair.meaning)

    if isinstance(action, DiffActionChangeWord):
        return '*%s; %s ===> %s; %s' % (
            action.old_pair.word,
            action.old_pair.meaning,
            action.new_pair.word,
            action.new_pair.meaning)

    if isinstance(action, DiffActionDeleteWord):
        return '-%s; %s' % (action.pair.word, action.pair.meaning)

    return 'Unknown action: %s' % action


def pretty_print_actions(actions):
    return '\n'.join(map(pretty_print_action, actions))
