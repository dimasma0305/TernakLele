import os

# import validators.volgactf

CONFIG = {
    'DEBUG': os.getenv('DEBUG') == '1',

    'TEAMS': {
        f'Team #{i}': f'{2*i - 1:02d}'
        for i in range(1, 16)
    },
    # 'FLAG_FORMAT': r'CTF\.Moscow\{[a-zA-Z\.0-9_-]+\}',
    # 'FLAG_FORMAT': r'VolgaCTF{[\w-]*\.[\w-]*\.[\w-]*}',
    'FLAG_FORMAT': r'COMPFEST17{.*?}',

    # 'SYSTEM_PROTOCOL': 'ructf_http',
    # 'SYSTEM_URL': 'http://monitor.ructfe.org/flags',
    # 'SYSTEM_TOKEN': '275_17fc104dd58d429ec11b4a5e82041cd2',

    'SYSTEM_PROTOCOL': 'ailurus',
    'SYSTEM_URL': 'https://api.ctf-compfest.com',
    'TEAM_TOKEN': 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1ODk2ODMzMiwianRpIjoiYzY3Mzg5NzQtZTg2NC00ZjE3LTkyOTEtMWJmYmVkOTIzN2ZjIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ0ZWFtIjp7ImlkIjo4LCJuYW1lIjoiYXBhIHlhIGthPyJ9fSwibmJmIjoxNzU4OTY4MzMyLCJleHAiOjE3NTkwMTE1MzJ9.oq5hpSyTiOl7FVAnObP1Yl6NU915fuJGo4g8oMyYRct167VC819nTw3-7ZmU9V1QFe6pFnVfdz9TXyNPzoYlcA',

    # 'SYSTEM_HOST': '10.10.10.10',
    # 'SYSTEM_PORT': '31337',
    # 'SYSTEM_PROTOCOL': 'volgactf',
    # 'SYSTEM_VALIDATOR': 'volgactf',
    # 'SYSTEM_HOST': 'final.volgactf.ru',
    # 'SYSTEM_SERVER_KEY': validators.volgactf.get_public_key('https://final.volgactf.ru'),

    # this is for run.py
    'SOLVER_TIMEOUT': 60,
    'SUBMIT_GRACE_SECONDS': 5,
    'RUN_INTERVAL': 30,
    'WATCH_POLL': 2,
    'USE_THREADING': False,  # Set to False to run solvers synchronously (no threading)

    # The server will submit not more than SUBMIT_FLAG_LIMIT flags
    # every SUBMIT_PERIOD seconds. Flags received more than
    # FLAG_LIFETIME seconds ago will be skipped.
    'SUBMIT_FLAG_LIMIT': 100,
    'SUBMIT_PERIOD': 2,
    'FLAG_LIFETIME': 10 * 60,
    # 'FLAG_LIFETIME': 5 * 60,

    # VOLGA: Don't make more than INFO_FLAG_LIMIT requests to get flag info,
    # usually should be more than SUBMIT_FLAG_LIMIT
    # 'INFO_FLAG_LIMIT': 10,

    # Password for the web interface. This key will be excluded from config
    # before sending it to farm clients.
    # ########## DO NOT FORGET TO CHANGE IT ##########
    'SERVER_PASSWORD': os.getenv('SERVER_PASSWORD') or 'dimas123',

    # For all time-related operations
    'TIMEZONE': 'Europe/Moscow',
}
