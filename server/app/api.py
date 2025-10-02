import importlib
import time
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta

from flask import request, jsonify, Blueprint
from prometheus_client import Counter, Gauge

import auth
import reloader
from database import db_cursor
from models import FlagStatus

api = Blueprint('api', __name__, url_prefix='/api')

def parse_time_string(time_str):
    """
    Parse various time formats and return Unix timestamp.
    Supports:
    - ISO formats: 2024-01-01, 2024-01-01T10:30:00, 2024-01-01 10:30:00
    - Timezone offsets: +8, +1, +0, -5, +05:30, etc.
    - Relative times: 1h, 2d, 30m, 1w (hours, days, minutes, weeks ago)
    - Natural language: yesterday, today, now
    - Unix timestamp: 1640995200
    """
    if not time_str or not time_str.strip():
        return None
    
    time_str = time_str.strip()
    now = datetime.now()
    
    # Try relative time formats first (e.g., "1h", "2d", "30m", "1w")
    relative_match = re.match(r'^(\d+)([hdmw])$', time_str.lower())
    if relative_match:
        value = int(relative_match.group(1))
        unit = relative_match.group(2)
        
        if unit == 'h':  # hours
            return round((now - timedelta(hours=value)).timestamp())
        elif unit == 'd':  # days
            return round((now - timedelta(days=value)).timestamp())
        elif unit == 'm':  # minutes
            return round((now - timedelta(minutes=value)).timestamp())
        elif unit == 'w':  # weeks
            return round((now - timedelta(weeks=value)).timestamp())
    
    # Try natural language
    if time_str.lower() in ['now', 'today']:
        return round(now.timestamp())
    elif time_str.lower() == 'yesterday':
        return round((now - timedelta(days=1)).timestamp())
    
    # Try Unix timestamp (numeric)
    try:
        timestamp = float(time_str)
        if timestamp > 0:
            return round(timestamp)
    except ValueError:
        pass
    
    # Try timezone offset formats (e.g., "+8", "+1", "+0", "-5", "+05:30")
    timezone_match = re.match(r'^([+-]?\d{1,2})(?::(\d{2}))?$', time_str)
    if timezone_match:
        hours = int(timezone_match.group(1))
        minutes = int(timezone_match.group(2) or 0)
        
        # Calculate offset in hours
        offset_hours = hours + (minutes / 60.0)
        
        # Apply timezone offset to current time
        offset_time = now + timedelta(hours=offset_hours)
        return round(offset_time.timestamp())
    
    # Try various datetime formats with timezone support
    formats = [
        # ISO formats with timezone
        '%Y-%m-%d %H:%M:%S%z',     # 2024-01-01 10:30:00+08:00
        '%Y-%m-%d %H:%M%z',        # 2024-01-01 10:30+08:00
        '%Y-%m-%dT%H:%M:%S%z',     # 2024-01-01T10:30:00+08:00
        '%Y-%m-%dT%H:%M%z',        # 2024-01-01T10:30+08:00
        '%Y-%m-%dT%H:%M:%S.%f%z',  # 2024-01-01T10:30:00.000+08:00
        '%Y-%m-%dT%H:%M:%SZ',      # 2024-01-01T10:30:00Z
        '%Y-%m-%dT%H:%M:%S.%fZ',   # 2024-01-01T10:30:00.000Z
        '%Y-%m-%dT%H:%MZ',         # 2024-01-01T10:30Z
        # Standard ISO formats
        '%Y-%m-%d %H:%M:%S',       # 2024-01-01 10:30:00
        '%Y-%m-%d %H:%M',          # 2024-01-01 10:30
        '%Y-%m-%d',                # 2024-01-01
        '%Y-%m-%dT%H:%M:%S',       # 2024-01-01T10:30:00
        '%Y-%m-%dT%H:%M',          # 2024-01-01T10:30
        '%Y-%m-%d %H:%M:%S.%f',    # 2024-01-01 10:30:00.000
        # Alternative date formats
        '%d/%m/%Y %H:%M:%S',       # 01/01/2024 10:30:00
        '%d/%m/%Y %H:%M',          # 01/01/2024 10:30
        '%d/%m/%Y',                # 01/01/2024
        '%m/%d/%Y %H:%M:%S',       # 01/01/2024 10:30:00
        '%m/%d/%Y %H:%M',          # 01/01/2024 10:30
        '%m/%d/%Y',                # 01/01/2024
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return round(dt.timestamp())
        except ValueError:
            continue
    
    # If all parsing attempts fail, raise an error
    raise ValueError(f"Unable to parse time format: '{time_str}'. Supported formats: ISO dates, timezone offsets (+8, +1, +0, -5, +05:30), relative times (1h, 2d, 30m, 1w), natural language (now, today, yesterday), Unix timestamps")

FLAGS_RECEIVED = Counter(
    'flags_received',
    'Number of flags received',
    ['sploit', 'team'],
)

TOTAL_TEAMS = Gauge('total_teams', 'Number of teams')
TOTAL_TEAMS.set_function(lambda: len(reloader.get_config()['TEAMS']))


@api.route('/get_config')
@auth.auth_required
def get_config():
    config = reloader.get_config()
    return jsonify({
        key: value
        for key, value in config.items()
        if 'PASSWORD' not in key and 'TOKEN' not in key
    })


@api.route('/post_flags', methods=['POST'])
@auth.auth_required
def post_flags():
    flags = request.json
    cur_time = round(time.time())
    config = reloader.get_config()

    if config.get('SYSTEM_VALIDATOR'):
        validator_module = importlib.import_module('validators.' + config['SYSTEM_VALIDATOR'])
        flags = validator_module.validate_flags(flags, config)

    rows = [
        (
            flag['flag'],
            flag['sploit'],
            flag['team'],
            cur_time,
            FlagStatus.QUEUED.name,
        )
        for flag in flags
    ]

    with db_cursor() as (conn, curs):
        curs.executemany(
            """
            INSERT OR IGNORE INTO flags (flag, sploit, team, time, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()

    for flag in flags:
        FLAGS_RECEIVED.labels(sploit=flag['sploit'], team=flag['team']).inc()

    return ''


@api.route('/filter_flags', methods=['GET'])
@auth.auth_required
def get_filtered_flags():
    filters = request.args

    conditions = []
    for column in ['sploit', 'status', 'team']:
        value = filters.get(column)
        if value:
            conditions.append((f'{column} = ?', value))

    for column in ['flag', 'checksystem_response']:
        value = filters.get(column)
        if value:
            conditions.append((f'INSTR(LOWER({column}), ?) > 0', value.lower()))

    for column in ['since', 'until']:
        value = filters.get(column, '').strip()
        if value:
            try:
                timestamp = parse_time_string(value)
                if timestamp is not None:
                    sign = '>=' if column == 'since' else '<='
                    conditions.append((f'time {sign} ?', timestamp))
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

    page = int(filters.get('page', 1))
    if page < 1:
        raise ValueError('Invalid page')

    page_size = int(filters.get('page_size', 30))
    if page_size < 1 or page_size > 100:
        raise ValueError('Invalid page size')

    if conditions:
        chunks, values = list(zip(*conditions))
        conditions_sql = 'WHERE ' + ' AND '.join(chunks)
        conditions_args = list(values)
    else:
        conditions_sql = ''
        conditions_args = []

    sql = 'SELECT * FROM flags ' + conditions_sql + ' ORDER BY time DESC LIMIT ? OFFSET ?'
    args = conditions_args + [page_size, page_size * (page - 1)]

    count_sql = 'SELECT COUNT(*) as cnt FROM flags ' + conditions_sql
    count_args = conditions_args

    with db_cursor(True) as (_, curs):
        curs.execute(sql, args)
        flags = curs.fetchall()
        curs.execute(count_sql, count_args)
        total_count = curs.fetchone()['cnt']

    response = {
        'flags': list(map(dict, flags)),
        'page_size': page_size,
        'page': page,
        'total': total_count,
    }

    return jsonify(response)


@api.route('/filter_config', methods=['GET'])
@auth.auth_required
def get_filter_config():
    distinct_values = {}
    with db_cursor(True) as (_, curs):
        for column in ['sploit', 'status', 'team']:
            curs.execute(f'SELECT DISTINCT {column} FROM flags ORDER BY {column}')
            rows = curs.fetchall()
            distinct_values[column] = [item[column] for item in rows]

    config = reloader.get_config()

    server_tz_name = time.strftime('%Z')
    if server_tz_name.startswith('+'):
        server_tz_name = 'UTC' + server_tz_name

    response = {
        'filters': distinct_values,
        'flag_format': config['FLAG_FORMAT'],
        'server_tz': server_tz_name
    }

    return jsonify(response)

@api.route('/summary', methods=['GET'])
@auth.auth_required
def summary():
    filters = request.args

    conditions = []
    for column in ['sploit', 'status', 'team']:
        value = filters.get(column)
        if value:
            conditions.append((f'{column} = ?', value))

    for column in ['flag', 'checksystem_response']:
        value = filters.get(column)
        if value:
            conditions.append((f'INSTR(LOWER({column}), ?) > 0', value.lower()))

    for column in ['since', 'until']:
        value = filters.get(column, '').strip()
        if value:
            try:
                timestamp = parse_time_string(value)
                if timestamp is not None:
                    sign = '>=' if column == 'since' else '<='
                    conditions.append((f'time {sign} ?', timestamp))
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

    # result for last x seconds
    for column in ['last']:
        value = filters.get(column, '').strip()
        if value:
            try:
                timestamp = parse_time_string(value)
                if timestamp is not None:
                    sign = '>='
                    conditions.append((f'time {sign} ?', timestamp))
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

    if conditions:
        chunks, values = list(zip(*conditions))
        conditions_sql = 'WHERE ' + ' AND '.join(chunks)
        conditions_args = list(values)
    else:
        conditions_sql = ''
        conditions_args = []

    sql = 'SELECT * FROM flags ' + conditions_sql
    args = conditions_args

    with db_cursor(True) as (_, curs):
        curs.execute(sql, args)
        flags = curs.fetchall()

    result = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    response = filters.get('response','')
    for item in flags:
        key = item['checksystem_response'][:64] if response else item['status']
        result[item['sploit']][item['team']][key] += 1

    teams = reloader.get_config()['TEAMS']
    sploits=[]
    for sploit in result:
        tmp={}
        tmp['sploit_name'] = sploit
        tmp['teams']=[]
        for team in teams:
            if team not in result[sploit]:
                tmp['teams'].append({
                    'team': team,
                    'team_status': 'not status'
                })
        for team in result[sploit]:
            output = ''
            for key, value in result[sploit][team].items():
                output += f'{key}: {value}\n'
            tmp['teams'].append({
                'team': team,
                'team_status': output
            })
        sploits.append(tmp)

    return jsonify(sploits)

@api.route('/teams', methods=['GET'])
@auth.auth_required
def get_teams():
    teams = reloader.get_config()['TEAMS']
    response = list(map(
        lambda x: {'name': x[0], 'address': x[1]},
        teams.items(),
    ))
    return jsonify(response)


@api.route('/chart-data', methods=['GET'])
@auth.auth_required
def get_chart_data():
    """
    RESTful endpoint for fetching chart data showing flag status breakdown by team.
    Returns all flag data without time filtering.
    """
    
    with db_cursor(True) as (_, curs):
        # Get flag counts by team and status
        curs.execute("""
            SELECT team, status, COUNT(*) as count 
            FROM flags 
            GROUP BY team, status
            ORDER BY team, status
        """)
        
        results = curs.fetchall()
        
        # Organize data by team
        team_data = {}
        status_types = set()
        
        for row in results:
            team = row['team']
            status = row['status']
            count = row['count']
            
            if team not in team_data:
                team_data[team] = {}
            
            team_data[team][status] = count
            status_types.add(status)
        
        # Convert to chart format
        teams = list(team_data.keys())
        status_list = sorted(list(status_types))
        
        # Define colors for different statuses
        status_colors = {
            'ACCEPTED': '#4CAF50',    # Green
            'REJECTED': '#F44336',    # Red
            'QUEUED': '#FF9800',      # Orange
            'SKIPPED': '#9E9E9E'      # Grey
        }
        
        # Create series data for stacked bar chart
        series = []
        for status in status_list:
            data = []
            for team in teams:
                data.append(team_data[team].get(status, 0))
            
            series.append({
                'name': status.title(),
                'data': data,
                'color': status_colors.get(status, '#2196F3')  # Default blue
            })
        
        return jsonify({
            'type': 'bar',
            'title': 'Flag Status by Team',
            'xAxis': teams,
            'series': series
        })


@api.route('/content-hash', methods=['GET'])
@auth.auth_required
def get_content_hash():
    """
    Get content hashes for flags and chart data to enable auto-refresh functionality.
    Returns MD5 hashes of the current data state.
    """
    
    with db_cursor(True) as (_, curs):
        # Get hash for flags data
        curs.execute("SELECT COUNT(*) as count, MAX(time) as max_time FROM flags")
        flags_meta = curs.fetchone()
        flags_hash_data = f"{flags_meta['count']}_{flags_meta['max_time'] or 0}"
        flags_hash = hashlib.md5(flags_hash_data.encode()).hexdigest()
        
        # Get hash for chart data (team status counts)
        curs.execute("""
            SELECT team, status, COUNT(*) as count 
            FROM flags 
            GROUP BY team, status
            ORDER BY team, status
        """)
        chart_results = curs.fetchall()
        chart_hash_data = json.dumps([dict(row) for row in chart_results], sort_keys=True)
        chart_hash = hashlib.md5(chart_hash_data.encode()).hexdigest()
        
        return jsonify({
            'flags_hash': flags_hash,
            'chart_hash': chart_hash,
            'timestamp': int(time.time())
        })
