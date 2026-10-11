import streamlit as st
import requests
import re
from deep_translator import GoogleTranslator, MyMemoryTranslator

# Configurar la página para usar todo el ancho de la pantalla
st.set_page_config(page_title="Letras de YouTube", layout="wide")

st.title("🎧 YouTube Lyrics & Translation")
st.write("Mira el video y lee la letra traducida al mismo tiempo.")

# 1. Leer si la extensión de Chrome nos está enviando un enlace por la URL
enlace_por_defecto = st.query_params.get("video", "")
url = st.text_input("Enlace de YouTube:", value=enlace_por_defecto)

if url:
    try:
        # Extraer el título del video usando YouTube oEmbed
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        respuesta_yt = requests.get(oembed_url).json()
        titulo_original = respuesta_yt.get("title", "")
        
        # Limpiar el título (quitar "Official Video", "(Lyrics)", etc.)
        titulo_limpio = re.sub(r'(?i)\(official.*?\)|\[.*?\]|\(lyrics.*?\)|\(audio.*?\)|- youtube', '', titulo_original).strip()
        
        # Crear 3 columnas: [Video (más ancha)] | [Inglés] | [Español]
        col_video, col_en, col_es = st.columns([2, 1.5, 1.5])
        
        with col_video:
            st.video(url)
            st.caption(f"Reproduciendo: {titulo_original}")

        with st.spinner("Buscando y traduciendo la letra completa..."):
            # Buscar la letra original en LRCLIB
            headers = {"User-Agent": "StreamlitYouTubeLyricsApp/1.0"}
            res_letra = requests.get(f"https://lrclib.net/api/search?q={titulo_limpio}", headers=headers)
            datos = res_letra.json()
            
            if res_letra.ok and len(datos) > 0 and datos[0].get("plainLyrics"):
                letra_ingles = datos[0]["plainLyrics"]
                artista = datos[0]["artistName"]
                cancion = datos[0]["trackName"]
                
                # Intentar traducir con múltiples opciones
                try:
                    # Plan A: Google Translate
                    letra_espanol = GoogleTranslator(source='en', target='es').translate(letra_ingles)
                except Exception:
                    try:
                        # Plan B: MyMemory (con límite de caracteres para evitar bloqueos)
                        fragmento = letra_ingles[:499] # MyMemory solo acepta textos cortos gratis
                        letra_espanol = MyMemoryTranslator(source='en', target='es').translate(fragmento) 
                        letra_espanol += "\n\n(⚠️ Mostrando fragmento. El servidor principal de traducción está saturado en este momento)."
                    except Exception:
                        # Plan C: Mensaje de error amigable
                        letra_espanol = "⚠️ Todos los servidores de traducción gratuitos están saturados en este momento. Por favor, intenta de nuevo más tarde."
                
                # Mostrar resultados
                with col_en:
                    st.subheader("Inglés")
                    st.write(f"**{artista} - {cancion}**")
                    st.text(letra_ingles)
                    
                with col_es:
                    st.subheader("Español")
                    st.write(f"**{artista} - {cancion}**")
                    st.text(letra_espanol)
            else:
                with col_en:
                    st.warning(f"No se encontró la letra en la base de datos para: {titulo_limpio}")
                    
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el enlace. Verifica que sea válido. Detalle: {e}")
