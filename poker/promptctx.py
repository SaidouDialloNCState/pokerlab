PROMPT_CTX = {'hole': None, 'board': None, 'config': None, 'stacks': None}
def record_prompt_context(hole, board, config, stacks):
    PROMPT_CTX['hole'] = hole
    PROMPT_CTX['board'] = board
    PROMPT_CTX['config'] = config
    PROMPT_CTX['stacks'] = stacks
def get_prompt_context():
    return PROMPT_CTX
