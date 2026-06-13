#!/usr/bin/env python3
"""
Standalone Scraper Runner
==========================
Run the continuous scraper as a separate background process.

Usage:
    # Run in foreground (for testing)
    python run_scraper.py
    
    # Run in background
    python run_scraper.py --daemon
    
    # Run with more workers
    python run_scraper.py --workers 5
    
    # Run without auto-discovery
    python run_scraper.py --no-discovery
    
    # Stop the daemon
    python run_scraper.py --stop

The scraper will:
1. Process URLs from the scrape_queue table
2. Auto-discover new company URLs
3. Extract links and queue them for scraping
4. Run continuously until stopped

View scraped data in the UI at /companies
View queue status at /monitoring
"""

import os
import sys
import argparse
import subprocess
import signal
import time
import signal

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment for database
os.environ.setdefault('DATABASE_URL', os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/intelligence_db'))
os.environ.setdefault('REDIS_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

from app.scraper.scraper_service import ContinuousScraper


def run_scraper(args):
    """Run the scraper with given arguments"""
    print("Starting Company Intelligence Scraper...")
    print(f"Workers: {args.workers}")
    print(f"Auto-discovery: {'Disabled' if args.no_discovery else 'Enabled'}")
    print("-" * 50)
    
    scraper = ContinuousScraper(
        num_workers=args.workers,
        enable_discovery=not args.no_discovery
    )
    
    try:
        scraper.run()
    except KeyboardInterrupt:
        print("\nScraper interrupted by user")
    except Exception as e:
        print(f"Scraper error: {e}")
        raise


def run_daemon(args):
    """Run scraper as a background daemon"""
    pid_file = '/tmp/intelligence_scraper.pid'
    
    # Check if already running
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            print(f"Scraper already running with PID {pid}")
            return
        except OSError:
            print("Stale PID file, removing...")
            os.remove(pid_file)
    
    print("Starting scraper as daemon...")
    
    # Fork process
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process
            with open(pid_file, 'w') as f:
                f.write(str(pid))
            print(f"Daemon started with PID {pid}")
            print(f"Log file: /tmp/scraper_{pid}.log")
            sys.exit(0)
    except OSError as e:
        print(f"Fork failed: {e}")
        sys.exit(1)
    
    # Child process - redirect output and run
    os.close(0)
    os.open('/dev/null', os.O_RDWR)
    os.dup2(0, 1)
    os.dup2(0, 2)
    
    # Change to root directory
    os.chdir('/')
    
    # Run the scraper
    scraper = ContinuousScraper(
        num_workers=args.workers,
        enable_discovery=not args.no_discovery
    )
    
    try:
        scraper.run()
    except Exception as e:
        print(f"Daemon error: {e}")


def stop_daemon():
    """Stop the running daemon"""
    pid_file = '/tmp/intelligence_scraper.pid'
    
    if not os.path.exists(pid_file):
        print("No scraper daemon running")
        return
    
    with open(pid_file, 'r') as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped scraper daemon (PID {pid})")
        os.remove(pid_file)
    except OSError as e:
        print(f"Error stopping daemon: {e}")
        if os.path.exists(pid_file):
            os.remove(pid_file)


def status_daemon():
    """Check daemon status"""
    pid_file = '/tmp/intelligence_scraper.pid'
    
    if not os.path.exists(pid_file):
        print("Scraper daemon is not running")
        return
    
    with open(pid_file, 'r') as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, 0)
        print(f"Scraper daemon is running (PID {pid})")
    except OSError:
        print("Scraper daemon is not running (stale PID file)")
        os.remove(pid_file)


def main():
    parser = argparse.ArgumentParser(
        description='Company Intelligence Scraper - Run continuous scraping in background',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py                    # Run in foreground
  python run_scraper.py --daemon            # Run in background
  python run_scraper.py --workers 5         # Use 5 concurrent workers
  python run_scraper.py --no-discovery      # Disable auto-discovery
  python run_scraper.py --stop             # Stop the daemon
  python run_scraper.py --status           # Check if running

The scraper continuously:
  - Processes URLs from the scrape_queue table
  - Auto-discovers new company URLs
  - Extracts links from scraped pages
  - Adds extracted links to the queue
  - Runs 24/7 until stopped
        """
    )
    
    parser.add_argument('--daemon', action='store_true', help='Run as background daemon')
    parser.add_argument('--stop', action='store_true', help='Stop the running daemon')
    parser.add_argument('--status', action='store_true', help='Check if daemon is running')
    parser.add_argument('--workers', type=int, default=3, help='Number of concurrent workers (default: 3)')
    parser.add_argument('--no-discovery', action='store_true', help='Disable auto-discovery of new URLs')
    parser.add_argument('--limit', type=int, default=None, help='Limit total URLs to scrape')
    
    args = parser.parse_args()
    
    if args.stop:
        stop_daemon()
    elif args.status:
        status_daemon()
    elif args.daemon:
        run_daemon(args)
    else:
        run_scraper(args)


if __name__ == '__main__':
    main()