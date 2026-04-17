/**
 * Service Worker - Coordinacion y comunicacion con API
 * Maneja: autenticacion, registro de clientes, estadisticas
 */

// =====================================================================
// CONFIGURACION
// =====================================================================

// URL del servidor - HARDCODEADA para proteger el negocio
// Cambiar a la URL de produccion cuando se despliegue
const API_URL = 'http://localhost:5000';

function getApiUrl() {
    return API_URL;
}

async function getAuthToken() {
    const data = await chrome.storage.local.get(['authToken']);
    return data.authToken;
}

// =====================================================================
// LISTENER PRINCIPAL
// =====================================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    handleMessage(message, sender)
        .then(sendResponse)
        .catch(err => sendResponse({ status: 'error', message: err.message }));
    return true; // Mantener canal abierto para respuesta asincrona
});

async function handleMessage(message, sender) {
    switch (message.type) {
        case 'activateLicense':
            return await apiActivateLicense(message.clave);

        case 'validateLicense':
            return await apiValidateLicense(message.clave);

        case 'login':
            return await apiLogin(message.username, message.password, message.licenciaClave);

        case 'logout':
            await chrome.storage.local.remove([
                'authToken', 'usuario', 'logs', 'stats', 'botStatus', 'tipoRecorrido'
            ]);
            return { status: 'ok' };

        case 'log':
            await appendLog(message.message);
            return { status: 'ok' };

        case 'statsUpdate':
            await chrome.storage.local.set({ stats: message.stats });
            return { status: 'ok' };

        case 'statusUpdate':
            await chrome.storage.local.set({ botStatus: message.status });
            return { status: 'ok' };

        case 'clientProcessed':
            return await apiRegistrarCliente(message.data);

        case 'getClientesHoy':
            return await apiGetClientesHoy();

        case 'getEstadisticas':
            return await apiGetEstadisticas(message.dias || 30);

        default:
            return { status: 'error', message: `Tipo desconocido: ${message.type}` };
    }
}

// =====================================================================
// LOG EN STORAGE (persiste aunque el popup se cierre)
// =====================================================================

async function appendLog(message) {
    const data = await chrome.storage.local.get(['logs']);
    const logs = data.logs || [];
    logs.push(message);

    // Mantener maximo 500 mensajes
    if (logs.length > 500) {
        logs.splice(0, logs.length - 500);
    }

    await chrome.storage.local.set({ logs });
}

// =====================================================================
// API: LICENCIAS
// =====================================================================

async function apiActivateLicense(clave) {
    try {
        const apiUrl = getApiUrl();

        // Generar un ID unico de instalacion (reemplaza al hardware ID)
        const data = await chrome.storage.local.get(['installationId']);
        let installationId = data.installationId;
        if (!installationId) {
            installationId = 'EXT-' + crypto.randomUUID().replace(/-/g, '').substring(0, 24).toUpperCase();
            await chrome.storage.local.set({ installationId });
        }

        const response = await fetch(`${apiUrl}/licencias/activar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                clave,
                hardware_id: installationId,
                nombre_maquina: 'Chrome Extension',
                usuario_sistema: 'extension',
                hw_componentes: {
                    mac_address: 'extension',
                    hostname: 'chrome',
                    os_info: navigator.userAgent.substring(0, 50),
                    processor: navigator.platform,
                    motherboard_uuid: installationId
                }
            })
        });

        const result = await response.json();

        if (response.ok) {
            return { status: 'ok', message: result.message };
        }

        return { status: 'error', message: result.message || 'Clave invalida' };
    } catch (e) {
        return { status: 'error', message: `Error de conexion: ${e.message}` };
    }
}

async function apiValidateLicense(clave) {
    try {
        const apiUrl = getApiUrl();
        const data = await chrome.storage.local.get(['installationId']);

        if (!data.installationId) {
            return { status: 'error', message: 'Sin ID de instalacion' };
        }

        const response = await fetch(`${apiUrl}/licencias/validar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                clave,
                hardware_id: data.installationId
            })
        });

        const result = await response.json();

        if (response.ok) {
            return { status: 'ok' };
        }

        return { status: 'error', message: result.message || 'Licencia invalida' };
    } catch {
        // Sin conexion: permitir uso temporal
        return { status: 'ok' };
    }
}

// =====================================================================
// API: AUTENTICACION
// =====================================================================

async function apiLogin(username, password, licenciaClave) {
    try {
        const apiUrl = getApiUrl();

        // Validar licencia antes de login
        if (licenciaClave) {
            const licValid = await apiValidateLicense(licenciaClave);
            if (licValid.status !== 'ok') {
                return { status: 'error', message: 'Licencia invalida o revocada. Contacte al administrador.' };
            }
        }

        const response = await fetch(`${apiUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            await chrome.storage.local.set({
                authToken: data.token,
                usuario: data.usuario
            });
            return { status: 'ok', token: data.token, usuario: data.usuario };
        }

        return { status: 'error', message: data.message || 'Credenciales invalidas' };
    } catch (e) {
        return { status: 'error', message: `Error de conexion: ${e.message}` };
    }
}

// =====================================================================
// API: REGISTRAR CLIENTE
// =====================================================================

async function apiRegistrarCliente(clienteData) {
    try {
        const apiUrl = getApiUrl();
        const token = await getAuthToken();
        if (!token) return { status: 'error', message: 'Sin token de autenticacion' };

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };

        // Registrar cliente individual
        const r1 = await fetch(`${apiUrl}/registrar_cliente`, {
            method: 'POST',
            headers,
            body: JSON.stringify(clienteData)
        });

        if (!r1.ok) {
            const err = await r1.json();
            console.warn('Error registrando cliente:', err);
        }

        // Actualizar contador diario
        const esExitoso = clienteData.estado === 'exitoso';
        const r2 = await fetch(`${apiUrl}/registrar`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                clientes: 1,
                exitosos: esExitoso ? 1 : 0,
                errores: esExitoso ? 0 : 1
            })
        });

        if (!r2.ok) {
            const err = await r2.json();
            console.warn('Error actualizando contador:', err);
        }

        return { status: 'ok' };
    } catch (e) {
        console.error('Error en apiRegistrarCliente:', e);
        return { status: 'error', message: e.message };
    }
}

// =====================================================================
// API: ESTADISTICAS Y REPORTES
// =====================================================================

async function apiGetClientesHoy() {
    try {
        const apiUrl = getApiUrl();
        const token = await getAuthToken();
        if (!token) return { status: 'error', message: 'Sin token' };

        const response = await fetch(`${apiUrl}/clientes_hoy`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        return await response.json();
    } catch (e) {
        return { status: 'error', message: e.message };
    }
}

async function apiGetEstadisticas(dias) {
    try {
        const apiUrl = getApiUrl();
        const token = await getAuthToken();
        if (!token) return { status: 'error', message: 'Sin token' };

        const response = await fetch(`${apiUrl}/estadisticas?dias=${dias}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        return await response.json();
    } catch (e) {
        return { status: 'error', message: e.message };
    }
}
