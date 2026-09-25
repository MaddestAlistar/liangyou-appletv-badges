"""Native vector glyphs for the existing LiangYou badge system."""

def icon_paths(kind,c,slug):
    # 60 by 60 native vector glyph, centered inside the established icon circle.
    stroke=f'fill="none" stroke="{c}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"'
    if kind=='dolby': return f'<rect x="5" y="14" width="50" height="32" rx="3" {stroke}/><path d="M10 19v22h8c6 0 11-5 11-11s-5-11-11-11zm40 0h-8c-6 0-11 5-11 11s5 11 11 11h8z" fill="{c}"/>'
    if kind=='web': return f'<circle cx="28" cy="28" r="21" {stroke}/><path d="M7 28h42M28 7c-12 12-12 30 0 42M28 7c12 12 12 30 0 42M12 16h32M12 40h32" {stroke}/><path d="M45 34v18m-8-8 8 8 8-8" {stroke}/>'
    if kind=='disc': return f'<circle cx="30" cy="30" r="23" {stroke}/><circle cx="30" cy="30" r="6" {stroke}/><path d="M17 10c-7 5-10 10-10 18M43 50c7-5 10-10 10-18" {stroke}/>'
    if kind=='tv': return f'<rect x="6" y="13" width="48" height="32" rx="4" {stroke}/><path d="M30 45v8m-13 0h26M22 5l8 8 8-8" {stroke}/>'
    if kind=='sun': return f'<circle cx="30" cy="30" r="13" {stroke}/><path d="M30 4v8m0 36v8M4 30h8m36 0h8M12 12l6 6m24 24 6 6M12 48l6-6m24-24 6-6" {stroke}/>'
    if kind=='screen': return f'<rect x="4" y="13" width="52" height="35" rx="3" {stroke}/><path d="M8 7h44M8 54h44M10 20h9m-9 0v9m40-9h-9m9 0v9M10 42h9m-9 0v-9m40 9h-9m9 0v-9" {stroke}/>'
    if kind=='depth': return f'<path d="M30 8 5 21l25 13 25-13L30 8zM5 31l25 13 25-13M5 41l25 13 25-13" {stroke}/>'
    if kind=='speaker':
        if slug=='10':return f'<rect x="18" y="7" width="24" height="46" rx="4" {stroke}/><circle cx="30" cy="36" r="7" {stroke}/><circle cx="30" cy="19" r="3" {stroke}/>'
        if slug=='61':return ''.join(f'<rect x="{x}" y="{y}" width="8" height="11" rx="1.5" {stroke}/>' for x,y in [(6,10),(26,4),(46,10),(6,40),(26,46),(46,40)])+f'<circle cx="30" cy="30" r="6" {stroke}/><path d="M14 18 24 26m12 0 10-8M14 43l10-9m12 0 10 9" {stroke}/>'
        return f'<rect x="9" y="10" width="15" height="40" rx="3" {stroke}/><rect x="36" y="10" width="15" height="40" rx="3" {stroke}/><circle cx="16.5" cy="35" r="4.5" {stroke}/><circle cx="43.5" cy="35" r="4.5" {stroke}/><path d="M15 20h3m24 0h3" {stroke}/>'
    if kind=='wave': return f'<path d="M6 29v2m7-11v20m8-26v32m9-39v46m9-39v32m8-26v20m7-11v2" {stroke}/>'
    if kind=='glasses': return f'<rect x="3" y="19" width="23" height="25" rx="5" {stroke}/><rect x="34" y="19" width="23" height="25" rx="5" {stroke}/><path d="M26 28q4-5 8 0M3 23l4-10m50 10-4-10" {stroke}/>'
    if kind=='chip': return f'<rect x="14" y="14" width="32" height="32" rx="5" {stroke}/><rect x="21" y="21" width="18" height="18" rx="2" {stroke}/><path d="M22 6v8m8-8v8m8-8v8M22 46v8m8-8v8m8-8v8M6 22h8m-8 8h8m-8 8h8M46 22h8m-8 8h8m-8 8h8" {stroke}/>'
    if kind=='motion': return f'<circle cx="33" cy="32" r="19" {stroke}/><path d="M33 13V7m-7 0h14M33 32l9-10M3 22h9M0 32h10M3 42h9" {stroke}/>'
    if kind=='scissors': return f'<circle cx="13" cy="42" r="8" {stroke}/><circle cx="44" cy="42" r="8" {stroke}/><path d="M18 36 46 8M38 36 10 8" {stroke}/>'
    if kind=='extend': return f'<rect x="17" y="18" width="26" height="24" rx="3" {stroke}/><path d="M2 30h15m-9-8-8 8 8 8m35-8h15m-8-8 8 8-8 8" {stroke}/>'
    if kind=='sparkles': return f'<path d="M26 8l5 16 16 5-16 5-5 16-5-16-16-5 16-5 5-16zm23-4 2 7 7 2-7 2-2 7-2-7-7-2 7-2 2-7z" {stroke}/>'
    if kind=='repeat': return f'<path d="M48 22A21 21 0 0 0 10 20l-4 9M6 14v15h15M12 38a21 21 0 0 0 38 2l4-9m0 15V31H39" {stroke}/>'
    if kind=='check': return f'<path d="m30 5 21 9v17c0 10-12 18-21 24C21 49 9 41 9 31V14l21-9zM18 29l9 9 16-18" {stroke}/>'
    if kind=='criterion': return f'<circle cx="30" cy="30" r="23" {stroke}/><path d="M40 20a14 14 0 1 0 0 20" {stroke}/>'
    if kind=='link': return f'<path d="m25 17 7-7a13 13 0 0 1 18 18l-9 9a13 13 0 0 1-18 0M35 43l-7 7a13 13 0 0 1-18-18l9-9a13 13 0 0 1 18 0M20 40l20-20" {stroke}/>'
    if kind=='bw': return f'<circle cx="30" cy="30" r="23" {stroke}/><path d="M30 7a23 23 0 0 0 0 46z" fill="{c}"/>'
    if kind=='film': return f'<rect x="6" y="10" width="48" height="40" rx="3" {stroke}/><path d="M15 10v40m30-40v40M6 20h9m-9 10h9m-9 10h9m30-20h9m-9 10h9m-9 10h9" {stroke}/>'
    if kind=='language': return f'<path d="M6 11h48v32H32L20 53V43H6V11z" {stroke}/>'+pathtext('文',30,35,23,c,True)
    if kind.startswith('platform:'): return pathtext(kind.split(':',1)[1],30,39,24,c,True,maxwidth=47)
    return pathtext('HD',30,38,21,c,True)
