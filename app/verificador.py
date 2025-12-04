import json
import base64
import os
import shutil
import billetera
from cryptography.hazmat.primitives.asymmetric import ed25519

CARPETA_INBOX = "inbox"
CARPETA_VERIFIED = "verified"
ARCHIVO_NONCES = "base_datos_nonces.json"

def cargar_tracker_nonces():
    if not os.path.exists(ARCHIVO_NONCES):
        return {}
    try:
        with open(ARCHIVO_NONCES, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_tracker_nonces(datos):
    with open(ARCHIVO_NONCES, "w") as f:
        json.dump(datos, f, indent=4)

def canonicalizar_json(datos):
    json_string = json.dumps(datos, sort_keys=True, separators=(',', ':'))
    return json_string.encode('utf-8')

def verificar_transaccion(ruta_archivo):
    print(f"Auditando archivo: {ruta_archivo}")
    
    try:
        with open(ruta_archivo, "r") as f:
            paquete = json.load(f)
        
        tx_datos = paquete["tx"]
        firma_b64 = paquete["signature_b64"]
        pubkey_b64 = paquete["pubkey_b64"]
        
        remitente = tx_datos["from"]
        nonce_entrante = tx_datos["nonce"]
  
        nonces_db = cargar_tracker_nonces()
        ultimo_nonce = nonces_db.get(remitente, -1) 
        
        if nonce_entrante <= ultimo_nonce:
            print(f"ALERTA. Replay Attack detectado.")
            print(f"El nonce {nonce_entrante} ya fue usado (último: {ultimo_nonce}).")
            return False

        bytes_publicos = base64.b64decode(pubkey_b64)
        llave_publica = ed25519.Ed25519PublicKey.from_public_bytes(bytes_publicos)
        
        direccion_calculada = billetera.generar_direccion(bytes_publicos)
        
        if direccion_calculada != remitente:
            print(f"Error. Dirección falsa. No coincide con la llave pública.")
            return False

        bytes_mensaje = canonicalizar_json(tx_datos)
        bytes_firma = base64.b64decode(firma_b64)
        
        try:
            llave_publica.verify(bytes_firma, bytes_mensaje)
        except:
            print("Error. Firma criptográfica invalida.")
            return False

        print("OK. Transacción legítima y firma válida.")
        nonces_db[remitente] = nonce_entrante
        guardar_tracker_nonces(nonces_db)
        
        return True

    except Exception as e:
        print(f"Error. Archivo corrupto: {e}")
        return False

def procesar_inbox():
    resultado = {"exito": True, "mensaje": "", "procesados": 0, "validos": 0, "invalidos": 0, "error": ""}

    print("Buscando transacciones en Inbox...")
    if not os.path.exists(CARPETA_INBOX):
        os.mkdir(CARPETA_INBOX)
    if not os.path.exists(CARPETA_VERIFIED):
        os.mkdir(CARPETA_VERIFIED)

    try:
        archivos = os.listdir(CARPETA_INBOX)
        procesados = 0
        validos = 0
        invalidos = 0

        for nombre in archivos:
            if not nombre.endswith(".json"):
                continue
                
            ruta_completa = os.path.join(CARPETA_INBOX, nombre)
            es_valida = verificar_transaccion(ruta_completa)
            
            if es_valida:
                ruta_destino = os.path.join(CARPETA_VERIFIED, nombre)
                shutil.move(ruta_completa, ruta_destino)
                print(f"Movido. Archivado en Verified.")
                validos += 1
            else:
                print(f"Eliminado. El archivo inválido {nombre} será borrado.")
                os.remove(ruta_completa)
                invalidos += 1
            
            procesados += 1

        if procesados == 0:
            resultado["mensaje"] = "No hay archivos nuevos en Inbox."
            print(resultado["mensaje"])
        else:
            resultado["mensaje"] = f"Procesamiento completado.\nArchivos procesados: {procesados}\nVálidos (movidos a Verified): {validos}\nInválidos (eliminados): {invalidos}"
            print(resultado["mensaje"])
        
        resultado["procesados"] = procesados
        resultado["validos"] = validos
        resultado["invalidos"] = invalidos
        
    except Exception as e:
        resultado["exito"] = False
        resultado["error"] = f"Error durante procesamiento: {str(e)}"
        print(resultado["error"])

    return resultado

if __name__ == "__main__":
    procesar_inbox()