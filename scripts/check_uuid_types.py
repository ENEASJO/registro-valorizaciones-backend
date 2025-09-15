#!/usr/bin/env python3
"""
Script para verificar que los tipos de UUID sean correctos
"""
import ast
import sys
import os
from pathlib import Path

def check_file_for_int_conversion(file_path):
    """Busca conversiones inseguras de UUID a int"""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except:
            return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Buscar llamadas a int()
            if isinstance(node.func, ast.Name) and node.func.id == 'int':
                # Verificar si el argumento podría ser un UUID
                if node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Attribute):
                        # Algo como int(empresa.id)
                        if isinstance(arg.value, ast.Name):
                            issues.append({
                                'type': 'int_conversion',
                                'line': node.lineno,
                                'message': f'Potential UUID conversion: int({arg.value.id}.{arg.attr})',
                                'severity': 'error'
                            })
                    elif isinstance(arg, ast.Subscript):
                        # Algo como int(data['id'])
                        if isinstance(arg.value, ast.Name) and isinstance(arg.slice, ast.Constant):
                            if arg.slice.value == 'id':
                                issues.append({
                                    'type': 'int_conversion',
                                    'line': node.lineno,
                                    'message': f'Potential UUID conversion: int({arg.value.id}[{repr(arg.slice.value)}])',
                                    'severity': 'error'
                                })

    return issues

def check_schema_types(file_path):
    """Verifica que los schemas usen tipos correctos"""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar definiciones de clase con pydantic
    if 'class EmpresaResponse' in content:
        if 'id: int' in content:
            issues.append({
                'type': 'schema_type',
                'line': content.find('id: int'),
                'message': 'EmpresaResponse.id should be str, not int',
                'severity': 'error'
            })

    if 'class RepresentanteResponse' in content:
        if 'id: int' in content:
            issues.append({
                'type': 'schema_type',
                'line': content.find('id: int'),
                'message': 'RepresentanteResponse.id should be str, not int',
                'severity': 'error'
            })

    return issues

def main():
    """Función principal"""
    base_dir = Path('.')
    all_issues = []

    # Verificar archivos de rutas
    for route_file in base_dir.glob('app/api/routes/*.py'):
        print(f"Checking {route_file}")
        issues = check_file_for_int_conversion(route_file)
        all_issues.extend(issues)

    # Verificar schemas
    schema_files = [
        'app/models/empresa.py',
        'app/schemas/empresa.py'
    ]

    for schema_file in schema_files:
        if Path(schema_file).exists():
            print(f"Checking {schema_file}")
            issues = check_schema_types(schema_file)
            all_issues.extend(issues)

    # Reportar resultados
    if all_issues:
        print("\n❌ Issues found:")
        for issue in all_issues:
            print(f"  Line {issue['line']}: {issue['message']}")
        print("\nPlease fix these issues before committing")
        sys.exit(1)
    else:
        print("✅ No UUID type issues found")
        sys.exit(0)

if __name__ == "__main__":
    main()