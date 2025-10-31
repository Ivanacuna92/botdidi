================================================================================
                        BOT DIDI - GUIA DE USO
================================================================================

VERSION: 1.0
FECHA: Octubre 2025

================================================================================
REQUISITOS DEL SISTEMA
================================================================================

✓ Windows 10 o Windows 11 (64 bits)
✓ Google Chrome instalado (cualquier version reciente)
✓ Conexion a Internet
✓ Clave de licencia valida (formato: DIDI-XXXX-XXXX-XXXX)


================================================================================
INSTALACION
================================================================================

1. DESCARGAR
   - Descarga el archivo BotDidi.exe
   - Tamano aproximado: 150-180 MB

2. COLOCAR EN UNA CARPETA
   - Crea una carpeta (ejemplo: C:\BotDidi\)
   - Copia BotDidi.exe dentro de esa carpeta
   - No es necesario instalar nada mas

3. PRIMERA EJECUCION
   - Haz doble clic en BotDidi.exe
   - Windows Defender podria mostrar una advertencia (ver seccion SOLUCIONAR PROBLEMAS)


================================================================================
PRIMERA VEZ - ACTIVACION DE LICENCIA
================================================================================

Al ejecutar por primera vez, veras la pantalla de "Activacion de Licencia":

1. INFORMACION DE TU MAQUINA
   - El programa muestra automaticamente:
     * Nombre de tu computadora
     * Usuario del sistema
     * Hardware ID (identificador unico)

2. INGRESAR CLAVE DE LICENCIA
   - Escribe tu clave en el formato: XXXX-XXXX-XXXX
   - El programa agregara automaticamente el prefijo "DIDI-"
   - Ejemplo: Si tu clave es "A3F2-9B7E-4C12", escribela asi

3. ACTIVAR
   - Haz clic en "ACTIVAR LICENCIA"
   - El sistema validara tu clave con el servidor
   - Si es valida, quedara activada permanentemente en esta maquina

4. IMPORTANTE
   - Cada clave solo se puede activar en UNA maquina
   - Una vez activada, no necesitas volver a ingresarla
   - No se puede transferir a otra computadora


================================================================================
INICIO DE SESION
================================================================================

Despues de activar la licencia, veras la pantalla de login:

1. CREDENCIALES
   - Usuario: [proporcionado por el administrador]
   - Contrasena: [proporcionada por el administrador]

2. INICIAR SESION
   - Ingresa tus credenciales
   - Haz clic en "INICIAR SESION"
   - El sistema validara tu acceso


================================================================================
USO NORMAL DEL BOT
================================================================================

Una vez dentro, veras la pantalla principal:

1. PANTALLA PRINCIPAL
   - Estado del bot (LISTO / PROCESANDO)
   - Botones de control (INICIAR / DETENER)
   - Estadisticas en vivo
   - Log de actividad

2. INICIAR EL BOT
   a) Haz clic en "INICIAR BOT"
   b) El sistema iniciara el servidor backend
   c) Abrira Chrome automaticamente
   d) Si no estas logueado en Didi:
      - Completa el login manualmente en Chrome
      - El bot detectara cuando termines
      - Esperara hasta 5 minutos
   e) Una vez logueado, comenzara el procesamiento automatico

3. DURANTE EL PROCESAMIENTO
   - Veras el progreso en tiempo real:
     * Clientes procesados
     * Exitosos
     * Errores
     * Pagina actual
   - El log mostrara cada accion del bot
   - NO cierres Chrome mientras el bot trabaja

4. DETENER EL BOT
   - Haz clic en "DETENER"
   - El bot terminara el cliente actual
   - Guardara todo el progreso
   - Podras reiniciar cuando quieras

5. VER REPORTES
   - "Ver Estadisticas Completas": Muestra historial de 30 dias
   - "Descargar Reporte CSV": Exporta clientes procesados hoy


================================================================================
ARCHIVOS GENERADOS
================================================================================

El programa crea automaticamente estos archivos en tu computadora:

Ubicacion: C:\Users\[TuUsuario]\AppData\Roaming\BotDidi\

- DidiProfile\
  * Perfil de Chrome dedicado
  * Guarda tu sesion de Didi
  * Permite recordar el login

- .license_token
  * Token de licencia encriptado
  * Permite usar el bot sin ingresar clave cada vez

- db_config.json
  * Configuracion de la base de datos
  * Creado automaticamente en primera ejecucion


================================================================================
SOLUCIONAR PROBLEMAS
================================================================================

PROBLEMA 1: Windows Defender bloquea el programa
------------------------------------------------------
Mensaje: "Windows protegió su PC"

SOLUCION:
1. Haz clic en "Mas informacion"
2. Haz clic en "Ejecutar de todas formas"

O agregar excepcion permanente:
1. Abre Windows Security
2. Ve a "Proteccion contra virus y amenazas"
3. Clic en "Administrar configuracion"
4. Desplaza hasta "Exclusiones"
5. Agrega BotDidi.exe como excepcion

NOTA: El programa NO es un virus. Es un falso positivo comun con ejecutables Python.


PROBLEMA 2: "Error al validar licencia"
------------------------------------------------------
CAUSAS POSIBLES:
- Sin conexion a Internet
- Clave incorrecta
- Servidor temporalmente fuera de linea

SOLUCION:
1. Verifica tu conexion a Internet
2. Verifica que la clave este correcta (sin espacios extras)
3. Contacta al soporte si persiste


PROBLEMA 3: "Backend no disponible"
------------------------------------------------------
CAUSAS POSIBLES:
- El puerto 5000 esta ocupado
- Firewall bloqueando el programa

SOLUCION:
1. Cierra completamente el programa
2. Reinicia BotDidi.exe
3. Si persiste:
   - Abre el Administrador de tareas
   - Busca procesos "BotDidi.exe"
   - Finaliza todos
   - Reinicia el programa


PROBLEMA 4: "Chrome no se conecta"
------------------------------------------------------
CAUSAS POSIBLES:
- Multiples ventanas de Chrome abiertas
- Chrome en modo incognito

SOLUCION:
1. Cierra TODAS las ventanas de Chrome manualmente
2. Reinicia BotDidi.exe
3. El bot abrira Chrome automaticamente


PROBLEMA 5: El bot pierde la sesion de Didi
------------------------------------------------------
CAUSA:
- Didi cerro sesion automaticamente (por tiempo)

SOLUCION:
1. Detén el bot
2. Vuelve a iniciar
3. Completa el login cuando te lo pida
4. El bot continuara automaticamente


PROBLEMA 6: Errores al procesar clientes
------------------------------------------------------
Si algunos clientes fallan:
1. Revisa el log de actividad (pantalla principal)
2. Los errores se guardan automaticamente
3. Puedes ver el reporte completo con "Descargar Reporte CSV"
4. Clientes con error no afectan a los demas


================================================================================
CONSEJOS Y BUENAS PRACTICAS
================================================================================

1. INTERNET ESTABLE
   - Usa una conexion a Internet estable
   - Evita WiFi con señal debil

2. NO TOQUES CHROME
   - Mientras el bot trabaja, NO cierres Chrome
   - NO cambies de pestañas manualmente
   - Deja que el bot haga su trabajo

3. REVISION PERIODICA
   - Revisa el log de vez en cuando
   - Verifica que no haya errores repetitivos

4. CERRAR CORRECTAMENTE
   - Usa el boton "DETENER" antes de cerrar
   - No cierres el programa abruptamente

5. ACTUALIZACIONES
   - Cuando recibas una nueva version (BotDidi_v1.1.exe):
     * Cierra la version anterior
     * Ejecuta la nueva version
     * Tu licencia y datos se mantienen


================================================================================
PREGUNTAS FRECUENTES
================================================================================

P: ¿Necesito instalar Python?
R: NO. El .exe incluye todo lo necesario.

P: ¿Puedo usar el bot en varias computadoras?
R: NO. Cada licencia solo funciona en UNA maquina.

P: ¿Que pasa si cambio de computadora?
R: Necesitaras una nueva licencia. Contacta al administrador.

P: ¿El bot funciona con Chrome en modo incognito?
R: NO. Usa Chrome normal.

P: ¿Puedo usar Chrome para otras cosas mientras el bot trabaja?
R: NO RECOMENDADO. Deja que el bot use Chrome exclusivamente.

P: ¿Se guardan los datos si cierro el programa?
R: SI. Todo se guarda en la base de datos automaticamente.

P: ¿Cuanto tiempo tarda en procesar clientes?
R: Depende de cuantos sean. Aproximadamente 30-60 segundos por cliente.

P: ¿El bot funciona sin Internet?
R: NO. Necesita Internet para:
   - Conectarse a Didi
   - Validar licencia
   - Guardar en base de datos


================================================================================
SOPORTE TECNICO
================================================================================

Si tienes problemas que no se resuelven con esta guia:

1. RECOPILA INFORMACION
   - Captura de pantalla del error
   - Texto completo del mensaje de error
   - Lo que estabas haciendo cuando ocurrio

2. CONTACTA AL ADMINISTRADOR
   - Proporciona la informacion recopilada
   - Menciona tu clave de licencia
   - Describe los pasos para reproducir el problema


================================================================================
INFORMACION DE VERSION
================================================================================

Version:        1.0
Fecha:          Octubre 2025
Plataforma:     Windows 10/11 (64 bits)
Desarrollador:  [Tu nombre/empresa]


================================================================================
                              FIN DEL MANUAL
================================================================================
