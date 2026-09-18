import urllib.request
import json
import ssl

ctx = ssl.create_default_context()

backend = 'https://study-assistant-backend-rho.vercel.app'
frontend = 'https://ai-study-assistant-five-tau.vercel.app'

print('=== 1. VERIFYING PRODUCTION BACKEND ENDPOINTS ===')
endpoints = [
    ('GET', '/'),
    ('GET', '/api/health'),
    ('GET', '/api/resources?subject=Computer+Science&topic=Data+Structures'),
    ('POST', '/api/search', {'query': 'binary search tree', 'subject': 'Computer Science', 'max_results': 3}),
    ('POST', '/api/ask', {'question': 'what is binary tree', 'subject': 'Computer Science', 'explanation_mode': 'simple'}),
    ('GET', '/api/documents'),
    ('GET', '/api/conversations'),
    ('GET', '/api/resources/saved'),
    ('GET', '/api/profile')
]

all_passed = True

for item in endpoints:
    method = item[0]
    ep = item[1]
    data = item[2] if len(item) > 2 else None
    url = backend + ep
    headers = {'User-Agent': 'Mozilla/5.0'}
    req_body = None
    if data is not None:
        headers['Content-Type'] = 'application/json'
        req_body = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            status = resp.status
            body = resp.read().decode('utf-8')
            ct = resp.headers.get('Content-Type', '')
            parsed = json.loads(body) if 'application/json' in ct else body[:80]
            print(f'[PASS] {method:4} {ep:40} -> HTTP {status}')
            if ep == '/api/health':
                print(f'       Status: {parsed.get("status")} | Model: {parsed.get("model")} | Gemini: {parsed.get("gemini_configured")} | Tavily: {parsed.get("tavily_configured")}')
            elif ep == '/api/ask':
                ans = parsed.get('answer', '')
                print(f'       Answer preview: {ans[:90].replace(chr(10), " ")}...')
                print(f'       Warning: {parsed.get("warning")} | Sources: {len(parsed.get("sources", []))}')
            elif 'resources' in ep or ep == '/api/search':
                count = len(parsed) if isinstance(parsed, list) else 0
                print(f'       Items retrieved: {count}')
            elif ep in ('/api/documents', '/api/conversations', '/api/resources/saved'):
                count = len(parsed) if isinstance(parsed, list) else 0
                print(f'       List length: {count}')
    except Exception as e:
        all_passed = False
        print(f'[FAIL] {method:4} {ep:40} -> Error: {e}')

print('\n=== 2. VERIFYING PRODUCTION FRONTEND ROUTES ===')
routes = [
    '/',
    '/login',
    '/register',
    '/resources',
    '/dashboard',
    '/study',
    '/conversations',
    '/materials',
    '/saved',
    '/profile'
]

for r in routes:
    url = frontend + r
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='GET')
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            status = resp.status
            html = resp.read().decode('utf-8')
            has_root = '<div id="root">' in html
            has_script = '<script type="module"' in html
            title = 'AI Study Assistant' in html
            print(f'[PASS] Route {r:16} -> HTTP {status} | root_div={has_root} | script={has_script} | title_ok={title}')
    except Exception as e:
        all_passed = False
        print(f'[FAIL] Route {r:16} -> Error: {e}')

print(f'\n=== OVERALL INTEGRATION STATUS: {"ALL PASS" if all_passed else "FAILURES DETECTED"} ===')
