#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面提取工具 - 分析整個文件結構並提取所有可能的 Python 資源
"""

import os
import struct
import zlib
import marshal
import re

def analyze_file_structure(file_path):
    """分析文件結構"""
    print(f"[+] 分析文件結構: {file_path}")
    file_size = os.path.getsize(file_path)
    print(f"[+] 文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    with open(file_path, 'rb') as f:
        # 讀取 PE 頭部
        f.seek(0)
        dos_header = f.read(64)
        if dos_header[:2] != b'MZ':
            print("[!] 不是有效的 PE 文件")
            return
        
        # 讀取 PE 簽名位置
        pe_offset = struct.unpack('<I', dos_header[60:64])[0]
        f.seek(pe_offset)
        pe_signature = f.read(4)
        
        if pe_signature != b'PE\x00\x00':
            print("[!] 無效的 PE 簽名")
            return
        
        # 讀取可選頭部
        f.read(20)  # COFF 頭部
        optional_header = f.read(224)
        
        # 讀取節區表
        num_sections = struct.unpack('<H', optional_header[2:4])[0]
        print(f"[+] 節區數量: {num_sections}")
        
        sections = []
        for i in range(num_sections):
            section_header = f.read(40)
            name = section_header[:8].rstrip(b'\x00').decode('utf-8', errors='ignore')
            virtual_size = struct.unpack('<I', section_header[8:12])[0]
            virtual_addr = struct.unpack('<I', section_header[12:16])[0]
            raw_size = struct.unpack('<I', section_header[16:20])[0]
            raw_addr = struct.unpack('<I', section_header[20:24])[0]
            
            sections.append({
                'name': name,
                'virtual_size': virtual_size,
                'virtual_addr': virtual_addr,
                'raw_size': raw_size,
                'raw_addr': raw_addr
            })
        
        return sections, file_size

def search_python_data(file_path, output_dir='extracted'):
    """搜索文件中的 Python 數據"""
    print("\n[+] 搜索 Python 數據...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    file_size = os.path.getsize(file_path)
    
    # Python 相關的搜索模式
    patterns = {
        'pyc_magic': [
            b'\x42\x0d\x0d\x0a',  # Python 3.7+
            b'\x55\x0d\x0d\x0a',  # Python 3.8+
            b'\x6f\x0d\x0d\x0a',  # Python 3.9+
            b'\x16\x0d\x0d\x0a',  # Python 3.10+
            b'\xa6\x0d\x0d\x0a',  # Python 3.11+
        ],
        'python_strings': [
            b'__pycache__',
            b'.pyc',
            b'.pyo',
            b'import ',
            b'from ',
            b'def ',
            b'class ',
        ],
        'pyinstaller': [
            b'PyInstaller',
            b'MEI',
            b'PKG',
        ]
    }
    
    found_items = []
    
    # 分段讀取文件
    chunk_size = 5 * 1024 * 1024  # 5MB
    offset = 0
    
    with open(file_path, 'rb') as f:
        while offset < file_size:
            f.seek(offset)
            data = f.read(chunk_size)
            
            if not data:
                break
            
            # 搜索每個模式
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    pos = 0
                    while True:
                        pos = data.find(pattern, pos)
                        if pos == -1:
                            break
                        
                        abs_pos = offset + pos
                        found_items.append({
                            'type': pattern_type,
                            'pattern': pattern,
                            'position': abs_pos
                        })
                        pos += 1
            
            offset += chunk_size - len(pattern)  # 重疊避免跨塊
            
            if offset % (10 * 1024 * 1024) == 0:
                print(f"  處理進度: {offset / file_size * 100:.1f}%")
    
    print(f"[+] 找到 {len(found_items)} 個匹配項")
    
    # 保存結果
    results_file = os.path.join(output_dir, 'search_results.txt')
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write(f"搜索結果 - 共找到 {len(found_items)} 個匹配項\n")
        f.write("=" * 80 + "\n\n")
        
        for item in found_items[:1000]:  # 限制輸出
            f.write(f"類型: {item['type']}, 位置: 0x{item['position']:X}, 模式: {item['pattern']}\n")
    
    print(f"[+] 結果已保存到: {results_file}")
    
    # 嘗試提取可能的 .pyc 文件
    extract_pyc_from_positions(file_path, found_items, output_dir)
    
    return found_items

def extract_pyc_from_positions(file_path, items, output_dir):
    """從找到的位置提取可能的 .pyc 文件"""
    print("\n[+] 嘗試提取 .pyc 文件...")
    
    pyc_positions = [item for item in items if item['type'] == 'pyc_magic']
    
    if not pyc_positions:
        print("[!] 未找到 .pyc 魔數")
        return
    
    print(f"[+] 找到 {len(pyc_positions)} 個可能的 .pyc 位置")
    
    extracted = 0
    with open(file_path, 'rb') as f:
        for i, item in enumerate(pyc_positions[:100]):  # 限制處理數量
            try:
                pos = item['position']
                f.seek(pos)
                
                # 讀取頭部
                header = f.read(16)
                if len(header) < 16:
                    continue
                
                # 嘗試讀取代碼對象
                try:
                    code_obj = marshal.load(f)
                    if hasattr(code_obj, 'co_code') or hasattr(code_obj, 'co_name'):
                        # 保存文件
                        filename = f"pyc_{i:04d}_0x{pos:X}.pyc"
                        filepath = os.path.join(output_dir, filename)
                        
                        # 讀取完整文件（嘗試）
                        f.seek(pos)
                        data = f.read(10240)  # 讀取 10KB
                        
                        with open(filepath, 'wb') as out:
                            out.write(data)
                        
                        extracted += 1
                        if extracted % 10 == 0:
                            print(f"  [OK] 已提取 {extracted} 個文件...")
                except:
                    pass
            except Exception as e:
                continue
    
    print(f"[+] 提取完成! 共提取 {extracted} 個 .pyc 文件")

def main():
    file_path = 'spoolsv.exe'
    
    if not os.path.exists(file_path):
        print(f"[!] 文件不存在: {file_path}")
        return
    
    # 分析文件結構
    result = analyze_file_structure(file_path)
    if result:
        sections, file_size = result
        print("\n[節區信息]")
        for section in sections:
            print(f"  {section['name']}: VA=0x{section['virtual_addr']:X}, Size=0x{section['raw_size']:X}")
    
    # 搜索 Python 數據
    found_items = search_python_data(file_path)
    
    print("\n[+] 分析完成!")
    print(f"[提示] 檢查 extracted/ 目錄查看結果")
    print(f"[提示] 如果找到 .pyc 文件，使用以下命令反編譯:")
    print(f"  python decompile_pyc.py extracted/ decompiled/")

if __name__ == '__main__':
    main()

