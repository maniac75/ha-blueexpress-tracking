# Blue Express Tracking for Home Assistant 🇨🇱

**Integración comunitaria no oficial** para consultar el seguimiento público de [Blue Express](https://www.blue.cl/enviar/seguimiento) en Home Assistant.

**Unofficial** Home Assistant integration for the public Blue Express parcel tracker in Chile.

> No está afiliada ni respaldada por Blue Express. Usa las mismas consultas públicas que su web de seguimiento, pero **no una API oficial documentada para terceros**. Blue Express puede cambiar o limitar el servicio sin aviso. Respeta sus condiciones de uso.

## Funciones

- Añade cada envío mediante **Configuración → Dispositivos y servicios → Añadir integración → Blue Express Tracking**.
- Muestra la etapa del envío, la fecha máxima *publicada* por Blue Express y la fecha del último movimiento.
- Guarda como atributos un historial de movimientos con hora y ubicación general.
- Ignora eventos internos sin descripción (no inventa etiquetas para ellos).
- Permite múltiples paquetes: **añade la integración nuevamente** para cada número; los duplicados se rechazan.
- Permite renombrar la entidad o el dispositivo desde Home Assistant y quitar el envío eliminando su entrada de integración.
- Actualización automática cada **30 minutos**, sin reintentos agresivos. Conserva la última lectura válida y marca `stale: true` cuando falla una actualización.
- No requiere correo, clave ni API comercial.

El número debe contener **8–10 dígitos**. No todos los números de otras empresas son reconocidos por Blue Express.

## Instalación (repositorio personalizado de HACS)

1. Abre HACS → menú ⋮ → **Repositorios personalizados**.
2. Añade `https://github.com/maniac75/ha-blueexpress-tracking` con categoría **Integración**.
3. Busca **Blue Express Tracking (Chile)** e instala.
4. Reinicia Home Assistant para cargar la integración recién instalada.
5. Ve a **Configuración → Dispositivos y servicios → Añadir integración** y busca **Blue Express Tracking**.
6. Ingresa un número de seguimiento y, opcionalmente, un nombre breve. Repite el paso 5 para otros envíos.

También se puede instalar manualmente copiando `custom_components/blueexpress_tracking/` a `/config/custom_components/blueexpress_tracking/`.

## Datos del sensor

La entidad `sensor.<nombre>_estado` expone:

| Campo | Significado |
|---|---|
| Estado | Etapa actual según Blue Express |
| `tracking_number` | Número del envío |
| `promise_date` | Fecha máxima publicada (`YYYY-MM-DD`); **no garantiza entrega** |
| `last_movement` | Fecha/hora del último movimiento |
| `event_count` | Cantidad de eventos con descripción |
| `events` | Eventos ordenados del más reciente al más antiguo (`time`, `title`, `location`) |
| `fetched_at` | Última consulta exitosa (UTC) |
| `stale` | `true` si la última actualización falló |
| `source_url` | Enlace directo al seguimiento oficial |

Algunos movimientos internos no incluyen descripción; se omiten deliberadamente. El seguimiento internacional de AliExpress/Cainiao puede ofrecer más detalle antes de que Blue Express reciba el paquete en Chile.

## Privacidad y límites

Las consultas se realizan desde **tu instancia de Home Assistant** a `www.blue.cl`, usando el número de seguimiento que ingresaste. No hay servidor intermedio del proyecto, telemetría propia ni cuentas externas.

La integración procesa únicamente estado, fecha máxima, hora, código de etapa y ubicación general del evento. **No copia** nombres, teléfonos, correos ni direcciones del remitente o destinatario devueltos por el servicio. El número de seguimiento queda en la configuración local de Home Assistant y puede verse en atributos y registros de la entidad.

- Se hacen como máximo dos solicitudes por paquete cada 30 minutos, salvo una actualización manual iniciada por el usuario o reinicio/configuración inicial.
- Un HTTP 403/429, un timeout o un cambio en el JSON deja el valor anterior marcado como obsoleto; no es una confirmación de entrega.
- No realiza acciones de reparto ni cambia direcciones.
- Si Blue Express limita el acceso automatizado, no se deben eludir controles ni aumentar la frecuencia para sortear la restricción.

## Compatibility / Compatibilidad

Desarrollado para **Home Assistant 2026.10+** y Python del entorno que incorpora Home Assistant. Es una integración en desarrollo comunitario: verificarla primero con un número propio y revisar las incidencias.

## Desarrollo y pruebas

```bash
python -m pip install aiohttp
python -m unittest discover -s tests -v
```

Se ejecutan además Hassfest y HACS Action en GitHub Actions. Las pruebas unitarias usan envíos ficticios y respuestas simuladas; no dependen de ninguna cuenta personal.

## Créditos y licencia

Proyecto comunitario de **Gonzalo Umaña** (`@maniac75`). Código MIT.

Este repositorio **no incluye** números de seguimiento reales, configuraciones privadas, credenciales ni dashboards personales.

## Tarjeta opcional incluida desde v0.2.0

La integración incluye una tarjeta visual compacta **Blue Express Tracking** para
cada paquete. No requiere Parcel, 17TRACK, otro repositorio HACS ni llamadas al
rastreador desde el navegador: lee únicamente el sensor de Home Assistant.

Después de actualizar desde HACS y reiniciar Home Assistant:
1. Agrega un número de seguimiento mediante la integración.
2. Edita tu dashboard y elige **Agregar tarjeta → Blue Express Tracking**.
3. Selecciona el sensor correspondiente en el editor; el título es opcional.

La tarjeta muestra estado, fecha máxima *publicada por el transportista*
(no garantiza entrega), último evento y un historial desplegable sin eventos
internos vacíos. Respeta modo oscuro y pantallas móviles. No se añade
automáticamente a ningún dashboard existente.

El recurso JavaScript se registra automáticamente en Lovelace en modo
almacenamiento. Con `lovelace: resource_mode: yaml`, agrega manualmente
esta URL como recurso de tipo JavaScript module:

`/blueexpress_tracking/blueexpress-tracking-card.js`

Si Home Assistant indica que no encuentra la tarjeta, recarga la página,
comprueba los recursos del dashboard y limpia la caché de la aplicación.
