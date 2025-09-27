#!/usr/bin/env python3
"""
🧹 Script para limpiar caracteres problemáticos de encoding en archivos Python
"""

import re
import sys
from pathlib import Path

def clean_file_encoding(file_path):
    """
    Limpia caracteres problemáticos de un archivo Python
    """
    print(f"🧹 Limpiando encoding de: {file_path}")
    
    try:
        # Leer el archivo con diferentes encodings
        content = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ Archivo leído con encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"❌ No se pudo leer el archivo con ningún encoding")
            return False
        
        # Diccionario de reemplazos de emojis problemáticos
        emoji_replacements = {
            '📦': '[LOADING]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            'ℹ️': '[INFO]',
            '🚀': '[STARTING]',
            '🌐': '[WEB]',
            '🔍': '[SEARCH]',
            '⚡': '[FAST]',
            '🎯': '[TARGET]',
            '🔄': '[REFRESH]',
            '🎉': '[SUCCESS]',
        }
        
        # Contar reemplazos
        total_replacements = 0
        
        # Reemplazar cada emoji
        for emoji, replacement in emoji_replacements.items():
            count = content.count(emoji)
            if count > 0:
                content = content.replace(emoji, replacement)
                total_replacements += count
                print(f"  - Reemplazado '{emoji}' → '{replacement}' ({count} veces)")
        
        # También limpiar otros caracteres problemáticos usando regex
        # Remover caracteres no-ASCII excepto espacios y caracteres básicos
        content_clean = re.sub(r'[^\x00-\x7F\xC0-\xFF]', '', content)
        
        if content != content_clean:
            print(f"  - Removidos caracteres no-ASCII adicionales")
            content = content_clean
            total_replacements += 1
        
        if total_replacements > 0:
            # Escribir el archivo limpio
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Archivo limpiado exitosamente ({total_replacements} cambios)")
            return True
        else:
            print(f"ℹ️  No se encontraron caracteres problemáticos")
            return True
            
    except Exception as e:
        print(f"❌ Error limpiando archivo: {e}")
        return False

def main():
    """Limpiar main.py y otros archivos críticos"""
    
    print("🧹 LIMPIEZA DE ENCODING PARA DEPLOYMENT")
    print("=" * 50)
    
    # Archivos críticos para deployment
    critical_files = [
        'main.py',
        'app/core/database.py', 
        'app/models/empresa.py'
    ]
    
    success_count = 0
    total_files = 0
    
    for file_path in critical_files:
        if Path(file_path).exists():
            total_files += 1
            if clean_file_encoding(file_path):
                success_count += 1
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESUMEN: {success_count}/{total_files} archivos procesados exitosamente")
    
    if success_count == total_files:
        print("🎉 ¡Todos los archivos críticos están limpios!")
        return True
    else:
        print("❌ Algunos archivos tuvieron problemas")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)