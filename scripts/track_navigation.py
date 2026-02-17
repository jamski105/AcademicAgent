#!/usr/bin/env python3
"""
Navigation Session Tracker for DBIS Proxy Mode
Tracks browser navigation to enforce DBIS-first policy

Usage:
  python3 scripts/track_navigation.py "https://dbis.ur.de" session.json
  python3 scripts/track_navigation.py "https://ieeexplore.ieee.org" session.json
"""

import sys
import json
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime


def load_session(session_file: Path) -> dict:
    """Load existing session or create new one"""
    if session_file.exists():
        with open(session_file, 'r') as f:
            return json.load(f)
    else:
        return {
            'session_active': False,
            'started_from_dbis': False,
            'navigation_count': 0,
            'navigation_history': [],
            'first_url': None,
            'created_at': datetime.now().isoformat()
        }


def save_session(session: dict, session_file: Path):
    """Save session to file"""
    session['last_updated'] = datetime.now().isoformat()
    with open(session_file, 'w') as f:
        json.dump(session, f, indent=2)


def is_dbis_domain(url: str) -> bool:
    """Check if URL is a DBIS domain"""
    try:
        hostname = urlparse(url).hostname
        dbis_domains = ['dbis.ur.de', 'dbis.de', 'www.dbis.de']
        return any(hostname == domain or hostname.endswith('.' + domain)
                   for domain in dbis_domains)
    except:
        return False


def track_navigation(url: str, session_file: Path) -> dict:
    """
    Track navigation and update session

    Returns session info with status
    """
    session = load_session(session_file)

    # Check if this is first navigation
    if not session['session_active']:
        # First navigation MUST be to DBIS
        if is_dbis_domain(url):
            session['session_active'] = True
            session['started_from_dbis'] = True
            session['first_url'] = url
            session['navigation_count'] = 1
            session['navigation_history'] = [
                {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'is_dbis': True,
                    'navigation_number': 1
                }
            ]
            save_session(session, session_file)
            return {
                'status': 'session_started',
                'message': 'Navigation session started from DBIS',
                'session': session
            }
        else:
            # First navigation to non-DBIS domain → ERROR
            return {
                'status': 'error',
                'message': f'First navigation must be to DBIS. Attempted: {url}',
                'session': session
            }

    # Subsequent navigation
    session['navigation_count'] += 1
    session['navigation_history'].append({
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'is_dbis': is_dbis_domain(url),
        'navigation_number': session['navigation_count']
    })

    # Limit history size (keep last 50)
    if len(session['navigation_history']) > 50:
        session['navigation_history'] = session['navigation_history'][-50:]

    save_session(session, session_file)

    return {
        'status': 'tracked',
        'message': f'Navigation tracked (#{session["navigation_count"]})',
        'session': session
    }


def reset_session(session_file: Path):
    """Reset session (new research session)"""
    if session_file.exists():
        session_file.unlink()
    return {
        'status': 'reset',
        'message': 'Session reset'
    }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Navigation Session Tracker')
    parser.add_argument('url', nargs='?', help='URL being navigated to')
    parser.add_argument('session_file', help='Path to session file')
    parser.add_argument('--reset', action='store_true', help='Reset session')
    parser.add_argument('--status', action='store_true', help='Show session status')

    args = parser.parse_args()

    session_file = Path(args.session_file)

    # Ensure parent directory exists
    session_file.parent.mkdir(parents=True, exist_ok=True)

    if args.reset:
        result = reset_session(session_file)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if args.status:
        session = load_session(session_file)
        print(json.dumps(session, indent=2))
        sys.exit(0)

    if not args.url:
        print(json.dumps({
            'status': 'error',
            'message': 'URL required'
        }))
        sys.exit(1)

    # Track navigation
    result = track_navigation(args.url, session_file)
    print(json.dumps(result, indent=2))

    # Exit code: 0 for success, 1 for error
    sys.exit(0 if result['status'] != 'error' else 1)


if __name__ == '__main__':
    main()
