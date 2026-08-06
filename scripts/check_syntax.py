import py_compile
py_compile.compile('/opt/data/stock-web-system/backend/app/services/analysis_service.py', doraise=True)
print('analysis_service.py: OK')

py_compile.compile('/opt/data/stock-web-system/backend/app/api/analysis.py', doraise=True)
print('analysis.py: OK')
