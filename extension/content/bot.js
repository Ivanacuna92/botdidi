/**
 * Logica principal del Bot Didi
 * Traduccion directa de bot/processor.py y bot/navigator.py
 */
const DidiBot = {
    running: false,
    shouldStop: false,
    config: { tipoRecorrido: 'CreditCard' },
    stats: { total: 0, exitosos: 0, errores: 0, pagina: 1 },

    // =====================================================================
    // COMUNICACION
    // =====================================================================

    log(msg) {
        const ts = new Date().toLocaleTimeString('es-MX', { hour12: false });
        chrome.runtime.sendMessage({ type: 'log', message: `[${ts}] ${msg}` });
    },

    updateStats() {
        chrome.runtime.sendMessage({ type: 'statsUpdate', stats: { ...this.stats } });
    },

    sendStatus(status) {
        chrome.runtime.sendMessage({ type: 'statusUpdate', status });
    },

    // =====================================================================
    // NAVEGACION (equivalente a bot/navigator.py)
    // =====================================================================

    async navegarAMisCasos() {
        this.log('[*] Navegando al dashboard...');

        // Verificar que el menu principal exista (usuario logueado)
        await BotUtils.waitForElement(
            "//ul[@role='menubar' and contains(@class, 'el-menu')]"
        );

        // Expandir Mesa de trabajo
        await BotUtils.waitAndClick(
            "//div[@class='el-submenu__title']//span[contains(@title, 'Mesa de trabajo')]"
        );
        await BotUtils.sleep(1500);

        // Expandir Mis casos
        await BotUtils.waitAndClick(
            "//div[@class='nest-menu']//div[@class='el-submenu__title']//span[@title='Mis casos']"
        );
        await BotUtils.sleep(1500);

        // Click en link final
        await BotUtils.waitAndClick(
            "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']"
        );
        await BotUtils.sleep(2000);

        this.log('[OK] Navegacion completada');
    },

    // =====================================================================
    // GESTION DE PESTANAS
    // =====================================================================

    async cerrarPestanasDetalles() {
        try {
            const botonCerrar = BotUtils.findByXPath(
                "//span[contains(@class, 'tags-view-item') and contains(., 'Detalles del lead')]//span[contains(@class, 'el-icon-close')]"
            );
            if (botonCerrar) {
                await BotUtils.clickElement(botonCerrar);
                this.log('[OK] Pestana de detalles previa cerrada');
                await BotUtils.sleep(1000);
                return true;
            }
        } catch {
            try {
                const link = BotUtils.findByXPath(
                    "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']"
                );
                if (link) {
                    link.click();
                    await BotUtils.sleep(2000);
                }
            } catch { /* ignorar */ }
        }
        return false;
    },

    navegar_a_mis_casos_fallback() {
        try {
            const link = BotUtils.findByXPath(
                "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']"
            );
            if (link) link.click();
        } catch { /* ignorar */ }
    },

    // =====================================================================
    // SELECCION DE PLANTILLA WHATSAPP (navegacion carrusel)
    // =====================================================================

    async seleccionarCarpetaWa(plantillaWa) {
        this.log(`[*] Buscando plantilla '${plantillaWa}'...`);

        // Buscar la carpeta target en el DOM
        const findTarget = () => {
            const carpetas = document.querySelectorAll('.wa-folder');
            return Array.from(carpetas).find(c => c.textContent.trim().includes(plantillaWa));
        };

        // Verificar si la carpeta target esta activa
        const isTargetActive = () => {
            const active = document.querySelector('.wa-folder.folder-active');
            return active && active.textContent.trim().includes(plantillaWa);
        };

        let target = findTarget();
        if (!target) {
            this.log(`[!] Plantilla '${plantillaWa}' no existe en el DOM`);
            return;
        }

        // Diagnostico: ver estructura del carrusel
        const container = document.querySelector('.wa-folder-main');
        if (container) {
            this.log(`[DEBUG] Container: scrollWidth=${container.scrollWidth}, clientWidth=${container.clientWidth}, overflow=${getComputedStyle(container).overflow}`);
        }

        // Listar todas las carpetas para ver que hay
        const todasCarpetas = document.querySelectorAll('.wa-folder');
        this.log(`[DEBUG] Total carpetas en DOM: ${todasCarpetas.length}`);
        todasCarpetas.forEach((c, i) => {
            const isActive = c.classList.contains('folder-active') ? ' [ACTIVE]' : '';
            this.log(`[DEBUG]   ${i}: '${c.textContent.trim().substring(0, 50)}'${isActive}`);
        });

        // Diagnostico: ver estructura HTML de las flechas
        const containerEl = document.querySelector('.wa-folder-container');
        if (containerEl) {
            const rightIcon = containerEl.querySelector('.el-icon-caret-right');
            const leftIcon = containerEl.querySelector('.el-icon-caret-left');
            if (rightIcon) {
                this.log(`[DEBUG] Flecha derecha: tag=${rightIcon.tagName}, parent=${rightIcon.parentElement.tagName}.${rightIcon.parentElement.className}`);
            }
            if (leftIcon) {
                this.log(`[DEBUG] Flecha izquierda: tag=${leftIcon.tagName}, parent=${leftIcon.parentElement.tagName}.${leftIcon.parentElement.className}`);
            }
        }

        // ============================================================
        // ESTRATEGIA 1: Scroll directo del contenedor + click
        // ============================================================
        if (container && target) {
            this.log('[DEBUG] Intentando scroll directo del contenedor...');

            // Calcular posicion del target relativa al contenedor
            const targetLeft = target.offsetLeft;
            const containerWidth = container.clientWidth;

            // Scroll para centrar el target
            container.scrollLeft = targetLeft - containerWidth / 2 + target.offsetWidth / 2;
            await BotUtils.sleep(500);
            this.log(`[DEBUG] scrollLeft set to ${container.scrollLeft}`);

            // Tambien probar scrollTo
            container.scrollTo({ left: targetLeft - 50, behavior: 'smooth' });
            await BotUtils.sleep(800);

            // Click en el target
            await BotUtils.clickElement(target);
            await BotUtils.sleep(800);

            if (isTargetActive()) {
                this.log(`[OK] Plantilla '${plantillaWa}' seleccionada (scroll directo)`);
                return;
            }
        }

        // ============================================================
        // ESTRATEGIA 2: scrollIntoView con inline
        // ============================================================
        this.log('[DEBUG] Intentando scrollIntoView inline...');
        target = findTarget();
        if (target) {
            target.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' });
            await BotUtils.sleep(800);

            await BotUtils.clickElement(target);
            await BotUtils.sleep(800);

            if (isTargetActive()) {
                this.log(`[OK] Plantilla '${plantillaWa}' seleccionada (scrollIntoView)`);
                return;
            }
        }

        // ============================================================
        // ESTRATEGIA 3: Flechas del carrusel (multiples niveles de click)
        // ============================================================
        this.log('[DEBUG] Intentando con flechas del carrusel...');
        if (containerEl) {
            const rightIcon = containerEl.querySelector('.el-icon-caret-right');
            if (rightIcon) {
                // Intentar click en el icono, su padre, y su abuelo
                const targets = [rightIcon, rightIcon.parentElement, rightIcon.parentElement?.parentElement].filter(Boolean);

                for (const arrowEl of targets) {
                    this.log(`[DEBUG] Probando click en: ${arrowEl.tagName}.${arrowEl.className.substring(0, 40)}`);

                    for (let i = 0; i < 15; i++) {
                        // Click nativo
                        arrowEl.click();
                        await BotUtils.sleep(400);

                        // Verificar si el scroll cambio
                        if (container) {
                            this.log(`[DEBUG]   click ${i + 1}: scrollLeft=${container.scrollLeft}`);
                        }

                        target = findTarget();
                        if (target) {
                            await BotUtils.clickElement(target);
                            await BotUtils.sleep(800);

                            if (isTargetActive()) {
                                this.log(`[OK] Plantilla '${plantillaWa}' seleccionada (flecha)`);
                                return;
                            }
                        }
                    }
                }
            }
        }

        this.log(`[!] No se pudo seleccionar '${plantillaWa}' - revisar logs de diagnostico`);
    },

    // =====================================================================
    // PROCESAMIENTO DE UN REGISTRO (equivalente a bot/processor.py)
    // =====================================================================

    async procesarRegistro(indice) {
        const datosDefault = { nombre: 'DESCONOCIDO', cfrnid: 'N/A', monto_total: '0.00' };

        if (this.shouldStop) {
            return { exito: false, datos: { ...datosDefault, nombre: 'DETENIDO' } };
        }

        let nombre = 'DESCONOCIDO';
        let cfrnid = 'DESCONOCIDO';
        let monto = '0.00';

        try {
            // Cerrar pestanas previas
            await this.cerrarPestanasDetalles();

            this.log(`[*] Procesando registro #${indice + 1}`);
            await BotUtils.sleep(1000);

            // Obtener botones de detalles
            const botonesDetalles = BotUtils.findAllByXPath(
                "//td[not(contains(@class, 'is-hidden'))]//button[contains(@class, 'el-button') and .//span[text()='Detalles']]"
            );

            if (indice >= botonesDetalles.length) {
                return { exito: false, datos: { ...datosDefault, nombre: 'SIN_REGISTROS' } };
            }

            // Click en Detalles
            await BotUtils.clickElement(botonesDetalles[indice]);
            await BotUtils.sleep(3000);

            if (this.shouldStop) return { exito: false, datos: { ...datosDefault, nombre: 'DETENIDO' } };

            // ==========================================================
            // CAPTURAR DATOS DEL CLIENTE
            // ==========================================================

            try {
                // Esperar vista de detalles
                await BotUtils.waitForElement("//div[contains(@class, 'el-descriptions')]", 10000);
                this.log('[OK] Vista de detalles cargada');
                await BotUtils.sleep(1500);

                // Nombre
                try {
                    const elNombre = await BotUtils.waitForElement(
                        "//span[@class='el-descriptions-item__label has-colon ' and contains(text(), 'Nombre')]/following-sibling::span[@class='el-descriptions-item__content']",
                        15000
                    );
                    nombre = elNombre.textContent.trim();
                    this.log(`[OK] Cliente: ${nombre}`);
                } catch {
                    this.log('[!] No se pudo capturar nombre');
                }

                // cfrnid
                try {
                    const elCfrnid = BotUtils.findByXPath(
                        "//span[@class='el-descriptions-item__label has-colon ' and contains(text(), 'cfrnid')]/following-sibling::span[@class='el-descriptions-item__content']"
                    );
                    if (elCfrnid) {
                        cfrnid = elCfrnid.textContent.trim();
                        this.log(`[OK] cfrnid: ${cfrnid}`);
                    }
                } catch {
                    this.log('[!] No se pudo capturar cfrnid');
                }

                // Monto
                try {
                    const xpathMonto = this.config.tipoRecorrido === 'Loan'
                        ? "//span[@class='el-descriptions-item__label has-colon ' and contains(text(), 'Monto pendiente total')]/following-sibling::span[@class='el-descriptions-item__content']"
                        : "//span[@class='el-descriptions-item__label has-colon ' and contains(text(), 'Monto total del estado de cuenta')]/following-sibling::span[@class='el-descriptions-item__content']";
                    const elMonto = BotUtils.findByXPath(xpathMonto);
                    if (elMonto) {
                        monto = elMonto.textContent.trim();
                        this.log(`[OK] Monto: ${monto}`);
                    }
                } catch {
                    this.log('[!] No se pudo capturar monto');
                }

            } catch (e) {
                this.log(`[ERROR] Error capturando datos: ${e.message}`);
                throw e;
            }

            if (this.shouldStop) return { exito: false, datos: { nombre, cfrnid, monto_total: monto } };

            // ==========================================================
            // WHATSAPP
            // ==========================================================

            this.log('[*] Enviando WhatsApp...');
            await BotUtils.waitAndClick(
                "//button[contains(@class, 'el-button') and contains(., 'whatsapp')]"
            );
            await BotUtils.sleep(2000);

            if (this.shouldStop) return { exito: false, datos: { nombre, cfrnid, monto_total: monto } };

            // Boton plantilla
            await BotUtils.waitAndClick("//button[contains(@class, 'check-template80')]");
            await BotUtils.sleep(2000);

            // Seleccionar plantilla segun config del usuario
            await this.seleccionarCarpetaWa(this.config.plantillaWa);

            // Clickear el contenido de la plantilla
            await BotUtils.waitAndClick("//div[contains(@class, 'wa-template-content')]");
            await BotUtils.sleep(1500);

            // Boton Enviar
            const botonEnviar = await BotUtils.findButtonByText(
                "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--medium')]",
                'Enviar'
            );
            await BotUtils.clickElement(botonEnviar);
            await BotUtils.sleep(2000);

            if (this.shouldStop) return { exito: false, datos: { nombre, cfrnid, monto_total: monto } };

            // ==========================================================
            // SMS
            // ==========================================================

            this.log('[*] Enviando SMS...');
            await BotUtils.waitAndClick(
                "//button[contains(@class, 'el-button--mini') and .//span[contains(text(), 'SMS')]]"
            );
            await BotUtils.sleep(2000);

            // Seleccionar plantilla SMS segun config del usuario
            const plantillaSms = this.config.plantillaSms;
            this.log(`[*] Seleccionando plantilla SMS: ${plantillaSms}`);
            await BotUtils.waitAndClick(
                "//input[@placeholder='Seleccionar plantilla de comunicaci\u00f3n']"
            );
            await BotUtils.sleep(1000);

            // Scroll dentro del dropdown para opciones no visibles
            const opcionSms = await BotUtils.waitForElement(
                `//li[contains(@class, 'el-select-dropdown__item') and contains(., '${plantillaSms}')]`
            );
            if (opcionSms) {
                opcionSms.scrollIntoView({ block: 'nearest' });
                const ul = opcionSms.closest('.el-scrollbar__view');
                if (ul && ul.parentElement) ul.parentElement.scrollTop = opcionSms.offsetTop - 50;
                await BotUtils.sleep(300);
            }
            await BotUtils.clickElement(opcionSms);
            await BotUtils.sleep(1500);

            // Confirmar SMS
            this.log('[*] Confirmando SMS...');
            const botonConfirmarSms = await BotUtils.findButtonByText(
                "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--medium')]",
                'Confirmar'
            );
            await BotUtils.clickElement(botonConfirmarSms);
            await BotUtils.sleep(2000);
            this.log('[OK] SMS enviado');

            if (this.shouldStop) return { exito: false, datos: { nombre, cfrnid, monto_total: monto } };

            // ==========================================================
            // CODIGO DEL PAGO
            // ==========================================================

            await BotUtils.sleep(2000);
            try {
                const botonesMini = await BotUtils.waitForAllElements(
                    "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--mini')]"
                );
                const botonCodigo = botonesMini.find(
                    b => b.textContent.includes('Código del pago') || b.textContent.includes('Codigo del pago')
                );
                if (botonCodigo) {
                    await BotUtils.clickElement(botonCodigo);
                    await BotUtils.sleep(2000);
                }
            } catch {
                this.log('[!] No se encontro boton de codigo de pago');
            }

            if (this.shouldStop) return { exito: false, datos: { nombre, cfrnid, monto_total: monto } };

            // ==========================================================
            // RADIO BUTTON + CONFIRMAR
            // ==========================================================

            await BotUtils.sleep(1000);
            const radioButtons = await BotUtils.waitForAllElements("//table//input[@type='radio']");

            let radioButton;
            if (this.config.tipoRecorrido === 'Loan') {
                radioButton = radioButtons.length >= 2 ? radioButtons[1] : radioButtons[0];
                this.log('[*] Seleccionando segundo radio button (Loan)');
            } else {
                radioButton = radioButtons[0];
            }
            await BotUtils.clickElement(radioButton);
            await BotUtils.sleep(1500);

            const botonConfirmar = await BotUtils.findButtonByText(
                "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--medium')]",
                'Confirmar'
            );
            await BotUtils.clickElement(botonConfirmar);
            await BotUtils.sleep(2000);

            if (this.shouldStop) return { exito: false, datos: { nombre, cfrnid, monto_total: monto } };

            // ==========================================================
            // INFORME DE COBRO
            // ==========================================================

            this.log('[*] Clickeando botón Informe de cobro...');
            try {
                const botonesMiniInforme = await BotUtils.waitForAllElements(
                    "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--mini')]"
                );
                const botonInforme = botonesMiniInforme.find(
                    b => b.textContent.includes('Informe de cobro')
                );
                if (botonInforme) {
                    await BotUtils.clickElement(botonInforme);
                    await BotUtils.sleep(2000);

                    // Llenar número del contacto con 000 (nativeSetter para Vue reactivity)
                    this.log('[*] Llenando número del contacto...');
                    const inputNumero = await BotUtils.waitForElement(
                        "//input[@placeholder='Número del contacto']"
                    );
                    const inputSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    inputSetter.call(inputNumero, '000');
                    inputNumero.dispatchEvent(new Event('input', { bubbles: true }));
                    inputNumero.dispatchEvent(new Event('change', { bubbles: true }));
                    await BotUtils.sleep(500);
                    this.log('[OK] Número del contacto: 000');

                    // Seleccionar relación con el contacto
                    this.log('[*] Seleccionando relación con el contacto...');
                    await BotUtils.waitAndClick(
                        "//input[@placeholder='Relación con el contacto']"
                    );
                    await BotUtils.sleep(1000);
                    await BotUtils.waitAndClick(
                        "//li[contains(@class, 'el-select-dropdown__item') and contains(., 'Solicitante del crédito')]"
                    );
                    await BotUtils.sleep(500);
                    this.log('[OK] Relación: Solicitante del crédito');

                    // Seleccionar ¿Se pudo conectar la llamada?
                    this.log('[*] Seleccionando conexión de llamada...');
                    await BotUtils.waitAndClick(
                        "//input[@placeholder='¿Se pudo conectar la llamada?']"
                    );
                    await BotUtils.sleep(1000);
                    await BotUtils.waitAndClick(
                        "//li[contains(@class, 'el-select-dropdown__item') and contains(., 'No conectada')]"
                    );
                    await BotUtils.sleep(500);
                    this.log('[OK] Llamada: No conectada');

                    // Clickear "Otro"
                    await BotUtils.waitAndClick("//span[text()='Otro']");
                    await BotUtils.sleep(500);
                    this.log('[OK] Seleccionado: Otro');

                    // Llenar textarea con comentario (nativeSetter para Vue reactivity)
                    const textarea = await BotUtils.waitForElement(
                        "//label[@for='remark']/following::textarea[1]"
                    );
                    const nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLTextAreaElement.prototype, 'value'
                    ).set;
                    nativeSetter.call(textarea, 'Se envió accionamiento');
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    await BotUtils.sleep(500);
                    this.log('[OK] Comentario: Se envió accionamiento');

                    // Confirmar informe de cobro
                    const botonConfirmarInforme = await BotUtils.findButtonByText(
                        "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--medium')]",
                        'Confirmar'
                    );
                    await BotUtils.clickElement(botonConfirmarInforme);
                    await BotUtils.sleep(2000);

                    this.log('[OK] Informe de cobro completado');
                } else {
                    this.log('[!] No se encontró botón Informe de cobro');
                }
            } catch {
                this.log('[!] No se pudo clickear Informe de cobro');
            }

            // ==========================================================
            // CERRAR PESTANA DE DETALLES
            // ==========================================================

            try {
                const botonCerrarTab = await BotUtils.waitForElement(
                    "//span[contains(@class, 'tags-view-item') and contains(., 'Detalles del lead')]//span[contains(@class, 'el-icon-close')]",
                    5000
                );
                await BotUtils.clickElement(botonCerrarTab);
                await BotUtils.sleep(1000);
            } catch {
                try {
                    await BotUtils.waitAndClick(
                        "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']",
                        5000
                    );
                    await BotUtils.sleep(2000);
                } catch { /* ignorar */ }
            }

            this.log(`[OK] Registro #${indice + 1} completado - ${nombre}`);
            return { exito: true, datos: { nombre, cfrnid, monto_total: monto } };

        } catch (e) {
            // Recuperacion: volver a Mis Casos
            const errorMsg = e.message || '';
            if (errorMsg.includes('Timeout')) {
                this.log(`[ERROR] Registro #${indice + 1}: Timeout esperando elemento - ${nombre}`);
            } else {
                this.log(`[ERROR] Registro #${indice + 1}: Error procesando cliente - ${nombre}`);
            }

            this.navegar_a_mis_casos_fallback();
            await BotUtils.sleep(2000);

            return { exito: false, datos: { nombre, cfrnid, monto_total: monto } };
        }
    },

    // =====================================================================
    // LOOP PRINCIPAL (equivalente a bot/main.py)
    // =====================================================================

    async procesarTodos() {
        this.log('[*] Iniciando procesamiento masivo...');

        while (!this.shouldStop) {
            this.log(`[*] Procesando pagina ${this.stats.pagina}...`);

            // Esperar tabla
            await BotUtils.waitForElement("//table[contains(@class, 'el-table')]");
            await BotUtils.sleep(1000);

            const botonesDetalles = BotUtils.findAllByXPath(
                "//td[not(contains(@class, 'is-hidden'))]//button[contains(@class, 'el-button') and .//span[text()='Detalles']]"
            );
            const numRegistros = botonesDetalles.length;
            this.log(`[OK] ${numRegistros} registros en pagina ${this.stats.pagina}`);

            if (numRegistros === 0) break;

            for (let i = 0; i < numRegistros; i++) {
                if (this.shouldStop) break;

                this.stats.total++;
                const resultado = await this.procesarRegistro(i);

                if (resultado.exito) {
                    this.stats.exitosos++;
                } else {
                    this.stats.errores++;
                }

                // Registrar en API via service worker
                chrome.runtime.sendMessage({
                    type: 'clientProcessed',
                    data: {
                        nombre: resultado.datos.nombre,
                        cfrnid: resultado.datos.cfrnid,
                        monto_total: resultado.datos.monto_total,
                        estado: resultado.exito ? 'exitoso' : 'error'
                    }
                });

                this.updateStats();
            }

            if (this.shouldStop) break;

            // Siguiente pagina
            try {
                const iconNext = BotUtils.findByXPath(
                    "//button[contains(@class, 'btn-next') and not(@disabled)]//i[contains(@class, 'el-icon-arrow-right')]"
                );
                if (!iconNext) {
                    this.log('[OK] No hay mas paginas');
                    break;
                }
                await BotUtils.clickElement(iconNext.parentElement);
                await BotUtils.sleep(2000);
                this.stats.pagina++;
            } catch {
                this.log('[OK] No hay mas paginas');
                break;
            }
        }

        if (this.shouldStop) {
            this.log('[!] Bot detenido por el usuario');
        } else {
            this.log('[OK] PROCESAMIENTO COMPLETADO');
            this.log(`[*] Total: ${this.stats.total} | Exitosos: ${this.stats.exitosos} | Errores: ${this.stats.errores}`);
        }
    },

    // =====================================================================
    // CONTROL
    // =====================================================================

    async start(config) {
        if (this.running) {
            this.log('[!] El bot ya esta corriendo');
            return;
        }

        this.running = true;
        this.shouldStop = false;
        this.config = config;
        this.stats = { total: 0, exitosos: 0, errores: 0, pagina: 1 };
        this.sendStatus('running');
        this.updateStats();

        try {
            this.log('[*] Iniciando bot...');
            this.log(`[*] Tipo de recorrido: ${config.tipoRecorrido}`);
            this.log(`[*] Plantilla WA: ${config.plantillaWa}`);
            this.log(`[*] Plantilla SMS: ${config.plantillaSms}`);

            // Verificar URL correcta
            const currentUrl = window.location.href;
            const expectedPath = config.tipoRecorrido === 'Loan' ? '/loan/' : '/creditcard/';

            if (!currentUrl.includes(expectedPath)) {
                const targetUrl = config.tipoRecorrido === 'Loan'
                    ? 'https://pixiu-prod.didiglobal.com/global-fintech/loan/mx/global-pixiu-api/home#/index'
                    : 'https://pixiu-prod.didiglobal.com/global-fintech/creditcard/mx/global-pixiu-api/home#/index';
                this.log(`[*] Navegando a URL de ${config.tipoRecorrido}...`);
                window.location.href = targetUrl;
                await BotUtils.sleep(5000);
            }

            await this.navegarAMisCasos();
            await this.procesarTodos();

        } catch (e) {
            this.log(`[ERROR] Error critico: ${e.message}`);
        } finally {
            this.running = false;
            this.sendStatus('idle');
            this.updateStats();
        }
    },

    stop() {
        this.shouldStop = true;
        this.log('[!] Deteniendo bot...');
    }
};

// =====================================================================
// LISTENER DE MENSAJES (popup/service-worker -> content script)
// =====================================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'start') {
        DidiBot.start(message.config);
        sendResponse({ status: 'started' });
    } else if (message.action === 'stop') {
        DidiBot.stop();
        sendResponse({ status: 'stopping' });
    } else if (message.action === 'getStatus') {
        sendResponse({
            running: DidiBot.running,
            stats: DidiBot.stats
        });
    } else if (message.action === 'ping') {
        sendResponse({ status: 'alive' });
    }
    return true;
});
