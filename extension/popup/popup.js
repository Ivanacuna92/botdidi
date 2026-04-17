/**
 * Popup - Interfaz de usuario de la extension
 * Flujo: Activacion de licencia -> Login -> Bot
 */

// =====================================================================
// INICIALIZACION
// =====================================================================

document.addEventListener('DOMContentLoaded', async () => {
    const data = await chrome.storage.local.get([
        'licenciaClave', 'authToken', 'usuario', 'logs', 'stats', 'botStatus', 'tipoRecorrido',
        'plantillaWa', 'plantillaSms'
    ]);

    // Flujo: licencia -> login -> main
    if (!data.licenciaClave) {
        // Sin licencia: mostrar activacion
        showActivationView();
    } else if (!data.authToken || !data.usuario) {
        // Con licencia pero sin login: validar licencia y mostrar login
        const valid = await revalidarLicencia(data.licenciaClave);
        if (valid) {
            showLoginView();
        } else {
            // Licencia invalida: pedir nueva
            await chrome.storage.local.remove(['licenciaClave']);
            showActivationView();
        }
    } else {
        // Con licencia y login: validar licencia y mostrar main
        const valid = await revalidarLicencia(data.licenciaClave);
        if (valid) {
            showMainView(data.usuario);
            if (data.tipoRecorrido) {
                document.getElementById('tipo-recorrido').value = data.tipoRecorrido;
            }
            restoreTemplateInputs(data.tipoRecorrido || 'CreditCard', data.plantillaWa, data.plantillaSms);
            updateStats(data.stats);
            updateLogs(data.logs);
            updateBotStatus(data.botStatus);
        } else {
            await chrome.storage.local.remove(['licenciaClave', 'authToken', 'usuario']);
            showActivationView();
        }
    }

    // Escuchar cambios en storage
    chrome.storage.onChanged.addListener((changes, area) => {
        if (area !== 'local') return;
        if (changes.logs) updateLogs(changes.logs.newValue);
        if (changes.stats) updateStats(changes.stats.newValue);
        if (changes.botStatus) updateBotStatus(changes.botStatus.newValue);
    });

    // Event listeners
    document.getElementById('btn-activate').addEventListener('click', handleActivation);
    document.getElementById('btn-login').addEventListener('click', handleLogin);
    document.getElementById('btn-start').addEventListener('click', handleStart);
    document.getElementById('btn-stop').addEventListener('click', handleStop);
    document.getElementById('btn-export').addEventListener('click', handleExport);
    document.getElementById('btn-logout').addEventListener('click', handleLogout);

    // Enter keys
    document.getElementById('license-key').addEventListener('keydown', e => {
        if (e.key === 'Enter') handleActivation();
    });
    document.getElementById('username').addEventListener('keydown', e => {
        if (e.key === 'Enter') handleLogin();
    });
    document.getElementById('password').addEventListener('keydown', e => {
        if (e.key === 'Enter') handleLogin();
    });

    // Auto-formato de clave de licencia
    document.getElementById('license-key').addEventListener('input', formatLicenseKey);

    // Guardar tipo de recorrido cuando cambie y actualizar plantillas por defecto
    document.getElementById('tipo-recorrido').addEventListener('change', (e) => {
        const tipo = e.target.value;
        chrome.storage.local.set({ tipoRecorrido: tipo });
        const defaults = getDefaultTemplates(tipo);
        document.getElementById('plantilla-wa').value = defaults.wa;
        document.getElementById('plantilla-sms').value = defaults.sms;
        chrome.storage.local.set({ plantillaWa: defaults.wa, plantillaSms: defaults.sms });
    });

    // Guardar plantillas cuando cambien
    document.getElementById('plantilla-wa').addEventListener('change', (e) => {
        chrome.storage.local.set({ plantillaWa: e.target.value.trim() });
    });
    document.getElementById('plantilla-sms').addEventListener('change', (e) => {
        chrome.storage.local.set({ plantillaSms: e.target.value.trim() });
    });
});

// =====================================================================
// VISTAS
// =====================================================================

function showActivationView() {
    document.getElementById('activation-view').style.display = 'block';
    document.getElementById('login-view').style.display = 'none';
    document.getElementById('main-view').style.display = 'none';
    document.getElementById('license-key').focus();
}

function showLoginView() {
    document.getElementById('activation-view').style.display = 'none';
    document.getElementById('login-view').style.display = 'block';
    document.getElementById('main-view').style.display = 'none';
    document.getElementById('username').focus();
}

function showMainView(usuario) {
    document.getElementById('activation-view').style.display = 'none';
    document.getElementById('login-view').style.display = 'none';
    document.getElementById('main-view').style.display = 'block';
    const nombre = usuario.nombre_completo || usuario.username;
    document.getElementById('user-info').textContent = `${nombre} (${usuario.rol || 'operador'})`;
}

// =====================================================================
// FORMATO DE CLAVE
// =====================================================================

function formatLicenseKey() {
    const input = document.getElementById('license-key');
    let text = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');

    // Limitar a 16 caracteres (DIDI + 12 chars)
    text = text.substring(0, 16);

    // Insertar guiones cada 4 caracteres
    const parts = [];
    for (let i = 0; i < text.length; i += 4) {
        parts.push(text.substring(i, i + 4));
    }

    const formatted = parts.join('-');
    const cursorPos = input.selectionStart;
    input.value = formatted;

    // Restaurar cursor
    const newPos = Math.min(cursorPos, formatted.length);
    input.setSelectionRange(newPos, newPos);
}

// =====================================================================
// PLANTILLAS POR DEFECTO
// =====================================================================

const TEMPLATE_DEFAULTS = {
    CreditCard: {
        wa: 'MXCC_CM5_wa_Acuerdo Abril_01',
        sms: 'MXCC_CM2_sms_Promesa Rota Abril_01'
    },
    Loan: {
        wa: 'MXCL_M4_wa_Requerimiento Abril_01',
        sms: 'MXCL_M5-6_sms_Seguimiento Abril_01'
    }
};

function getDefaultTemplates(tipo) {
    return TEMPLATE_DEFAULTS[tipo] || TEMPLATE_DEFAULTS.CreditCard;
}

function restoreTemplateInputs(tipo, savedWa, savedSms) {
    const defaults = getDefaultTemplates(tipo);
    document.getElementById('plantilla-wa').value = savedWa || defaults.wa;
    document.getElementById('plantilla-sms').value = savedSms || defaults.sms;
}

// =====================================================================
// REVALIDACION DE LICENCIA (cada vez que se abre el popup)
// =====================================================================

async function revalidarLicencia(clave) {
    try {
        const response = await chrome.runtime.sendMessage({
            type: 'validateLicense',
            clave
        });
        return response.status === 'ok';
    } catch {
        // Si no hay conexion, permitir uso temporal
        return true;
    }
}

// =====================================================================
// ACTUALIZACION DE UI
// =====================================================================

function updateStats(stats) {
    if (!stats) return;
    document.getElementById('stat-total').textContent = stats.total || 0;
    document.getElementById('stat-exitosos').textContent = stats.exitosos || 0;
    document.getElementById('stat-errores').textContent = stats.errores || 0;
    document.getElementById('stat-pagina').textContent = stats.pagina || 0;
}

function updateLogs(logs) {
    if (!logs) return;
    const logEl = document.getElementById('log');
    logEl.innerHTML = '';

    logs.forEach(msg => {
        const line = document.createElement('div');
        line.className = 'log-line';
        if (msg.includes('[ERROR]')) line.classList.add('log-error');
        else if (msg.includes('[OK]')) line.classList.add('log-success');
        else if (msg.includes('[!]')) line.classList.add('log-warning');
        line.textContent = msg;
        logEl.appendChild(line);
    });

    logEl.scrollTop = logEl.scrollHeight;
}

function updateBotStatus(status) {
    const statusEl = document.getElementById('status');
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');

    if (status === 'running') {
        statusEl.textContent = 'PROCESANDO';
        statusEl.className = 'status-running';
        btnStart.disabled = true;
        btnStop.disabled = false;
    } else {
        statusEl.textContent = 'LISTO';
        statusEl.className = 'status-idle';
        btnStart.disabled = false;
        btnStop.disabled = true;
    }
}

// =====================================================================
// HANDLERS
// =====================================================================

async function handleActivation() {
    let clave = document.getElementById('license-key').value.trim().toUpperCase();
    const errorEl = document.getElementById('activation-error');
    const btn = document.getElementById('btn-activate');

    if (!clave) {
        errorEl.textContent = 'Ingrese una clave de licencia';
        return;
    }

    // Agregar prefijo DIDI- si no lo tiene
    if (!clave.startsWith('DIDI-')) {
        clave = `DIDI-${clave}`;
    }

    // Validar formato
    const formatoValido = /^DIDI-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(clave);
    if (!formatoValido) {
        errorEl.textContent = 'Formato invalido. Use: DIDI-XXXX-XXXX-XXXX';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'VALIDANDO...';
    errorEl.textContent = '';

    try {
        const response = await chrome.runtime.sendMessage({
            type: 'activateLicense',
            clave
        });

        if (response.status === 'ok') {
            await chrome.storage.local.set({ licenciaClave: clave });
            showLoginView();
        } else {
            errorEl.textContent = response.message || 'Clave invalida';
        }
    } catch (e) {
        errorEl.textContent = `Error de conexion: ${e.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'ACTIVAR LICENCIA';
    }
}

async function handleLogin() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('login-error');
    const btn = document.getElementById('btn-login');

    if (!username || !password) {
        errorEl.textContent = 'Complete todos los campos';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'VERIFICANDO...';
    errorEl.textContent = '';

    try {
        // Obtener la clave de licencia almacenada
        const data = await chrome.storage.local.get(['licenciaClave']);

        const response = await chrome.runtime.sendMessage({
            type: 'login',
            username,
            password,
            licenciaClave: data.licenciaClave
        });

        if (response.status === 'ok') {
            showMainView(response.usuario);
        } else {
            errorEl.textContent = response.message || 'Credenciales invalidas';
        }
    } catch (e) {
        errorEl.textContent = `Error: ${e.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'INICIAR SESION';
    }
}

async function handleStart() {
    const tipoRecorrido = document.getElementById('tipo-recorrido').value;
    const plantillaWa = document.getElementById('plantilla-wa').value.trim();
    const plantillaSms = document.getElementById('plantilla-sms').value.trim();

    if (!plantillaWa || !plantillaSms) {
        alert('Debe ingresar ambas plantillas (WhatsApp y SMS)');
        return;
    }

    // Guardar plantillas actuales
    chrome.storage.local.set({ plantillaWa, plantillaSms });

    // Buscar pestana de Pixiu
    const tabs = await chrome.tabs.query({ url: 'https://pixiu-prod.didiglobal.com/*' });

    if (tabs.length === 0) {
        const url = tipoRecorrido === 'Loan'
            ? 'https://pixiu-prod.didiglobal.com/global-fintech/loan/mx/global-pixiu-api/home#/index'
            : 'https://pixiu-prod.didiglobal.com/global-fintech/creditcard/mx/global-pixiu-api/home#/index';

        const newTab = await chrome.tabs.create({ url });

        await new Promise(resolve => {
            const listener = (tabId, info) => {
                if (tabId === newTab.id && info.status === 'complete') {
                    chrome.tabs.onUpdated.removeListener(listener);
                    resolve();
                }
            };
            chrome.tabs.onUpdated.addListener(listener);
        });

        await new Promise(r => setTimeout(r, 3000));

        await chrome.storage.local.set({
            logs: [],
            stats: { total: 0, exitosos: 0, errores: 0, pagina: 1 },
            botStatus: 'running'
        });

        chrome.tabs.sendMessage(newTab.id, {
            action: 'start',
            config: { tipoRecorrido, plantillaWa, plantillaSms }
        });
        return;
    }

    const tab = tabs[0];

    try {
        const ping = await chrome.tabs.sendMessage(tab.id, { action: 'ping' });
        if (!ping || ping.status !== 'alive') throw new Error('No responde');
    } catch {
        alert('El content script no responde.\nRecarga la pagina de Pixiu e intenta de nuevo.');
        return;
    }

    await chrome.storage.local.set({
        logs: [],
        stats: { total: 0, exitosos: 0, errores: 0, pagina: 1 },
        botStatus: 'running'
    });
    updateLogs([]);
    updateStats({ total: 0, exitosos: 0, errores: 0, pagina: 1 });
    updateBotStatus('running');

    chrome.tabs.sendMessage(tab.id, {
        action: 'start',
        config: { tipoRecorrido, plantillaWa, plantillaSms }
    });

    chrome.tabs.update(tab.id, { active: true });
}

async function handleStop() {
    if (!confirm('Seguro que quieres detener el bot?')) return;

    const tabs = await chrome.tabs.query({ url: 'https://pixiu-prod.didiglobal.com/*' });
    if (tabs.length > 0) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'stop' });
    }
}

async function handleExport() {
    try {
        const response = await chrome.runtime.sendMessage({ type: 'getClientesHoy' });

        if (response.status !== 'ok') {
            alert(response.message || 'No se pudieron obtener los datos');
            return;
        }

        const clientes = response.clientes || [];
        if (clientes.length === 0) {
            alert('No hay clientes procesados hoy');
            return;
        }

        const fecha = new Date().toISOString().split('T')[0];
        let csv = 'REPORTE DE CLIENTES PROCESADOS\n';
        csv += `Fecha,${fecha}\n`;
        csv += `Total,${response.total}\n`;
        csv += `Exitosos,${response.exitosos}\n`;
        csv += `Errores,${response.errores}\n\n`;
        csv += 'ID,Nombre,CFRNID,Monto Total,Estado,Fecha Procesado\n';

        clientes.forEach(c => {
            const nombre = (c.nombre_cliente || '').replace(/"/g, '""');
            const cfrnid = (c.cfrnid || 'N/A').replace(/"/g, '""');
            const monto = (c.monto_total || 'N/A').replace(/"/g, '""');
            csv += `${c.id},"${nombre}","${cfrnid}","${monto}",${(c.estado || '').toUpperCase()},${c.fecha_procesado}\n`;
        });

        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Reporte_Clientes_${fecha}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (e) {
        alert(`Error: ${e.message}`);
    }
}

async function handleLogout() {
    if (!confirm('Cerrar sesion?')) return;
    await chrome.runtime.sendMessage({ type: 'logout' });
    showLoginView();
}
