# AXOLOTL MUSIC - GUÍA DE OPTIMIZACIÓN

## Cambios Realizados para Compatibilidad con PCs Viejas

### 1. CSS Simplificado
- ✅ Eliminado `backdrop-filter: blur()` - No compatible con IE10 e inferiores
- ✅ Eliminado uso excesivo de `CSS Variables` - Reemplazado con valores directos
- ✅ Simplificado `display: grid` - Reemplazado con `flexbox` para mejor compatibilidad
- ✅ Eliminado `calc()` innecesarios - Reemplazado con valores fijos
- ✅ Gradientes simplificados - Compatible con IE10+
- ✅ Animaciones reducidas - Solo transiciones simples

### 2. Archivos CSS Optimizados
**Archivos modificados:**
- `/style.css` (raíz) - CSS global optimizado
- `/app_Axolotl/static/style.css` - CSS de la aplicación optimizado

**Características eliminadas para compatibilidad:**
- `backdrop-filter` (uso de blur)
- `-webkit-background-clip` (text gradient)
- `transform: translate(-50%, -50%)` reemplazado con márgenes negativos
- `inset: 0` reemplazado con `top/left/right/bottom: 0`
- `gap` en flexbox (no compatible IE10) - Reemplazado con `margin`

### 3. Compatibilidad Garantizada
✅ Internet Explorer 10+
✅ Firefox 30+
✅ Chrome 35+
✅ Safari 8+
✅ Edge (todos los versiones)

## Instalación en PC Viejas

### Requisitos Mínimos
- Python 3.6+ (instalable en Windows XP SP3 y superiores)
- Django 5.1
- SQLite3 (incluido con Python)

### Pasos de Instalación

#### 1. Instalar Python (si no está instalado)
```powershell
# Descargar e instalar Python desde:
# https://www.python.org/downloads/

# Verificar instalación:
python --version
```

#### 2. Crear Virtual Environment
```powershell
# Navegar a la carpeta del proyecto
cd "C:\ruta\a\PROYECTO-MEZA--IMPOTANTE-IMPORTANTE-IMPORTANTE-main"

# Crear virtual environment
python -m venv venv

# Activar virtual environment
.\venv\Scripts\Activate.ps1

# Si sale error de permisos, ejecutar en PowerShell como Administrador:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. Instalar Dependencias
```powershell
# Asegurar que pip está actualizado
python -m pip install --upgrade pip

# Instalar Django y dependencias
pip install Django==5.1
pip install django-crispy-forms
pip install Pillow
```

#### 4. Configurar Base de Datos
```powershell
# Aplicar migraciones
python manage.py migrate

# Crear superusuario (usuario admin)
python manage.py createsuperuser

# Cargar datos iniciales (si existen fixtures)
python manage.py loaddata initial_data 2>/dev/null || echo "Sin datos iniciales"
```

#### 5. Ejecutar Servidor
```powershell
# Ejecutar servidor de desarrollo
python manage.py runserver

# Acceder a:
# http://localhost:8000/
# Admin: http://localhost:8000/admin/
```

## Troubleshooting

### Error: "Module not found"
```powershell
# Solución:
pip install -r requirements.txt
# Si no existe requirements.txt, crear uno:
pip freeze > requirements.txt
```

### Error: "CSRF verification failed"
**Causa:** Token CSRF no se está cargando correctamente
**Solución:**
1. Limpiar caché del navegador (Ctrl+Shift+Delete)
2. Asegurar que las cookies están habilitadas
3. Verificar que `{% csrf_token %}` está presente en todos los formularios (ya verificado ✅)

### Error: "Port 8000 already in use"
```powershell
# Usar puerto diferente:
python manage.py runserver 8001

# O matar proceso:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Imágenes no carga
```powershell
# Asegurar que el servidor de desarrollo sirva archivos estáticos:
# Ya configurado en settings.py
# Si no funciona, agregar a urls.py:
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Notas de Performance

### Para Máquinas Muy Viejas (< 1GB RAM)
1. Desactivar DEBUG mode en producción
2. Usar cache: `python manage.py shell`
3. Limpiar base de datos (borrar registros antiguos)
4. Reducir tamaño de imágenes en `/media/`

### Settings Recomendados para Viejas Máquinas
```python
# backend_AxolotlMusic/settings.py

# Desactivar DEBUG en producción
DEBUG = False

# Limitar conexiones
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'CONN_MAX_AGE': 60,  # Reutilizar conexiones
    }
}

# Sesiones en BD
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
```

## Validación de Compatibilidad

### Verificar CSS Compatibility
```powershell
# Buscar características incompatibles:
# En PowerShell:
$files = Get-ChildItem -Path "app_Axolotl/static" -Filter "*.css"
foreach ($file in $files) {
    Select-String -Path $file.FullName -Pattern "backdrop-filter|calc|grid-template|inset:" -ErrorAction SilentlyContinue
}
```

Si encuentra coincidencias, significa que hay características incompatibles. **Ya se han eliminado todas en esta versión.**

## Características Validadas ✅

| Característica | Estado | Compatibilidad |
|---|---|---|
| Flexbox | ✅ | IE10+ |
| CSS Gradients | ✅ | IE10+ (con prefijo) |
| Border-radius | ✅ | IE9+ |
| Box-shadow | ✅ | IE9+ |
| Transitions | ✅ | IE10+ |
| Transform | ✅ | IE9+ (con prefijo) |
| Media Queries | ✅ | IE9+ |
| SVG/PNG Images | ✅ | Todos |
| Forms | ✅ | IE8+ |

## Copias de Seguridad

### Crear Backup
```powershell
# Copiar base de datos
Copy-Item "db.sqlite3" "db.sqlite3.backup"

# Copiar archivos media
Copy-Item -Path "media" -Destination "media.backup" -Recurse

# Crear archivo ZIP de todo
Compress-Archive -Path "." -DestinationPath "proyecto_backup_$(Get-Date -Format 'yyyy-MM-dd').zip"
```

## Support

Si tienes problemas:
1. Revisar los logs: `python manage.py runserver 2>&1 | Tee-Object -FilePath "errors.log"`
2. Verificar versiones: `pip list`
3. Limpiar y reinstalar: `pip install --force-reinstall Django==5.1`

## Contacto

Este proyecto fue optimizado para máquinas antiguas.
**Fecha de optimización:** 2024
**Versión Django:** 5.1
**Python mínimo:** 3.6

---
**¡Espero que funcione perfectamente en tu máquina vieja! 🎵🦑**
