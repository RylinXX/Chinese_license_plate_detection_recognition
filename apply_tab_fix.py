# -*- coding: UTF-8 -*-
import os

def main():
    target_path = "templates/index.html"
    
    if not os.path.exists(target_path):
        print(f"Error: {target_path} not found.")
        return
        
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 替换 CSS 中的 .nav-links 样式规则，实现绝对居中定位
    old_css_links = """        .nav-links {
            display: flex;
            gap: 4px;
            background: rgba(0, 0, 0, 0.03);
            padding: 4px;
            border-radius: var(--border-radius-md);
            border: 1px solid var(--card-border);
        }"""
        
    new_css_links = """        .nav-links {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 4px;
            background: rgba(0, 0, 0, 0.03);
            padding: 4px;
            border-radius: var(--border-radius-md);
            border: 1px solid var(--card-border);
        }"""
        
    content_new = content.replace(old_css_links, new_css_links)

    # 2. 替换 switchTab 中的 .menu-item-link 为 .nav-item
    old_js_line = "document.querySelectorAll('.menu-item-link').forEach(el => el.classList.remove('active'));"
    new_js_line = "document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));"
    
    content_new = content_new.replace(old_js_line, new_js_line)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content_new)
        
    print("Tab positioning and active state fix completed successfully!")

if __name__ == "__main__":
    main()
