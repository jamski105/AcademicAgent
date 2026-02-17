#!/usr/bin/env python3
"""
Domain Validator for AcademicAgent (DBIS Proxy Mode)
Validates URLs against whitelist/blacklist with DBIS proxy support

Usage:
  python3 scripts/validate_domain.py "https://ieeexplore.ieee.org"
  python3 scripts/validate_domain.py "https://example.com" --referer "https://dbis.ur.de" --session-file session.json

Returns:
  Exit code 0 if allowed, 1 if blocked
  JSON output with decision and reason
"""

import sys
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from fnmatch import fnmatch


def load_whitelist():
    """Load domain whitelist configuration"""
    config_file = Path(__file__).parent / 'domain_whitelist.json'
    with open(config_file, 'r') as f:
        return json.load(f)


def is_trusted_proxy(hostname: str, config: dict) -> bool:
    """Check if hostname is a trusted proxy (DBIS, EZProxy, etc.)"""
    trusted_proxies = config.get('trusted_proxies', [])
    for proxy in trusted_proxies:
        if hostname == proxy or hostname.endswith('.' + proxy):
            return True
    return False


def is_blocked_domain(hostname: str, config: dict) -> bool:
    """Check if domain is explicitly blocked"""
    for blocked_pattern in config.get('blocked_domains', []):
        if fnmatch(hostname, blocked_pattern):
            return True
    return False


def check_session_tracking(session_file: str = None) -> dict:
    """
    Check if current navigation is part of a DBIS-initiated session

    Returns:
        {
            'session_active': bool,
            'started_from_dbis': bool,
            'navigation_count': int
        }
    """
    if not session_file:
        return {
            'session_active': False,
            'started_from_dbis': False,
            'navigation_count': 0
        }

    try:
        with open(session_file, 'r') as f:
            session = json.load(f)
            return session
    except FileNotFoundError:
        return {
            'session_active': False,
            'started_from_dbis': False,
            'navigation_count': 0
        }


def validate_domain_proxy_mode(url: str, config: dict, referer: str = None, session_file: str = None) -> dict:
    """
    Validate URL in DBIS proxy mode

    Rules:
    1. Always allow DBIS/proxy domains
    2. Allow database domains ONLY if:
       - Referer is DBIS/proxy, OR
       - Session started from DBIS
    3. Block direct navigation to databases
    4. Always block pirate sites
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or parsed.netloc
    except Exception as e:
        return {
            'allowed': False,
            'reason': f'Invalid URL format: {str(e)}',
            'risk_level': 'HIGH'
        }

    # Rule 1: Always block pirate sites
    if is_blocked_domain(hostname, config):
        return {
            'allowed': False,
            'reason': f'Domain explicitly blocked (pirate site): {hostname}',
            'risk_level': 'CRITICAL',
            'mode': 'proxy'
        }

    # Rule 2: Always allow trusted proxies (DBIS, EZProxy, Shibboleth)
    if is_trusted_proxy(hostname, config):
        return {
            'allowed': True,
            'reason': f'Trusted proxy domain: {hostname}',
            'risk_level': 'LOW',
            'mode': 'proxy',
            'is_proxy': True
        }

    # Rule 3: Check if proxy mode is enabled
    proxy_policy = config.get('proxy_redirect_policy', {})
    allow_redirects = proxy_policy.get('allow_redirects_from_trusted_proxies', False)

    if not allow_redirects:
        # Fallback to legacy whitelist mode
        return validate_domain_legacy(url, config)

    # Rule 4: Check referer
    referer_is_dbis = False
    if referer:
        try:
            referer_parsed = urlparse(referer)
            referer_hostname = referer_parsed.hostname
            referer_is_dbis = is_trusted_proxy(referer_hostname, config)
        except:
            pass

    # Rule 5: Check session tracking
    session = check_session_tracking(session_file)
    session_from_dbis = session.get('started_from_dbis', False)

    # Rule 6: Allow database if from DBIS
    if referer_is_dbis or session_from_dbis:
        return {
            'allowed': True,
            'reason': f'Database access via DBIS proxy: {hostname}',
            'risk_level': 'LOW',
            'mode': 'proxy',
            'via_proxy': True,
            'referer_is_dbis': referer_is_dbis,
            'session_from_dbis': session_from_dbis
        }

    # Rule 7: Block direct navigation to databases
    # If we get here, it's direct navigation (no DBIS referer/session)
    return {
        'allowed': False,
        'reason': f'Direct database access blocked. Must navigate via DBIS (dbis.ur.de or dbis.de) to ensure university license compliance. Current: {hostname}',
        'risk_level': 'HIGH',
        'mode': 'proxy',
        'suggestion': 'Start navigation at https://dbis.ur.de and use database links from there'
    }


def validate_domain_legacy(url: str, config: dict) -> dict:
    """Legacy validation (whitelist-based)"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or parsed.netloc
    except Exception as e:
        return {
            'allowed': False,
            'reason': f'Invalid URL format: {str(e)}',
            'risk_level': 'HIGH'
        }

    # Check blocked first
    if is_blocked_domain(hostname, config):
        return {
            'allowed': False,
            'reason': f'Domain blocked: {hostname}',
            'risk_level': 'CRITICAL',
            'mode': 'legacy'
        }

    # Check allowed patterns
    for allowed_pattern in config.get('allowed_patterns', []):
        pattern_regex = allowed_pattern.replace('*', '.*')
        if re.match(pattern_regex, url):
            return {
                'allowed': True,
                'reason': f'URL matches allowed pattern: {allowed_pattern}',
                'risk_level': 'LOW',
                'mode': 'legacy'
            }

    # Check allowed domains
    for allowed_domain in config.get('allowed_domains', []):
        if hostname == allowed_domain or hostname.endswith('.' + allowed_domain):
            return {
                'allowed': True,
                'reason': f'Domain whitelisted: {hostname}',
                'risk_level': 'LOW',
                'mode': 'legacy'
            }

    # Not in whitelist
    return {
        'allowed': False,
        'reason': f'Domain not in whitelist: {hostname}',
        'risk_level': 'HIGH',
        'mode': 'legacy'
    }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Domain Validator (DBIS Proxy Mode)')
    parser.add_argument('url', help='URL to validate')
    parser.add_argument('--referer', help='HTTP Referer (previous page URL)')
    parser.add_argument('--session-file', help='Path to session tracking file')
    parser.add_argument('--mode', choices=['proxy', 'legacy'], default='proxy',
                        help='Validation mode (default: proxy)')

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_whitelist()
    except Exception as e:
        print(json.dumps({
            'allowed': False,
            'reason': f'Failed to load whitelist: {str(e)}',
            'risk_level': 'CRITICAL'
        }))
        sys.exit(1)

    # Validate
    if args.mode == 'proxy' or config.get('proxy_mode') == 'dbis_only':
        result = validate_domain_proxy_mode(
            args.url,
            config,
            referer=args.referer,
            session_file=args.session_file
        )
    else:
        result = validate_domain_legacy(args.url, config)

    # Output JSON
    print(json.dumps(result, indent=2))

    # Exit code
    sys.exit(0 if result['allowed'] else 1)


if __name__ == '__main__':
    main()
