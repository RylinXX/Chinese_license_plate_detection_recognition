# -*- coding: UTF-8 -*-
import os

def main():
    target_path = "templates/index.html"
    
    if not os.path.exists(target_path):
        print(f"Error: {target_path} not found.")
        return
        
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 优化轻量/浅色模式下的字体颜色变量以增加对比度
    old_vars = """            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;"""
            
    new_vars = """            --text-primary: #0f172a;
            --text-secondary: #27272a; /* 更加深色，增加易读性 */
            --text-muted: #52525b; /* 更加深色，增加易读性 */"""
            
    content_new = content.replace(old_vars, new_vars)

    # 2. 在 CSS 中新增 #chart-tooltip 的样式，使用 var(--modal-bg) 进行自适应，实现完美的明暗色彩对比
    tooltip_css = """
        /* 折线图悬浮气泡 */
        #chart-tooltip {
            position: absolute;
            display: none;
            background: var(--modal-bg);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: var(--border-radius-sm);
            font-size: 11px;
            pointer-events: none;
            z-index: 1000;
            box-shadow: var(--card-shadow);
            white-space: nowrap;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            transition: opacity 0.15s ease;
        }
    """
    
    # 插入在 style 结束标签 </style> 的正上方
    content_new = content_new.replace("    </style>", tooltip_css + "\n    </style>")

    # 3. 将 JS 里的动态 tooltip 框修改为无内联样式的干净 div，以读取 CSS 样式
    old_inline_div = """                // Set HTML along with relative tooltip box
                let html = svg + `
                    <div id="chart-tooltip" style="position: absolute; display: none; background: rgba(15, 23, 42, 0.95); border: 1px solid var(--card-border); color: var(--text-primary); padding: 6px 10px; border-radius: var(--border-radius-sm); font-size: 11px; pointer-events: none; z-index: 100; box-shadow: var(--card-shadow); white-space: nowrap;"></div>
                `;"""
                
    new_inline_div = """                // Set HTML along with relative tooltip box
                let html = svg + `
                    <div id="chart-tooltip"></div>
                `;"""
                
    content_new = content_new.replace(old_inline_div, new_inline_div)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content_new)
        
    print("Tooltip contrast and light mode readability fix applied successfully!")

if __name__ == "__main__":
    main()
