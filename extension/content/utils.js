/**
 * Utilidades para interaccion con el DOM
 * Equivalente a las funciones de Selenium WebDriverWait + EC
 */
const BotUtils = {

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    findByXPath(xpath) {
        return document.evaluate(
            xpath, document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE, null
        ).singleNodeValue;
    },

    findAllByXPath(xpath) {
        const result = document.evaluate(
            xpath, document, null,
            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null
        );
        const nodes = [];
        for (let i = 0; i < result.snapshotLength; i++) {
            nodes.push(result.snapshotItem(i));
        }
        return nodes;
    },

    async waitForElement(xpath, timeout = 10000) {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = this.findByXPath(xpath);
            if (el) return el;
            await this.sleep(250);
        }
        throw new Error(`Timeout esperando elemento: ${xpath.substring(0, 80)}`);
    },

    async waitForAllElements(xpath, timeout = 10000) {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const els = this.findAllByXPath(xpath);
            if (els.length > 0) return els;
            await this.sleep(250);
        }
        throw new Error(`Timeout esperando elementos: ${xpath.substring(0, 80)}`);
    },

    async clickElement(el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        await this.sleep(500);
        // Simular secuencia real de mouse (como hace Selenium WebDriver)
        const rect = el.getBoundingClientRect();
        const opts = {
            bubbles: true, cancelable: true, view: window,
            clientX: rect.left + rect.width / 2,
            clientY: rect.top + rect.height / 2
        };
        el.dispatchEvent(new MouseEvent('mousedown', opts));
        el.dispatchEvent(new MouseEvent('mouseup', opts));
        el.click();
    },

    async waitAndClick(xpath, timeout = 10000) {
        const el = await this.waitForElement(xpath, timeout);
        await this.clickElement(el);
        return el;
    },

    async findButtonByText(xpath, texto, timeout = 10000) {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const botones = this.findAllByXPath(xpath);
            // Solo considerar botones VISIBLES y habilitados
            // (textContent devuelve texto de elementos ocultos, a diferencia de Selenium .text)
            const boton = botones.find(b =>
                b.textContent.includes(texto) &&
                b.offsetParent !== null &&
                !b.disabled
            );
            if (boton) return boton;
            await this.sleep(250);
        }
        throw new Error(`Boton con texto "${texto}" no encontrado`);
    }
};
