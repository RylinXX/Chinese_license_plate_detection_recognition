# -*- coding: UTF-8 -*-
import os
import re

def main():
    backup_path = "templates/index.html.bak"
    output_path = "templates/index.html"
    
    if not os.path.exists(backup_path):
        print(f"Error: Backup file {backup_path} not found.")
        return
        
    with open(backup_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 重构 CSS 样式表部分 (用全新的毛玻璃、顶部导航、中国车牌样式替换)
    # 我们匹配 <style> 和 </style> 之间的内容
    new_css = """
        :root {
            color-scheme: light;
            --bg-color: #f1f5f9;
            --header-bg: rgba(255, 255, 255, 0.7);
            --card-bg: rgba(255, 255, 255, 0.85);
            --card-hover-bg: #ffffff;
            --card-border: rgba(226, 232, 240, 0.8);
            --card-border-hover: rgba(203, 213, 225, 1);
            
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            
            --color-primary: #4f46e5;
            --color-primary-hover: #4338ca;
            --color-primary-active-bg: rgba(79, 70, 229, 0.08);
            --color-primary-active-border: rgba(79, 70, 229, 0.15);
            --color-primary-hover-bg: rgba(79, 70, 229, 0.04);
            --color-primary-active-shadow: rgba(79, 70, 229, 0.25);
            
            --color-in: #10b981;
            --color-in-light: rgba(16, 185, 129, 0.08);
            
            --color-out: #0ea5e9;
            --color-out-light: rgba(14, 165, 233, 0.08);
            
            --color-stay: #f59e0b;
            --color-stay-light: rgba(245, 158, 11, 0.08);
            
            --color-danger: #ef4444;
            --color-danger-light: rgba(239, 68, 68, 0.08);

            --bg-image: radial-gradient(at 10% 20%, rgba(79, 70, 229, 0.05) 0px, transparent 50%),
                        radial-gradient(at 90% 80%, rgba(14, 165, 233, 0.04) 0px, transparent 50%),
                        radial-gradient(at 50% 50%, #f1f5f9 0px, #e2e8f0 100%);
            
            --kpi-bg: rgba(255, 255, 255, 0.5);
            --kpi-hover-bg: rgba(255, 255, 255, 0.9);
            --kpi-shadow: 0 4px 12px rgba(148, 163, 184, 0.05);
            
            --sub-panel-bg: rgba(255, 255, 255, 0.4);
            --input-bg: #ffffff;
            --input-focus-shadow: rgba(79, 70, 229, 0.2);
            
            --btn-sec-bg: #ffffff;
            --btn-sec-border: #cbd5e1;
            --btn-sec-color: #475569;
            --btn-sec-hover-bg: #f8fafc;
            --btn-sec-hover-border: #94a3b8;
            --btn-sec-hover-color: #1e293b;
            
            --suggestions-bg: #ffffff;
            --suggestions-border: #cbd5e1;
            --suggestions-shadow: 0 10px 25px rgba(148, 163, 184, 0.1);
            --suggestions-hover-bg: #f1f5f9;
            
            --rank-badge-bg: #f1f5f9;
            --rank-trips-bg: #ecfeff;
            --rank-trips-border: rgba(6, 182, 212, 0.2);
            --rank-trips-color: #06b6d4;
            
            --filter-bar-bg: rgba(255, 255, 255, 0.3);
            --table-bg: transparent;
            --table-th-bg: #f1f5f9;
            --table-border: rgba(226, 232, 240, 0.8);
            --table-hover-bg: rgba(241, 245, 249, 0.6);
            
            --summary-bar-bg: #ecfdf5;
            --summary-bar-border: rgba(16, 185, 129, 0.2);
            
            --card-shadow: 0 8px 30px rgba(148, 163, 184, 0.08);
            --card-hover-shadow: 0 12px 40px rgba(148, 163, 184, 0.15);
            
            --modal-bg: #ffffff;
            --modal-shadow: 0 20px 50px rgba(148, 163, 184, 0.15);
            --modal-overlay-bg: rgba(15, 23, 42, 0.3);
            
            --chart-grid-stroke: rgba(0, 0, 0, 0.05);
            --chart-bar-bg: #e2e8f0;
            --chart-line-start: #4f46e5;
            --chart-line-end: #0ea5e9;
            --chart-area-start: rgba(79, 70, 229, 0.15);
            --chart-area-end: rgba(79, 70, 229, 0);
            --chart-node-fill: #4f46e5;
            
            --font-family: 'Outfit', 'Noto Sans SC', sans-serif;
            --border-radius-lg: 16px;
            --border-radius-md: 12px;
            --border-radius-sm: 8px;
            --transition-base: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        }

        :root[data-theme="dark"] {
            color-scheme: dark;
            --bg-color: #060813;
            --header-bg: rgba(15, 22, 42, 0.7);
            --card-bg: rgba(15, 22, 42, 0.55);
            --card-hover-bg: rgba(22, 32, 60, 0.65);
            --card-border: rgba(255, 255, 255, 0.07);
            --card-border-hover: rgba(99, 102, 241, 0.3);
            
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            
            --color-primary: #6366f1;
            --color-primary-hover: #4f46e5;
            --color-primary-active-bg: rgba(99, 102, 241, 0.12);
            --color-primary-active-border: rgba(99, 102, 241, 0.25);
            --color-primary-hover-bg: rgba(255, 255, 255, 0.03);
            --color-primary-active-shadow: rgba(99, 102, 241, 0.4);
            
            --color-in: #10b981;
            --color-in-light: rgba(16, 185, 129, 0.15);
            
            --color-out: #0ea5e9;
            --color-out-light: rgba(14, 165, 233, 0.15);
            
            --color-stay: #f59e0b;
            --color-stay-light: rgba(245, 158, 11, 0.15);
            
            --color-danger: #ef4444;
            --color-danger-light: rgba(239, 68, 68, 0.15);

            --bg-image: radial-gradient(at 10% 20%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
                        radial-gradient(at 90% 80%, rgba(245, 158, 11, 0.03) 0px, transparent 50%),
                        radial-gradient(at 50% 50%, #060813 0px, #020307 100%);
            
            --kpi-bg: rgba(255, 255, 255, 0.01);
            --kpi-hover-bg: rgba(255, 255, 255, 0.03);
            --kpi-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            
            --sub-panel-bg: rgba(255, 255, 255, 0.015);
            --input-bg: rgba(10, 15, 30, 0.7);
            --input-focus-shadow: rgba(99, 102, 241, 0.35);
            
            --btn-sec-bg: rgba(255, 255, 255, 0.03);
            --btn-sec-border: rgba(255, 255, 255, 0.07);
            --btn-sec-color: #94a3b8;
            --btn-sec-hover-bg: rgba(255, 255, 255, 0.08);
            --btn-sec-hover-border: rgba(255, 255, 255, 0.15);
            --btn-sec-hover-color: #ffffff;
            
            --suggestions-bg: #0b0f19;
            --suggestions-border: rgba(255, 255, 255, 0.1);
            --suggestions-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            --suggestions-hover-bg: rgba(255, 255, 255, 0.06);
            
            --rank-badge-bg: rgba(255, 255, 255, 0.05);
            --rank-trips-bg: rgba(14, 165, 233, 0.15);
            --rank-trips-border: rgba(14, 165, 233, 0.25);
            --rank-trips-color: #38bdf8;
            
            --filter-bar-bg: rgba(255, 255, 255, 0.01);
            --table-bg: transparent;
            --table-th-bg: rgba(255, 255, 255, 0.03);
            --table-border: rgba(255, 255, 255, 0.03);
            --table-hover-bg: rgba(255, 255, 255, 0.02);
            
            --summary-bar-bg: rgba(16, 185, 129, 0.08);
            --summary-bar-border: rgba(16, 185, 129, 0.2);
            
            --card-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
            --card-hover-shadow: 0 16px 48px rgba(99, 102, 241, 0.15);
            
            --modal-bg: #0b0f19;
            --modal-shadow: 0 30px 70px rgba(0, 0, 0, 0.6);
            --modal-overlay-bg: rgba(2, 3, 6, 0.8);
            
            --chart-grid-stroke: rgba(255, 255, 255, 0.05);
            --chart-bar-bg: rgba(255, 255, 255, 0.03);
            --chart-line-start: #6366f1;
            --chart-line-end: #38bdf8;
            --chart-area-start: rgba(99, 102, 241, 0.25);
            --chart-area-end: rgba(99, 102, 241, 0);
            --chart-node-fill: #6366f1;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: var(--font-family);
            min-height: 100vh;
            padding: 108px 24px 24px 24px; /* 为浮动导航栏留出空间 */
            background-image: var(--bg-image);
            background-attachment: fixed;
            transition: background-color 0.3s, color 0.3s;
            overflow-y: auto;
            position: relative;
        }

        /* 背景装饰发光体 */
        .glow-bg-blob {
            position: fixed;
            border-radius: 50%;
            filter: blur(120px);
            z-index: -1;
            opacity: 0.12;
            pointer-events: none;
            transition: var(--transition-base);
        }
        .blob-1 {
            width: 400px;
            height: 400px;
            background: var(--color-primary);
            top: -100px;
            left: -100px;
        }
        .blob-2 {
            width: 500px;
            height: 500px;
            background: var(--color-out);
            bottom: -150px;
            right: -150px;
        }
        :root[data-theme="dark"] .glow-bg-blob {
            opacity: 0.22;
        }

        /* 顶部浮动导航栏 */
        .floating-navbar {
            position: fixed;
            top: 16px;
            left: 16px;
            right: 16px;
            height: 68px;
            background: var(--header-bg);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-lg);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 24px;
            z-index: 1000;
            box-shadow: var(--card-shadow);
            transition: var(--transition-base);
        }

        .floating-navbar:hover {
            border-color: var(--card-border-hover);
        }

        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo-container {
            width: 34px;
            height: 34px;
            background: linear-gradient(135deg, var(--color-out), var(--color-primary));
            border-radius: var(--border-radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
        }

        .brand-text {
            display: flex;
            flex-direction: column;
        }

        .brand-title {
            font-size: 15px;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: 0.5px;
        }

        .brand-subtitle {
            font-size: 9px;
            color: var(--text-muted);
            font-weight: 700;
            letter-spacing: 1px;
            margin-top: 1px;
            text-transform: uppercase;
        }

        .nav-links {
            display: flex;
            gap: 4px;
            background: rgba(0, 0, 0, 0.03);
            padding: 4px;
            border-radius: var(--border-radius-md);
            border: 1px solid var(--card-border);
        }

        :root[data-theme="dark"] .nav-links {
            background: rgba(255, 255, 255, 0.02);
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 18px;
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 700;
            text-decoration: none;
            border-radius: var(--border-radius-sm);
            transition: var(--transition-base);
            cursor: pointer;
        }

        .nav-item:hover {
            color: var(--color-primary);
            background-color: var(--color-primary-hover-bg);
        }

        .nav-item.active {
            color: #ffffff;
            background-color: var(--color-primary);
            box-shadow: 0 4px 14px var(--color-primary-active-shadow);
        }

        .navbar-actions {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .date-selector-wrapper {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .navbar-label {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-secondary);
            white-space: nowrap;
        }

        .actions-area {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .theme-toggle-btn {
            width: 34px;
            height: 34px;
            border-radius: var(--border-radius-sm);
            background: var(--btn-sec-bg);
            border: 1px solid var(--btn-sec-border);
            color: var(--btn-sec-color);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition-base);
        }

        .theme-toggle-btn:hover {
            background: var(--btn-sec-hover-bg);
            border-color: var(--btn-sec-hover-border);
            color: var(--btn-sec-hover-color);
        }

        .clock-display-wrapper {
            font-size: 12px;
            font-weight: 700;
            color: var(--text-primary);
            font-family: monospace;
            background: rgba(0, 0, 0, 0.03);
            padding: 7px 12px;
            border-radius: var(--border-radius-sm);
            border: 1px solid var(--card-border);
        }

        :root[data-theme="dark"] .clock-display-wrapper {
            background: rgba(255, 255, 255, 0.02);
        }

        /* 统一的主容器 */
        .main-container {
            width: 100%;
            max-width: 1600px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }

        /* 面板内容容器 */
        .main-content {
            display: none;
            width: 100%;
        }

        .main-content.active {
            display: flex;
            animation: panelFadeIn 0.35s cubic-bezier(0.4, 0, 0.2, 1) both;
        }

        @keyframes panelFadeIn {
            0% { opacity: 0; transform: translateY(12px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        /* 1. 实时监控看板 */
        #panel-monitor.active {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* 2. 通行财务台账 */
        #panel-ledger.active {
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 20px;
        }

        /* 3. 系统参数配置 */
        #panel-config.active {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 20px;
        }

        /* 玻璃面板卡片样式 */
        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-lg);
            padding: 20px;
            display: flex;
            flex-direction: column;
            box-shadow: var(--card-shadow);
            transition: var(--transition-base);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }

        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--card-border), transparent);
        }

        .glass-card:hover {
            box-shadow: var(--card-hover-shadow);
            border-color: var(--card-border-hover);
            transform: translateY(-2px);
        }

        .card-header-title {
            font-size: 15px;
            font-weight: 800;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-left: 3.5px solid var(--color-primary);
            padding-left: 10px;
            color: var(--text-primary);
        }

        /* 左右栏内部垂直堆叠 */
        .monitor-left-col, .ledger-left-col {
            display: flex;
            flex-direction: column;
            gap: 20px;
            min-height: 0;
        }

        /* KPIs指标堆叠 */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .kpi-card {
            background: var(--kpi-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-md);
            padding: 14px 16px;
            display: flex;
            align-items: center;
            gap: 14px;
            transition: var(--transition-base);
            box-shadow: var(--kpi-shadow);
        }

        .kpi-card:hover {
            background: var(--kpi-hover-bg);
            border-color: var(--card-border-hover);
            transform: translateY(-2px);
            box-shadow: var(--card-shadow);
        }

        .kpi-icon {
            width: 40px;
            height: 40px;
            border-radius: var(--border-radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-size: 18px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        }

        .kpi-info {
            display: flex;
            flex-direction: column;
            min-width: 0;
        }

        .kpi-label {
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .kpi-value {
            font-size: 20px;
            font-weight: 800;
            line-height: 1.25;
            color: var(--text-primary);
        }

        .kpi-icon-out { background-color: var(--color-out-light); color: var(--color-out); }
        .kpi-icon-cost { background-color: var(--color-in-light); color: var(--color-in); }
        .kpi-icon-danger { background-color: var(--color-danger-light); color: var(--color-danger); }
        .kpi-icon-stay { background-color: var(--color-stay-light); color: var(--color-stay); }

        /* 补录控制中心与配置滚存区 */
        .control-panel, .config-panel {
            flex-grow: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
        }

        .control-scroll-wrapper, .config-scroll-wrapper {
            flex-grow: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding-right: 4px;
        }

        /* 滚动条美化 */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(148, 163, 184, 0.2);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(148, 163, 184, 0.4);
        }
        :root[data-theme="dark"] ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.08);
        }
        :root[data-theme="dark"] ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        .sub-panel-box {
            background: var(--sub-panel-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-md);
            padding: 14px;
            transition: var(--transition-base);
        }
        .sub-panel-box:hover {
            border-color: var(--card-border-hover);
        }

        .sub-panel-title {
            font-size: 13px;
            font-weight: 800;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--text-primary);
        }

        /* 表单控件 */
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 12px;
            position: relative;
        }

        .form-label {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .input-control {
            background-color: var(--input-bg);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 10px 14px;
            border-radius: var(--border-radius-sm);
            font-family: var(--font-family);
            font-size: 13px;
            outline: none;
            width: 100%;
            transition: var(--transition-base);
        }

        .input-control:focus {
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px var(--input-focus-shadow);
        }

        .select-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        /* 按钮样式 */
        .btn {
            background: var(--color-primary);
            border: 1px solid var(--color-primary);
            color: #fff;
            padding: 10px 18px;
            border-radius: var(--border-radius-sm);
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: var(--transition-base);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 12px var(--color-primary-active-shadow);
        }

        .btn:hover {
            background: var(--color-primary-hover);
            border-color: var(--color-primary-hover);
            transform: translateY(-1px);
            box-shadow: 0 6px 16px var(--color-primary-active-shadow);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .btn-accent {
            background: var(--color-primary);
            border: 1px solid var(--color-primary);
            color: #fff;
        }

        .btn-secondary {
            background: var(--btn-sec-bg);
            border: 1px solid var(--btn-sec-border);
            color: var(--btn-sec-color);
            box-shadow: none;
        }

        .btn-secondary:hover {
            background: var(--btn-sec-hover-bg);
            border-color: var(--btn-sec-hover-border);
            color: var(--btn-sec-hover-color);
            box-shadow: var(--kpi-shadow);
        }

        .btn-danger {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.03));
            border-color: rgba(239, 68, 68, 0.25);
            color: var(--color-danger);
            box-shadow: none;
        }
        .btn-danger:hover {
            background: var(--color-danger);
            border-color: var(--color-danger);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        }

        /* 联想输入框 */
        .custom-suggestions-box {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--suggestions-bg);
            border: 1px solid var(--suggestions-border);
            border-radius: var(--border-radius-sm);
            max-height: 180px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            box-shadow: var(--suggestions-shadow);
            margin-top: 4px;
            animation: slideDown 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .suggestion-item {
            padding: 10px 14px;
            cursor: pointer;
            font-size: 13px;
            color: var(--text-primary);
            transition: background 0.2s;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .suggestion-item:hover {
            background: var(--suggestions-hover-bg);
        }

        /* 1. 可视化分析 */
        .charts-row {
            display: grid;
            grid-template-columns: 1.2fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .chart-card-box {
            background: var(--sub-panel-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-md);
            padding: 16px;
            display: flex;
            flex-direction: column;
            min-height: 220px;
            transition: var(--transition-base);
        }

        .chart-card-box:hover {
            border-color: var(--card-border-hover);
        }

        .chart-box-title {
            font-size: 12px;
            font-weight: 800;
            color: var(--text-secondary);
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* 拟真车牌样式 */
        .plate-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 3px 10px;
            border-radius: 4px;
            font-weight: 900;
            font-size: 13px;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            position: relative;
            font-family: 'Noto Sans SC', sans-serif;
            border: 1.5px solid rgba(255, 255, 255, 0.25);
            user-select: none;
            min-width: 92px;
            text-align: center;
            line-height: 1.2;
        }
        .plate-badge .plate-inner-border {
            position: absolute;
            top: 2px;
            left: 2px;
            right: 2px;
            bottom: 2px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 2px;
            pointer-events: none;
        }

        .plate-yellow {
            background: linear-gradient(180deg, #fbbf24 0%, #d97706 100%);
            color: #0f172a;
            border-color: #f59e0b;
        }
        .plate-yellow .plate-inner-border {
            border-color: rgba(0, 0, 0, 0.12);
        }

        .plate-blue {
            background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%);
            color: #ffffff;
            border-color: #2563eb;
        }

        .plate-green {
            background: linear-gradient(180deg, #ffffff 0%, #ffffff 20%, #4ade80 25%, #16a34a 100%);
            color: #0f172a;
            border-color: #22c55e;
        }
        .plate-green .plate-inner-border {
            border-color: rgba(0, 0, 0, 0.08);
        }

        .plate-black {
            background: linear-gradient(180deg, #475569 0%, #0f172a 100%);
            color: #ffffff;
            border-color: #1e293b;
        }

        .plate-white {
            background: #ffffff;
            color: #ef4444;
            border-color: #dc2626;
        }
        .plate-white .plate-inner-border {
            border-color: rgba(220, 38, 38, 0.15);
        }

        .ranking-empty {
            color: var(--text-muted);
            font-size: 13px;
            text-align: center;
            margin: auto;
            padding: 30px 10px;
        }

        /* 通行方向胶囊 */
        .direction-pill {
            font-size: 10px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 12px;
            width: 72px;
            text-align: center;
            display: inline-block;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }

        .direction-pill.in {
            background-color: var(--color-in-light);
            border: 1.5px solid rgba(16, 185, 129, 0.3);
            color: var(--color-in);
        }

        .direction-pill.out {
            background-color: var(--color-out-light);
            border: 1.5px solid rgba(14, 165, 233, 0.3);
            color: var(--color-out);
        }

        /* 2. 通行财务对账大卡片 */
        .ledger-main-card {
            flex-grow: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
        }

        .ledger-filter-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            background: var(--filter-bar-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-md);
            padding: 12px 18px;
        }

        .table-responsive {
            flex-grow: 1;
            overflow-y: auto;
            border-radius: var(--border-radius-md);
            border: 1px solid var(--card-border);
            background: var(--table-bg);
        }

        .ledger-table {
            width: 100%;
            border-collapse: collapse;
            text-align: center;
            font-size: 13px;
        }

        .ledger-table th {
            background: var(--table-th-bg);
            color: var(--text-secondary);
            padding: 14px;
            font-weight: 800;
            border-bottom: 1px solid var(--card-border);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .ledger-table td {
            padding: 14px;
            border-bottom: 1px solid var(--table-border);
            color: var(--text-primary);
        }

        .ledger-table tr {
            transition: background 0.2s;
        }

        .ledger-table tr:hover {
            background: var(--table-hover-bg);
        }

        /* 对账汇总横幅 */
        .ledger-summary-bar {
            margin-top: 16px;
            background: var(--summary-bar-bg);
            border: 1px solid var(--summary-bar-border);
            border-radius: var(--border-radius-md);
            padding: 14px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            font-weight: 700;
            color: var(--text-primary);
        }

        /* 3. 卡片网格查看方式 (一行好几个车) */
        .ledger-cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 14px;
            padding: 2px;
        }

        .vehicle-summary-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-md);
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            transition: var(--transition-base);
            position: relative;
        }

        .vehicle-summary-card:hover {
            background: var(--card-hover-bg);
            border-color: var(--card-border-hover);
            transform: translateY(-2px);
            box-shadow: var(--card-hover-shadow);
        }

        .card-plate-badge-row {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 4px;
        }

        .card-plate-text {
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: var(--text-primary);
        }

        .card-stat-row {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-secondary);
        }

        /* 弹窗遮罩与卡片 */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--modal-overlay-bg);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            z-index: 9999;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .modal-card {
            background: var(--modal-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-lg);
            width: 100%;
            max-width: 950px;
            height: 80vh;
            display: flex;
            flex-direction: column;
            padding: 24px;
            box-shadow: var(--modal-shadow);
            animation: modalScale 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both;
            position: relative;
        }

        @keyframes modalScale {
            0% { transform: scale(0.95); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 14px;
        }

        .modal-title {
            font-size: 18px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .modal-close-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 28px;
            cursor: pointer;
            line-height: 1;
            transition: color 0.2s;
        }

        .modal-close-btn:hover {
            color: var(--text-primary);
        }

        /* 弹窗表格 */
        .modal-table-container {
            flex-grow: 1;
            overflow-y: auto;
            border-radius: var(--border-radius-md);
            border: 1px solid var(--card-border);
            background: var(--table-bg);
        }

        .modal-table {
            width: 100%;
            border-collapse: collapse;
            text-align: center;
            font-size: 13px;
        }

        .modal-table th {
            background: var(--table-th-bg);
            color: var(--text-secondary);
            padding: 12px;
            font-weight: 800;
            border-bottom: 1px solid var(--card-border);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .modal-table td {
            padding: 12px;
            border-bottom: 1px solid var(--table-border);
            color: var(--text-primary);
        }

        .modal-table tr:hover {
            background: var(--table-hover-bg);
        }

        /* Toast提示框 */
        .toast-container {
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast-card {
            background: var(--modal-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--border-radius-md);
            padding: 14px 20px;
            display: flex;
            align-items: center;
            gap: 14px;
            box-shadow: var(--modal-shadow);
            min-width: 300px;
            transform: translateX(120%);
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            backdrop-filter: blur(15px);
        }

        .toast-card.show {
            transform: translateX(0);
        }

        .toast-card.success { border-left: 4px solid var(--color-in); }
        .toast-card.error { border-left: 4px solid var(--color-danger); }
        .toast-card.info { border-left: 4px solid var(--color-out); }

        .toast-icon {
            font-size: 18px;
            flex-shrink: 0;
        }

        .toast-content {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .toast-title {
            font-size: 13px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .toast-desc {
            font-size: 11px;
            color: var(--text-secondary);
        }

        /* 对账微调小弹窗 */
        .adjust-modal-card {
            max-width: 540px;
            height: auto;
            max-height: 85vh;
        }
    """

    # 替换样式表部分
    # 用正则表达式匹配 `<style> ... </style>` 之间的内容，并替换为 new_css
    pattern_style = re.compile(r'(<style>).*?(</style>)', re.DOTALL)
    content_new = pattern_style.sub(r'\1' + new_css + r'\2', content)

    # 2. 替换 Body 的布局结构
    # 原先的布局是用 <aside class="sidebar">...</aside> 和 <main class="main-layout">...</main>
    # 我们将其重构为顶部浮动导航栏，和主面板大容器 <div class="main-container">
    
    # 查找原 sidebar 开始到 <main class="main-layout"> 结束的部分并进行替换
    floating_nav_html = """
    <!-- 背景发光体 -->
    <div class="glow-bg-blob blob-1"></div>
    <div class="glow-bg-blob blob-2"></div>

    <!-- 顶部浮动玻璃质感导航栏 -->
    <nav class="floating-navbar">
        <div class="navbar-brand">
            <div class="brand-logo-container">
                <i data-lucide="zap" style="color:#fff; width:16px; height:16px;"></i>
            </div>
            <div class="brand-text">
                <span class="brand-title">工地车辆对账工作台</span>
                <span class="brand-subtitle" id="header-company-sub">北京营力特建筑工程有限公司</span>
            </div>
        </div>
        
        <div class="nav-links">
            <a class="nav-item active" id="menu-monitor" onclick="switchTab('monitor')">
                <i data-lucide="tv" style="width:14px; height:14px;"></i>
                <span>多维展示大屏</span>
            </a>
            <a class="nav-item" id="menu-ledger" onclick="switchTab('ledger')">
                <i data-lucide="file-spreadsheet" style="width:14px; height:14px;"></i>
                <span>现场财务记账</span>
            </a>
            <a class="nav-item" id="menu-config" onclick="switchTab('config')">
                <i data-lucide="settings" style="width:14px; height:14px;"></i>
                <span>系统参数配置</span>
            </a>
        </div>
        
        <div class="navbar-actions">
            <!-- 日期查询选择 -->
            <div class="date-selector-wrapper">
                <span class="navbar-label">对账日期:</span>
                <input type="date" class="input-control" id="query-date-picker" style="width: 140px; height: 32px; padding: 4px 8px; font-size:12px;">
            </div>
            
            <!-- 动态导出按钮等操作区 -->
            <div id="header-actions-area" class="actions-area"></div>
            
            <!-- 主题切换 -->
            <button class="theme-toggle-btn" onclick="toggleTheme()" id="theme-toggle-btn" title="切换主题">
                <i data-lucide="moon" id="theme-toggle-icon" style="width: 15px; height: 15px;"></i>
            </button>
            
            <!-- 实时时钟 -->
            <div class="clock-display-wrapper">
                <span class="clock-display" id="live-clock">加载时钟...</span>
            </div>
        </div>
    </nav>

    <div class="main-container">
    """

    # 替换 sidebar 和 header
    # 匹配从 <!-- ------------------ 左侧侧边栏导航 ------------------ --> 到 </header>
    pattern_layout = re.compile(
        r'<!-- -+ 左侧侧边栏导航 -+ -->.*?<main class="main-layout">.*?<!-- 头部 Header -->.*?<header class="main-header">.*?</header>',
        re.DOTALL
    )
    content_new = pattern_layout.sub(floating_nav_html, content_new)
    
    # 替换 </main> 闭合标签为 </div>
    # 闭合标签在大屏的最后, 或者是 panel-config 闭合之后
    # 我们匹配 `</section>\s*</main>` 并替换为 `</section>\s*</div>`
    pattern_main_close = re.compile(r'</section>\s*</main>', re.DOTALL)
    content_new = pattern_main_close.sub('</section>\n    </div>', content_new)

    # 3. JavaScript 部分的细微替换
    # 3.1 引入 `renderPlateBadge` 生成器函数
    plate_badge_js = """
        // 拟真车牌渲染器
        function renderPlateBadge(plateNo, plateColor) {
            if (!plateNo) return '-';
            plateNo = plateNo.trim().toUpperCase();
            
            let colorClass = 'plate-yellow';
            const color = (plateColor || '').trim();
            
            if (color.includes('蓝') || color.toUpperCase() === 'BLUE') {
                colorClass = 'plate-blue';
            } else if (color.includes('黄') || color.toUpperCase() === 'YELLOW') {
                colorClass = 'plate-yellow';
            } else if (color.includes('绿') || color.toUpperCase() === 'GREEN' || plateNo.length === 8) {
                colorClass = 'plate-green';
            } else if (color.includes('黑') || color.toUpperCase() === 'BLACK') {
                colorClass = 'plate-black';
            } else if (color.includes('白') || color.toUpperCase() === 'WHITE') {
                colorClass = 'plate-white';
            } else {
                if (plateNo.length === 8) {
                    colorClass = 'plate-green';
                } else {
                    colorClass = 'plate-yellow';
                }
            }
            return `<span class="plate-badge ${colorClass}"><span class="plate-inner-border"></span>${plateNo}</span>`;
        }
    """
    
    # 将 `renderPlateBadge` 插入到 `<script>` 标签的正下方
    content_new = content_new.replace("<script>", "<script>\n" + plate_badge_js)
    
    # 3.2 替换大屏和台账中的原始车牌字符渲染为 HTML 徽章渲染
    # 替换 1: 大屏通行明细 table 体
    # `<td style="font-weight:700;">${r.plate_no}</td>`
    content_new = content_new.replace(
        '<td style="font-weight:700;">${r.plate_no}</td>',
        '<td style="font-weight:700; padding: 6px 12px;">${renderPlateBadge(r.plate_no, r.plate_color)}</td>'
    )
    
    # 替换 2: 财务台账流水 table 体
    # `<td style="font-weight:700;">${r.plate_no}</td>`
    # 上面的 replace 会自动替换第一个和第二个（因为内容一致）
    
    # 替换 3: 弹窗历史全日志 table 体
    # `<td style="font-weight:700; letter-spacing:0.5px; color:var(--text-primary);">${r.plate_no}</td>`
    content_new = content_new.replace(
        '<td style="font-weight:700; letter-spacing:0.5px; color:var(--text-primary);">${r.plate_no}</td>',
        '<td style="font-weight:700; letter-spacing:0.5px; color:var(--text-primary); padding: 6px 12px;">${renderPlateBadge(r.plate_no, r.plate_color)}</td>'
    )
    
    # 替换 4: 车辆出运汇总卡片网格列表 (frequent list card) 中的车牌
    # 插入 lookup plate_color 并渲染 Badge
    old_card_js_block = """                    for (let plate in vehicleSummary) {
                        const v = vehicleSummary[plate];
                        grandTrips += v.trips;
                        grandCost += v.cost;
                        numVehicles++;

                        const warnBorder = v.unassigned > 0 ? 'border:1px solid rgba(239,68,68,0.3);' : '';
                        const unassignedBadge = v.unassigned > 0 ? `<div style="font-size:10px; color:var(--color-danger); font-weight:700; margin-top:2px;">待分账趟数: ${v.unassigned}趟</div>` : '';

                        cardsHtml += `
                            <div class="vehicle-summary-card" style="${warnBorder} cursor:pointer;" onclick="openAdjustModal('${plate}')">
                                <div class="card-plate-badge-row">
                                    <span class="card-plate-text">${plate}</span>
                                </div>"""
                                
    new_card_js_block = """                    for (let plate in vehicleSummary) {
                        const v = vehicleSummary[plate];
                        grandTrips += v.trips;
                        grandCost += v.cost;
                        numVehicles++;

                        const warnBorder = v.unassigned > 0 ? 'border:1px solid rgba(239,68,68,0.2); box-shadow: 0 4px 12px rgba(239,68,68,0.08);' : '';
                        const unassignedBadge = v.unassigned > 0 ? `<div style="font-size:10px; color:var(--color-danger); font-weight:700; margin-top:2px;">待分账趟数: ${v.unassigned}趟</div>` : '';

                        // 查找车牌的颜色
                        const matchedVeh = currentFrequentPlatesList.find(p => p.plate_no === plate);
                        const vColor = matchedVeh ? matchedVeh.plate_color : '黄色';
                        const plateBadgeHTML = renderPlateBadge(plate, vColor);

                        cardsHtml += `
                            <div class="vehicle-summary-card" style="${warnBorder} cursor:pointer;" onclick="openAdjustModal('${plate}')">
                                <div class="card-plate-badge-row">
                                    <span class="card-plate-text">${plateBadgeHTML}</span>
                                </div>"""
                                
    content_new = content_new.replace(old_card_js_block, new_card_js_block)

    # 4. SVG 趋势图表折线图优化（添加呼吸发光气泡与平滑圆角）
    old_svg_js = """                // Draw Trips line with area fill
                let polyTrips = [];
                let areaPoints = [`${padL},${padT + plotH}`];
                daily.forEach((d, idx) => {
                    const x = padL + idx * dx;
                    const y = padT + plotH - (d.trips / maxTrips) * plotH;
                    polyTrips.push(`${x},${y}`);
                    areaPoints.push(`${x},${y}`);
                });
                areaPoints.push(`${padL + (N - 1) * dx},${padT + plotH}`);

                if (polyTrips.length > 0) {
                    // Fill Area
                    svg += `<polygon points="${areaPoints.join(' ')}" fill="url(#areaGrad)" opacity="0.15" />`;
                    // Line
                    svg += `<path d="M ${polyTrips.join(' L ')}" fill="none" stroke="url(#lineGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />`;
                    
                    // Draw circles on nodes
                    daily.forEach((d, idx) => {
                        const [x, y] = polyTrips[idx].split(',');
                        svg += `
                        <circle cx="${x}" cy="${y}" r="3.5" fill="var(--chart-node-fill, #10b981)" stroke="var(--card-bg)" stroke-width="1.5" style="cursor:pointer; transition: r 0.2s;"
                            onmouseover="this.setAttribute('r', '6'); window.showChartTooltip(event, '${d.day_date}', ${d.trips}, ${d.cost})" 
                            onmouseout="this.setAttribute('r', '3.5'); window.hideChartTooltip()">
                        </circle>`;
                    });
                }"""
                
    new_svg_js = """                // Draw Trips line with area fill
                let polyTrips = [];
                let areaPoints = [`${padL},${padT + plotH}`];
                daily.forEach((d, idx) => {
                    const x = padL + idx * dx;
                    const y = padT + plotH - (d.trips / maxTrips) * plotH;
                    polyTrips.push(`${x},${y}`);
                    areaPoints.push(`${x},${y}`);
                });
                areaPoints.push(`${padL + (N - 1) * dx},${padT + plotH}`);

                if (polyTrips.length > 0) {
                    // Fill Area
                    svg += `<polygon points="${areaPoints.join(' ')}" fill="url(#areaGrad)" opacity="0.12" />`;
                    
                    // Shadow glow path under line
                    svg += `<path d="M ${polyTrips.join(' L ')}" fill="none" stroke="url(#lineGrad)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0.2" style="filter: url(#glow-filter);" />`;
                    
                    // Line
                    svg += `<path d="M ${polyTrips.join(' L ')}" fill="none" stroke="url(#lineGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />`;
                    
                    // Draw circles on nodes with halo glow ring
                    daily.forEach((d, idx) => {
                        const [x, y] = polyTrips[idx].split(',');
                        svg += `
                        <!-- Outer halo ring -->
                        <circle cx="${x}" cy="${y}" r="5" fill="none" stroke="var(--chart-node-fill, #6366f1)" stroke-width="2.5" opacity="0" class="svg-halo-${idx}" style="pointer-events:none; transition: opacity 0.2s;" />
                        <!-- Core interactive node -->
                        <circle cx="${x}" cy="${y}" r="3.5" fill="var(--chart-node-fill, #6366f1)" stroke="var(--card-bg)" stroke-width="1.5" style="cursor:pointer; transition: r 0.2s;"
                            onmouseover="this.setAttribute('r', '5.5'); document.querySelector('.svg-halo-${idx}').style.opacity='0.6'; window.showChartTooltip(event, '${d.day_date}', ${d.trips}, ${d.cost})" 
                            onmouseout="this.setAttribute('r', '3.5'); document.querySelector('.svg-halo-${idx}').style.opacity='0'; window.hideChartTooltip()">
                        </circle>`;
                    });
                }"""
                
    content_new = content_new.replace(old_svg_js, new_svg_js)

    # 4.1 在折线图定义 defs 中，加入模糊过滤器 glow-filter
    old_defs = """                    <defs>
                        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="var(--chart-area-start, #10b981)" />
                            <stop offset="100%" stop-color="var(--chart-area-end, rgba(16,185,129,0))" />
                        </linearGradient>
                        <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stop-color="var(--chart-line-start, #1ab2ab)" />
                            <stop offset="100%" stop-color="var(--chart-line-end, #0ea5e9)" />
                        </linearGradient>
                    </defs>"""
                    
    new_defs = """                    <defs>
                        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="var(--chart-area-start, #10b981)" />
                            <stop offset="100%" stop-color="var(--chart-area-end, rgba(16,185,129,0))" />
                        </linearGradient>
                        <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stop-color="var(--chart-line-start, #1ab2ab)" />
                            <stop offset="100%" stop-color="var(--chart-line-end, #0ea5e9)" />
                        </linearGradient>
                        <filter id="glow-filter" x="-20%" y="-20%" width="140%" height="140%">
                            <feGaussianBlur stdDeviation="3" result="blur" />
                            <feComposite in="SourceGraphic" in2="blur" operator="over" />
                        </filter>
                    </defs>"""
                    
    content_new = content_new.replace(old_defs, new_defs)

    # 5. 写入重构后的文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content_new)
        
    print("UI overhaul complete. templates/index.html updated successfully!")

if __name__ == "__main__":
    main()
