import re, json, os

base = '/Users/benwu/Library/CloudStorage/Dropbox-Personal/cowork/subdomain-platform-designs'
out_base = '/Users/benwu/Library/CloudStorage/Dropbox-Personal/cowork/wbn580-subdomain-platforms/sites'

SITES = {
    'zhongjie-paiming': {
        'domain': 'zhongjie-paiming.wubaining.workers.dev',
        'brand': '留学中介排名榜',
        'tagline': '哪间留学中介真正帮到你？',
        'lang': 'zh-CN',
        'bizLine': 'edu-ranking',
        'primary': '#13294B',
        'accent': '#D4AF37',
        'botName': '榜单顾问',
        'cfProject': 'sp-zhongjie-paiming',
    },
    'xianggang-zhuce': {
        'domain': 'xianggang-zhuce.wubaining.workers.dev',
        'brand': '香港公司注册指南',
        'tagline': '你好！想喺香港开公司？我帮你睇流程同费用',
        'lang': 'zh-HK',
        'bizLine': 'biz-registration',
        'primary': '#0B3D3A',
        'accent': '#C8A24B',
        'botName': '注册顾问',
        'cfProject': 'sp-xianggang-zhuce',
    },
    'oshc-bijia': {
        'domain': 'oshc-bijia.wubaining.workers.dev',
        'brand': '留学保险OSHC比价',
        'tagline': '澳洲OSHC留学生医保横向比价',
        'lang': 'zh-CN',
        'bizLine': 'insurance-compare',
        'primary': '#0E7C86',
        'accent': '#F2785C',
        'botName': 'OSHC比价助手',
        'cfProject': 'sp-oshc-bijia',
    },
    'luohu-chaxun': {
        'domain': 'luohu-chaxun.wubaining.workers.dev',
        'brand': '海归落户分数查询',
        'tagline': '海归学历落户积分计算工具',
        'lang': 'zh-CN',
        'bizLine': 'hukou-calculator',
        'primary': '#1A2E4A',
        'accent': '#19C37D',
        'botName': '落户助手',
        'cfProject': 'sp-luohu-chaxun',
    },
    'huikuan-bijia': {
        'domain': 'huikuan-bijia.wubaining.workers.dev',
        'brand': '跨境汇款比价',
        'tagline': '留学生跨境汇款省钱横向比价',
        'lang': 'zh-CN',
        'bizLine': 'remittance-compare',
        'primary': '#0E2A3F',
        'accent': '#1FB57A',
        'botName': '汇款小助手',
        'cfProject': 'sp-huikuan-bijia',
    },
    'yasi-peixun': {
        'domain': 'yasi-peixun.wubaining.workers.dev',
        'brand': '雅思培训排名',
        'tagline': '雅思培训机构横向排名/比价',
        'lang': 'zh-CN',
        'bizLine': 'edu-ranking',
        'primary': '#1E3A8A',
        'accent': '#F59E0B',
        'botName': '雅思小助手',
        'cfProject': 'sp-yasi-peixun',
    },
}

def extract_style(html):
    """Extract the <style> block content"""
    m = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    return m.group(1).strip() if m else ''

def extract_scripts(html):
    """Extract all <script> blocks"""
    scripts = []
    for m in re.finditer(r'<script[^>]*>(.*?)</script>', html, re.DOTALL):
        scripts.append(m.group(1).strip())
    return scripts

def classify_scripts(scripts):
    """Classify scripts as 'layout' (nav, scroll, burger, chatbot) or 'content'"""
    layout_keywords = ['scroll', 'nav', 'burger', 'hamburger', 'chatbot', 'chat-bubble', 
                       'chatWidget', 'openWidget', 'back.to.top', 'backToTop',
                       'prefers-reduced-motion', 'window.addEventListener', 'onscroll']
    content_keywords = ['rank', 'filter', 'calculator', 'calc', 'faq', 'accordion', 
                        'tab', 'comparison', 'trial', 'compute', 'chart', 'graph',
                        'IntersectionObserver', 'reveal']
    
    layout_scripts = []
    content_scripts = []
    
    for s in scripts:
        if not s.strip():
            continue
        score_layout = sum(1 for kw in layout_keywords if kw.lower() in s.lower())
        score_content = sum(1 for kw in content_keywords if kw.lower() in s.lower())
        if score_layout >= score_content:
            layout_scripts.append(s)
        else:
            content_scripts.append(s)
    
    return layout_scripts, content_scripts

def extract_nav(html):
    """Extract the first <nav> element (desktop nav)"""
    # Find position of first <nav
    start = html.find('<nav')
    if start == -1:
        return ''
    # Find matching </nav> - must handle nested tags
    depth = 0
    i = start
    in_tag = False
    in_close = False
    while i < len(html):
        c = html[i]
        if c == '<':
            in_tag = True
            in_close = False
        elif in_tag and c == '/':
            in_close = True
        elif in_tag and c == 'n' and html[i:i+4] == 'nav>':
            if in_close:
                depth -= 1
                if depth == 0:
                    return html[start:i+4]
            else:
                depth += 1
            in_tag = False
        elif in_tag and (c == '>' or c == ' '):
            # Check if this is <nav ...>
            if html[i-4:i] == '<nav' or (i >= 4 and html[i-3:i] == 'nav'):
                depth += 1
            in_tag = False
        elif in_tag and c == '>' and in_close:
            in_tag = False
            in_close = False
        i += 1
    return ''

def simple_tag_extract(html, tag):
    """Simple extraction of a top-level tag by counting depth with <tag and </tag>"""
    # Find first <tag
    start_pat = f'<{tag}'
    end_pat = f'</{tag}>'
    start = html.find(start_pat)
    if start == -1:
        return '', -1, -1
    depth = 0
    i = start
    while i < len(html):
        if html[i:i+len(start_pat)] == start_pat and (html[i+len(start_pat)] in ' >'):
            depth += 1
            i += len(start_pat)
            continue
        if html[i:i+len(end_pat)] == end_pat:
            depth -= 1
            if depth == 0:
                return html[start:i+len(end_pat)], start, i+len(end_pat)
        i += 1
    return '', start, -1

def extract_chatbot(html):
    """Extract chatbot widget div - looks for elements with chat/bot/bubble classes near end of body"""
    # Find elements with chat/bot/bubble/messenger classes after footer
    patterns = [
        r'<div[^>]*class="[^"]*chat[^"]*"[^>]*>.*?</div>',  # too greedy
    ]
    # Look for chatbot section: typically a div with class containing chat, bot, bubble, widget
    # near the end of body
    m = re.search(r'<!--.*?(?:CHATBOT|聊天|chatbot|widget).*?-->', html, re.IGNORECASE)
    if m:
        # Find the next div after the comment
        pos = m.end()
        # Find matching div
        tag, _, _ = simple_tag_extract(html[pos:], 'div')
        if tag:
            return tag
    
    # Try finding by class pattern
    for cls_pat in ['chatbot', 'chat-bubble', 'bot-widget', 'messenger-widget', 'widget-chat', 'chat-widget', 'chatWidget']:
        m = re.search(rf'<div[^>]*class="[^"]*\b{cls_pat}\b[^"]*"[^>]*>', html)
        if m:
            tag, _, _ = simple_tag_extract(html[m.start():], 'div')
            if tag:
                return tag
    
    # Fallback: look for the chat element at the end of body
    body_end = html.find('</body>')
    if body_end == -1:
        return ''
    # Search backward from body end for chat-related div
    tail = html[body_end-3000:body_end]
    for cls_pat in ['chat', 'bubble', 'bot', 'widget', 'messenger']:
        m = re.search(rf'<div[^>]*class="[^"]*\b{cls_pat}\b[^"]*"[^>]*>(?:(?!</div>).)*</div>', tail, re.DOTALL)
        if m:
            return m.group(0)
    
    return ''

def process_site(slug, config):
    html_path = os.path.join(base, slug, 'preview.html')
    with open(html_path, 'r') as f:
        html = f.read()
    
    # Extract <head> content
    head_m = re.search(r'<head[^>]*>(.*?)</head>', html, re.DOTALL)
    head_content = head_m.group(1) if head_m else ''
    
    # Extract title
    title_m = re.search(r'<title>(.*?)</title>', head_content)
    title = title_m.group(1) if title_m else config['brand']
    
    # Extract meta description
    desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', head_content)
    description = desc_m.group(1) if desc_m else config['tagline']
    
    # Extract og:image
    og_m = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', head_content)
    og_image = og_m.group(1) if og_m else ''
    
    # Extract lang from html tag
    lang_m = re.search(r'<html\s+lang="([^"]*)"', html)
    lang = lang_m.group(1) if lang_m else config['lang']
    
    # Extract <style>
    style_content = extract_style(html)
    
    # Extract scripts
    scripts = extract_scripts(html)
    layout_scripts, content_scripts = classify_scripts(scripts)
    
    # Extract body
    body_m = re.search(r'<body[^>]*>(.*)</body>', html, re.DOTALL)
    body = body_m.group(1) if body_m else ''
    
    # Extract desktop nav (first <nav>)
    nav_html = extract_nav(body)
    
    # Extract footer
    footer_html, footer_start, footer_end = simple_tag_extract(body, 'footer')
    
    # Content is between end of first nav and start of footer
    nav_end = body.find('</nav>') + 6
    if footer_start > 0:
        content_html = body[nav_end:footer_start]
    else:
        # No footer, content is everything after nav
        content_html = body[nav_end:]
    
    # Extract chatbot from body (after footer or near end)
    chatbot_html = ''
    if footer_end > 0:
        tail = body[footer_end:]
        chatbot_html = extract_chatbot(tail)
    
    # If no chatbot found, check entire body
    if not chatbot_html:
        chatbot_html = extract_chatbot(body)
    
    # Remove chatbot from content if it leaked
    if chatbot_html and chatbot_html in content_html:
        content_html = content_html.replace(chatbot_html, '')
    
    # Also extract any mobile nav overlay (second <nav> that appears right after first)
    mobile_nav_html = ''
    content_html_clean = content_html
    
    # Clean up excessive whitespace
    content_html_clean = re.sub(r'\n{4,}', '\n\n\n', content_html_clean)
    
    # Generate site.config.json
    site_config = {
        "slug": slug,
        "domain": config['domain'],
        "brand": config['brand'],
        "tagline": config['tagline'],
        "lang": lang,
        "bizLine": config['bizLine'],
        "theme": "bespoke",
        "palette": {
            "primary": config['primary'],
            "accent": config['accent']
        },
        "font": '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Noto Sans SC", "Source Han Sans SC", "Helvetica Neue", Arial, sans-serif',
        "author": "UNILINK",
        "chatbot": {
            "backend": "ai-widget",
            "botName": config['botName']
        },
        "deployTarget": "workers",
        "cfProject": config['cfProject'],
        "noBrandLink": True
    }
    
    # Write site.config.json
    config_path = os.path.join(out_base, slug, 'site.config.json')
    with open(config_path, 'w') as f:
        json.dump(site_config, f, ensure_ascii=False, indent=2)
    print(f"  ✓ site.config.json written")
    
    # Write Layout.astro
    layout_html = generate_layout(lang, title, description, og_image, style_content, 
                                   nav_html, footer_html, chatbot_html, mobile_nav_html,
                                   layout_scripts, config)
    layout_path = os.path.join(out_base, slug, 'theme', 'Layout.astro')
    with open(layout_path, 'w') as f:
        f.write(layout_html)
    print(f"  ✓ Layout.astro written ({len(layout_html)} bytes)")
    
    # Write IndexContent.astro
    index_html = generate_index(content_html_clean, content_scripts)
    index_path = os.path.join(out_base, slug, 'theme', 'IndexContent.astro')
    with open(index_path, 'w') as f:
        f.write(index_html)
    print(f"  ✓ IndexContent.astro written ({len(index_html)} bytes)")

def generate_layout(lang, title, description, og_image, style, nav, footer, chatbot, mobile_nav, scripts, config):
    og = f'\n<meta property="og:image" content="{og_image}" />' if og_image else ''
    
    # Combine nav elements
    all_nav = nav + '\n' + mobile_nav if mobile_nav else nav
    
    # Format scripts
    script_block = ''
    for s in scripts:
        if s.strip():
            script_block += f'\n<script>\n{s.strip()}\n</script>\n'
    
    lines = []
    lines.append('---')
    lines.append(f'// {config["brand"]} · Bespoke Layout')
    lines.append(f'import {{ siteConfig }} from \'../../../src/lib/site\';')
    lines.append('')
    lines.append('const { title, description, ogImage } = Astro.props;')
    lines.append(f'const brand = siteConfig.brand || \'{config["brand"]}\';')
    lines.append('const pageTitle = title || brand;')
    lines.append(f'const pageDesc = description || \'{config["tagline"]}\';')
    lines.append('---')
    lines.append(f'<!DOCTYPE html>')
    lines.append(f'<html lang="{lang}">')
    lines.append('<head>')
    lines.append('<meta charset="UTF-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('<title>{pageTitle}</title>')
    lines.append('<meta name="description" content={pageDesc} />')
    lines.append('{ogImage && <meta property="og:image" content={ogImage} />}')
    if og:
        lines.append(og)
    
    if style:
        lines.append('<style is:global>')
        lines.append(style)
        lines.append('</style>')
    
    lines.append('</head>')
    lines.append('<body>')
    
    if all_nav:
        lines.append(all_nav)
    
    lines.append('<main>')
    lines.append('  <slot />')
    lines.append('</main>')
    
    if footer:
        lines.append(footer)
    
    if chatbot:
        lines.append(chatbot)
    
    if script_block:
        lines.append(script_block)
    
    lines.append('</body>')
    lines.append('</html>')
    
    return '\n'.join(lines)

def generate_index(content, scripts):
    lines = []
    lines.append('---')
    lines.append('// Bespoke homepage content')
    lines.append('---')
    
    # Write content as raw HTML
    # But we need to be careful with Astro template syntax conflicts
    # Replace any accidental `{` or `}` that aren't in <script> blocks
    lines.append(content)
    
    if scripts:
        for s in scripts:
            if s.strip():
                lines.append(f'<script>\n{s.strip()}\n</script>')
    
    return '\n'.join(lines)

# Process all sites
for slug, config in SITES.items():
    print(f"Processing {slug}...")
    try:
        process_site(slug, config)
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    print()

print("Done!")
