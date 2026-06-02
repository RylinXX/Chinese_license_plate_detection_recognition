# -*- coding: UTF-8 -*-
import os

def main():
    target_path = "templates/index.html"
    
    if not os.path.exists(target_path):
        print(f"Error: {target_path} not found.")
        return
        
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 替换 ledger-site-filter 的高度和内边距，防止中文字体截断
    old_select_str = 'id="ledger-site-filter" style="width: 200px; height:34px;"'
    new_select_str = 'id="ledger-site-filter" style="width: 220px; padding: 6px 12px; font-size: 13px; height: 38px;"'
    
    content_new = content.replace(old_select_str, new_select_str)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content_new)
        
    print("Filter dropdown text clipping fix applied successfully!")

if __name__ == "__main__":
    main()
