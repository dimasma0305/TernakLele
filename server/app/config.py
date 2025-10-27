import os

# import validators.volgactf

CONFIG = {
    'DEBUG': os.getenv('DEBUG') == '1',

    'TEAMS': {
        f'Team #{i}-{2*i - 1:02d}': f'{10 + i:02d}'
        for i in range(1, 28)
    },
    # 'FLAG_FORMAT': r'CTF\.Moscow\{[a-zA-Z\.0-9_-]+\}',
    # 'FLAG_FORMAT': r'VolgaCTF{[\w-]*\.[\w-]*\.[\w-]*}',
    'FLAG_FORMAT': r'flag{.*?}',

    # 'SYSTEM_PROTOCOL': 'ructf_http',
    # 'SYSTEM_URL': 'http://monitor.ructfe.org/flags',
    # 'SYSTEM_TOKEN': '275_17fc104dd58d429ec11b4a5e82041cd2',

    'SYSTEM_PROTOCOL': 'xctf',
    'SYSTEM_URL': 'http://10.2.65.1',
    'SYSTEM_TOKEN': 'f330700f0498bdc5a265c716b9f61b0e',
    'RACE_ID': 'b2a01b4b88df2f76b05bbc1e4e50b2f7',

    # 'SYSTEM_HOST': '10.10.10.10',
    # 'SYSTEM_PORT': '31337',
    # 'SYSTEM_PROTOCOL': 'volgactf',
    # 'SYSTEM_VALIDATOR': 'volgactf',
    # 'SYSTEM_HOST': 'final.volgactf.ru',
    # 'SYSTEM_SERVER_KEY': validators.volgactf.get_public_key('https://final.volgactf.ru'),

    # The server will submit not more than SUBMIT_FLAG_LIMIT flags
    # every SUBMIT_PERIOD seconds. Flags received more than
    # FLAG_LIFETIME seconds ago will be skipped.
    'SUBMIT_FLAG_LIMIT': 100,
    'SUBMIT_PERIOD': 2,
    'FLAG_LIFETIME': 10 * 60,
    # 'FLAG_LIFETIME': 5 * 60,


    # Configuration keys (in CONFIG) that are used/added:
    #  - RUN_INTERVAL (seconds, default 30)
    #  - WATCH_POLL (seconds, default 2)
    #  - SOLVER_TIMEOUT (seconds, default 60)
    #  - SUBMIT_FLAG_LIMIT (int) - forwarded to get_fair_share
    #  - USE_THREADING (bool) - when True each solver will run attacks against teams concurrently; when False each solver will run teams sequentially
    #  - SOLVER_RETRIES (int, default 1) - retries for failed solver runs
    #  - SOLVER_THREADS_PER_SOLVER (int) - max workers per solver executor
    #  - MAX_CONCURRENT_ATTACKS (int, default 50) - global limit on concurrent attacks
    'RUN_INTERVAL': 30,
    'WATCH_POLL': 2,
    'SOLVER_TIMEOUT': 60,
    'SUBMIT_FLAG_LIMIT': 100,
    'USE_THREADING': True,
    'SOLVER_RETRIES': 1,
    'SOLVER_THREADS_PER_SOLVER': 2,
    'MAX_CONCURRENT_ATTACKS': 50,

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
