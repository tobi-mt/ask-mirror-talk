import re, os, sys

files = ['ask-mirror-talk.php', 'functions.php', 'answer-archive-template.php']
for fname in files:
    try:
        src = open(fname).read()
        opens = src.count('{')
        closes = src.count('}')
        status = 'OK' if opens == closes else 'MISMATCH'
        print(f'{fname}: open={opens} close={closes} {status}')
    except FileNotFoundError:
        print(f'{fname}: NOT FOUND')

icons = ['pwa-icon-512.png','pwa-icon-192.png','pwa-icon-180.png','pwa-icon-167.png','pwa-icon-152.png','pwa-icon.svg']
for icon in icons:
    print(f'icon {icon}: {"OK" if os.path.exists(icon) else "MISSING"}')

# Check style.css version
ver_line = [l for l in open('style.css') if 'Version:' in l]
print(f'style.css version: {ver_line[0].strip() if ver_line else "NOT FOUND"}')

# Generator scripts that should not be in ZIP
for f in sorted(os.listdir('.')):
    if f.endswith('.py'):
        print(f'WARNING .py present: {f}')
