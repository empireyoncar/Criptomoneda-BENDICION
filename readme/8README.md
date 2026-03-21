📘 README – Sistema P2P de la Criptomoneda BENDICIÓN
Este documento resume toda la arquitectura, configuración, endpoints, flujo de compra/venta y pasos de desarrollo del módulo P2P del proyecto Criptomoneda BENDICIÓN.

Está pensado para que puedas retomar el desarrollo en cualquier momento sin perder contexto.

🧩 1. Arquitectura del Sistema P2P
El sistema P2P está compuesto por:

Componente	Descripción
p2p_server.py	Servidor Flask que expone los endpoints REST del mercado P2P.
p2p.py	Módulo que maneja la base de datos (archivos JSON).
p2p_manager.py	Lógica de negocio: crear ofertas, iniciar operaciones, finalizar operaciones.
init_p2p.sh	Script que inicializa los archivos JSON si están vacíos.
docker-compose.yml	Orquesta el contenedor P2P y monta los archivos JSON.
Frontend (JS/HTML)	Interfaz donde los usuarios ven ofertas y compran/venden.
📁 2. Estructura de archivos
Código
/p2p
 ├── p2p_server.py
 ├── p2p.py
 ├── p2p_manager.py
 ├── init_p2p.sh
 └── /db
      ├── p2p_data.json
      ├── p2p_pending.json
      └── p2p_history.json
🗄️ 3. Base de datos (JSON)
El sistema usa 3 archivos JSON persistentes:

Archivo	Contenido
p2p_data.json	Ofertas activas o bloqueadas
p2p_pending.json	Operaciones en curso
p2p_history.json	Operaciones finalizadas
Todos se inicializan como:

json
[]
🐳 4. Docker y despliegue
El contenedor P2P:

Copia init_p2p.sh dentro de la imagen

Le da permisos de ejecución

Monta los JSON como volúmenes

Arranca el servidor Flask en el puerto 9999

Para reconstruir:

bash
docker compose down
docker compose up -d --build
Ver logs:

bash
docker logs bendicion_p2p
🔥 5. Endpoints del sistema P2P
📌 Ofertas
➤ Obtener ofertas
Código
GET /mercado2p2/ofertas
➤ Crear oferta
Código
POST /mercado2p2/ofertas/agregar
Body:

json
{
  "id": 123,
  "usuario": "jonatan",
  "tipo": "venta",
  "cantidad": 100,
  "precio": 1.05,
  "min": 10,
  "max": 100,
  "pagos": ["BIZUM"],
  "comentario": "Prueba P2P",
  "fiat": "EUR"
}
📌 Operaciones
➤ Iniciar operación
Código
POST /mercado2p2/operacion/iniciar
Body:

json
{
  "oferta_id": 123,
  "comprador": "cliente1",
  "cantidad": 10
}
➤ Finalizar operación
Código
POST /mercado2p2/operacion/finalizar
Body:

json
{
  "op_id": 1773673432886,
  "completada": true
}
🔄 6. Flujo completo de compra/venta
🟩 1. El vendedor crea una oferta
Se guarda en p2p_data.json con estado "activa".

🟦 2. El comprador pulsa “Comprar”
El frontend llama a:

Código
POST /operacion/iniciar
La oferta pasa a "bloqueada".

La operación se guarda en p2p_pending.json.

🟧 3. El vendedor confirma o cancela
El frontend llama a:

Código
POST /operacion/finalizar
Si se completa:

Se descuenta la cantidad de la oferta

Si llega a 0 → se elimina

La operación pasa a p2p_history.json

Si se cancela:

La oferta vuelve a "activa"

Se elimina de pending

🖥️ 7. Frontend – Cómo funciona el botón “Comprar”
El botón llama a:

js
iniciarOperacion(ofertaId)
La función:

Pide cantidad

Obtiene el usuario

Envía el JSON al backend

Muestra el resultado

Código:

js
async function iniciarOperacion(ofertaId) {
    const oferta = ofertas.find(o => o.id === ofertaId);
    const cantidad = prompt("¿Cuánta cantidad deseas comprar?");
    const comprador = localStorage.getItem("usuario") || "anonimo";

    const body = {
        oferta_id: oferta.id,
        comprador: comprador,
        cantidad: parseFloat(cantidad)
    };

    const res = await fetch("/mercado2p2/operacion/iniciar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    const data = await res.json();
    alert(data.ok ? "Operación iniciada" : data.message);
}
🧠 8. Cosas importantes a recordar
Nunca montes init_p2p.sh como volumen (pierde permisos).

Los JSON deben existir y contener [].

El frontend debe enviar JSON válido.

Las ofertas tienen estados: activa, bloqueada.

Las operaciones tienen estados: pendiente, completada.

El backend funciona perfecto (probado con curl).

Si el frontend “no hace nada”, es porque no llama al backend.

🚀 9. Próximos pasos recomendados
Crear panel de operaciones pendientes

Crear panel de historial

Añadir notificaciones visuales

Añadir expiración automática de ofertas

Añadir autenticación real para compradores/vendedores

Mejorar UI del flujo de compra (modales, no prompts)

🏁 10. Estado actual del sistema
✔ Backend funcionando
✔ JSON persistentes
✔ Docker estable
✔ Flujo de compra funcionando
✔ Frontend ya inicia operaciones
⬜ Falta mostrar operaciones pendientes
⬜ Falta mostrar historial
⬜ Falta finalizar operaciones desde la web