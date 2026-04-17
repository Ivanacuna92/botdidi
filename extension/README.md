# Bot Didi - Extension de Chrome

## Instalacion en modo desarrollo

1. Abre Chrome y ve a `chrome://extensions`
2. Activa "Modo de desarrollador" (esquina superior derecha)
3. Click en "Cargar extension sin empaquetar"
4. Selecciona la carpeta `extension/`
5. La extension aparecera en la barra de Chrome

## Configuracion del backend

La extension necesita un backend accesible. Por defecto apunta a `http://localhost:5000`.

### Desarrollo local
```bash
cd botdidi
python backend/deploy.py
```

### Produccion
```bash
pip install gunicorn
gunicorn backend.deploy:app --bind 0.0.0.0:5000 --workers 4
```

### Cambiar URL del API
En `background/service-worker.js`, cambiar `DEFAULT_API_URL`:
```javascript
const DEFAULT_API_URL = 'https://tu-servidor.com';
```

## Uso

1. Click en el icono de la extension
2. Iniciar sesion con tu usuario
3. Seleccionar tipo de recorrido (CreditCard / Loan)
4. Click en INICIAR
5. El bot procesara los registros automaticamente
6. Exportar CSV cuando termine

## Distribucion

### Opcion A: ZIP (rapida)
Comprimir la carpeta `extension/` y distribuir el .zip

### Opcion B: Chrome Web Store (recomendada)
1. Crear cuenta de desarrollador ($5 una vez)
2. Subir como "No listada"
3. Compartir link directo a los usuarios
