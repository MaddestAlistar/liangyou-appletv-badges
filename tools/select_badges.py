"""Reference post-match selector for client developers.

This module is NOT executed by imported badge JSON. A player must explicitly
integrate a stage like this after unioning matches for ONE selected MediaSource.
"""
from badge_rules import COMBOS, PRIORITIES, catalogue


def select_matched(slugs):
    pool = {s.removeprefix('ly9-').removeprefix('ly8-') for s in slugs}
    combos = [c[0] for c in COMBOS]
    result = []
    combo = next((c for c in COMBOS if c[0] in pool), None)
    if combo:
        result.append(combo[0])
    profiles = [p for p in ['dv-p5', 'dv-p7', 'dv-p8'] if p in pool]
    for family, order in PRIORITIES.items():
        if family == 'audio' and combo:
            continue
        if family == 'range':
            if combo and 'dolby-vision' in combo[1]:
                continue
            if profiles:
                result.append(profiles[0] if len(profiles) == 1 else 'dolby-vision')
                continue
        match = next((slug for slug in order if slug in pool), None)
        if match:
            result.append(match)
    handled = set(combos + ['dv-p5', 'dv-p7', 'dv-p8'])
    for order in PRIORITIES.values():
        handled.update(order)
    result.extend(b['slug'] for b in catalogue('all')
                  if b['slug'] in pool and b['slug'] not in handled)
    return result
