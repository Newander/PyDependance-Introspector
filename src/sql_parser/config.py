specificWords = (
    'begin', 'commit',
    'drop', 'create', 'alter',
    'with',
    'select', 'update', 'delete', 'insert',
    'join', 'window',
    'where',
    'group',
    'union',
    'order',
    'limit', 'offset',
)  # todo: here

ourTablesSignal = (
    'begin', 'commit',
    'drop', 'create', 'alter',
    'update', 'delete', 'insert',
)
spaces = '\n \t'
curves = '()'
separators = ',;'
skips = spaces + curves + separators
significant_s = curves + separators
joinWords = ('inner', 'outer', 'join', 'left', 'right')
