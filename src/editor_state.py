"""Autosaved, source/page-specific region drafts with bounded undo history."""
import hashlib
from copy import deepcopy
from pathlib import Path
from .config import MANIFESTS
from .manifest_manager import read, write

def draft_path(form, page, layout, directory=MANIFESTS):
    identity = f'{Path(form).resolve()}|{page}|{layout}'
    return Path(directory) / ('draft_' + hashlib.sha256(identity.encode()).hexdigest()[:24] + '.json')

def load_draft(path, initial):
    return read(path) if Path(path).exists() else {'regions': deepcopy(initial), 'history': [], 'extracted': None}

def update_draft(path, state, regions):
    state = deepcopy(state)
    if state['regions'] != regions:
        state['history'] = (state['history'] + [state['regions']])[-20:]
        state['regions'] = deepcopy(regions)
    write(path, state)
    return state

def undo_draft(path):
    state = read(path)
    if state.get('history'):
        state['regions'] = state['history'].pop()
        write(path, state)
    return state

def mark_extracted(path):
    state = read(path)
    state['extracted'] = deepcopy(state['regions'])
    write(path, state)

def is_dirty(state):
    return state['regions'] != state.get('extracted')
