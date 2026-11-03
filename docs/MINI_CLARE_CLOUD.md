# Mini Clare en Matick Studio LM Cloud

**Origen verificado:** el usuario creó su Mini Clare en Google Drive, en la carpeta `mini-clare-patitas`; el atlas final se llama `final/spritesheet-extended.png` y mide 1536×2288 px (cuadrícula de 8 columnas y 11 filas). Su diseño es del usuario; **no se publica ni copia a este repositorio público**.

## Para mostrar al personaje original

1. Abre Matick Cloud y pulsa 🐾 **Mini Clare** en la barra lateral.
2. Pulsa **📂 Importar sprite** y selecciona el archivo `spritesheet-extended.png` en tu carpeta sincronizada de Drive, dentro de `Compartidos/mini-clare-patitas/final`.
3. Clare aparece y los botones Saludar, Brincar y Moverse ejecutan animaciones del atlas.
4. Se guarda una copia en **IndexedDB de ese navegador y origen**, si el almacenamiento está habilitado. No se envía la imagen al backend ni a GitHub; sin permisos de almacenamiento tendrás que importar de nuevo.
5. Escribe una frase y pulsa **🔊 Hablar**. Se utilizará `speechSynthesis` del navegador, prefiriendo una voz es-MX instalada. El audio es de la computadora, no una llamada a un proveedor de IA ni una clonación de voz.
6. **Leer respuestas** está apagado por defecto. Al activarlo, Clare lee únicamente las respuestas que Matick realmente haya recibido, nunca una respuesta inventada.

El botón **✕** la oculta; el botón 🐾 la muestra otra vez. Arrastra el encabezado para moverla dentro de la ventana. En ventanas pequeñas se posiciona sin cubrir completamente el chat, y si cambias tamaño vuelve a quedar dentro de sus bordes.

## Límites y privacidad

- Este módulo es un compañero **dentro de la interfaz web de Matick Cloud**, no una mascota de escritorio que se muestre sobre todas las aplicaciones ni una integración directa con el modo Live de ChatGPT.
- No puede leer por sí solo la carpeta de Drive desde el navegador: hay que importar el PNG una vez. No necesita conexión a Drive para animarse.
- La voz es la síntesis del navegador y depende de las voces instaladas, permisos y del dispositivo.
- La fuente visual es el atlas privado del usuario. Este repositorio almacena únicamente código original para animarla, sin gráficos ni archivos personales.
- El estado de las animaciones se verifica por cálculos en Node. La voz real, el sprite y la interacción deben probarse visualmente en el navegador de Windows.
- Si quieres también el modo *siempre encima de otras apps*, requiere una ventana nativa transparente opcional separada y permisos de Windows.
