#!/usr/bin/env python3
"""
DBIS Selector Validation Test
Academic Agent v2.3

Tests that DBIS selectors in config/dbis_selectors.yaml work correctly.
Run this periodically to detect if DBIS structure changes.

Usage:
    python tests/validate_dbis_selectors.py

Requirements:
    pip install selenium pyyaml
"""

import sys
import yaml
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def load_selectors():
    """Load selectors from config file"""
    config_path = Path(__file__).parent.parent / "config" / "dbis_selectors.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_selectors():
    """Validate DBIS selectors against live site"""

    print("="*60)
    print("DBIS Selector Validation Test")
    print("="*60)

    # Load configuration
    print("\n[1/5] Loading configuration...")
    config = load_selectors()
    selectors = {
        'database_entry': config['database_entry']['primary'],
        'database_name': config['database_name']['primary'],
        'traffic_light': config['traffic_light']['primary'],
    }
    print(f"✓ Loaded selectors from config/dbis_selectors.yaml")
    print(f"  - Database entry: {selectors['database_entry']}")
    print(f"  - Database name: {selectors['database_name']}")
    print(f"  - Traffic light: {selectors['traffic_light']}")

    # Setup Chrome
    print("\n[2/5] Initializing Chrome driver...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)
    print("✓ Chrome driver initialized")

    try:
        # Navigate to DBIS
        print("\n[3/5] Navigating to DBIS...")
        driver.get("https://dbis.ur.de/fachliste.php?bib_id=ubtib")
        time.sleep(3)
        print("✓ Loaded subjects page")

        # Click on a subject
        print("\n[4/5] Loading database list...")
        subject_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Buch- und Bibliothekswesen")
        subject_link.click()
        time.sleep(5)  # Wait for JavaScript
        current_url = driver.current_url
        print(f"✓ Loaded database list: {current_url}")

        # Test selectors
        print("\n[5/5] Testing selectors...")
        results = {}
        errors = []

        # Test database entries
        try:
            entries = driver.find_elements(By.CSS_SELECTOR, selectors['database_entry'])
            results['database_entry'] = len(entries)
            if len(entries) == 0:
                errors.append(f"❌ Database entry selector returned 0 results: {selectors['database_entry']}")
            else:
                print(f"✓ Database entries: {len(entries)} found")

                # Sample first entry
                if entries:
                    first = entries[0]
                    sample_text = first.text[:80]
                    sample_href = first.get_attribute('href')
                    print(f"  Sample: {sample_text}")
                    print(f"  URL: {sample_href}")
        except Exception as e:
            errors.append(f"❌ Database entry selector failed: {str(e)}")
            results['database_entry'] = 0

        # Test database names
        try:
            names = driver.find_elements(By.CSS_SELECTOR, selectors['database_name'])
            results['database_name'] = len(names)
            if len(names) == 0:
                errors.append(f"❌ Database name selector returned 0 results: {selectors['database_name']}")
            else:
                print(f"✓ Database names: {len(names)} found")
        except Exception as e:
            errors.append(f"❌ Database name selector failed: {str(e)}")
            results['database_name'] = 0

        # Test traffic lights
        try:
            lights = driver.find_elements(By.CSS_SELECTOR, selectors['traffic_light'])
            results['traffic_light'] = len(lights)
            if len(lights) == 0:
                errors.append(f"❌ Traffic light selector returned 0 results: {selectors['traffic_light']}")
            else:
                print(f"✓ Traffic lights: {len(lights)} found")

                # Check for color patterns
                if lights:
                    colors = {'green': 0, 'yellow': 0, 'red': 0}
                    for light in lights:
                        src = light.get_attribute('src')
                        if 'green' in src:
                            colors['green'] += 1
                        elif 'yellow' in src:
                            colors['yellow'] += 1
                        elif 'red' in src:
                            colors['red'] += 1

                    print(f"  Colors: green={colors['green']}, yellow={colors['yellow']}, red={colors['red']}")
        except Exception as e:
            errors.append(f"❌ Traffic light selector failed: {str(e)}")
            results['traffic_light'] = 0

        # Print summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)

        if errors:
            print(f"\n❌ FAILED - {len(errors)} error(s) detected:\n")
            for error in errors:
                print(f"  {error}")
            print("\n⚠️  DBIS structure may have changed!")
            print("⚠️  Selectors in config/dbis_selectors.yaml need updating.")
            return False
        else:
            print(f"\n✅ SUCCESS - All selectors working correctly!")
            print(f"\nResults:")
            print(f"  - Database entries: {results['database_entry']}")
            print(f"  - Database names: {results['database_name']}")
            print(f"  - Traffic lights: {results['traffic_light']}")
            print(f"\n✓ Configuration is up to date.")
            return True

    finally:
        driver.quit()


if __name__ == "__main__":
    try:
        success = validate_selectors()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
