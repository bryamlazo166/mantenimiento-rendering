"""
Script para inicializar clases de equipo y sus atributos técnicos
Ejecutar UNA SOLA VEZ después del primer despliegue
"""

import requests

API_BASE = "https://mantenimiento-rendering.onrender.com"

# Definición de clases y sus atributos
CLASES_EQUIPOS = [
    {
        "nombre": "Motor eléctrico",
        "familia": "Rotativo",
        "descripcion": "Motores eléctricos de inducción AC",
        "atributos": [
            {"nombre_atributo": "Potencia (HP)", "tipo_dato": "numero", "unidad": "HP", "obligatorio": True},
            {"nombre_atributo": "Tensión nominal", "tipo_dato": "numero", "unidad": "V", "obligatorio": True},
            {"nombre_atributo": "Corriente nominal", "tipo_dato": "numero", "unidad": "A", "obligatorio": True},
            {"nombre_atributo": "Frecuencia", "tipo_dato": "numero", "unidad": "Hz", "obligatorio": True},
            {"nombre_atributo": "RPM", "tipo_dato": "numero", "unidad": "RPM", "obligatorio": True},
            {"nombre_atributo": "Número de polos", "tipo_dato": "numero", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Tipo de carcasa", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Grado de protección IP", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Marca", "tipo_dato": "texto", "unidad": "", "obligatorio": True},
            {"nombre_atributo": "Modelo", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Factor de servicio", "tipo_dato": "numero", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Tipo de montaje", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
        ]
    },
    {
        "nombre": "Bomba centrífuga",
        "familia": "Rotativo",
        "descripcion": "Bombas centrífugas para líquidos",
        "atributos": [
            {"nombre_atributo": "Caudal nominal", "tipo_dato": "numero", "unidad": "m³/h", "obligatorio": True},
            {"nombre_atributo": "Altura manométrica", "tipo_dato": "numero", "unidad": "m", "obligatorio": True},
            {"nombre_atributo": "Tipo de bomba", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Diámetro succión", "tipo_dato": "numero", "unidad": "mm", "obligatorio": True},
            {"nombre_atributo": "Diámetro descarga", "tipo_dato": "numero", "unidad": "mm", "obligatorio": True},
            {"nombre_atributo": "Fluido de proceso", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Material carcasa", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Velocidad de giro", "tipo_dato": "numero", "unidad": "RPM", "obligatorio": True},
            {"nombre_atributo": "Marca", "tipo_dato": "texto", "unidad": "", "obligatorio": True},
            {"nombre_atributo": "Modelo", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
        ]
    },
    {
        "nombre": "Reductor / Gearbox",
        "familia": "Transmisión",
        "descripcion": "Reductores de velocidad y cajas de engranajes",
        "atributos": [
            {"nombre_atributo": "Relación de transmisión", "tipo_dato": "texto", "unidad": "", "obligatorio": True},
            {"nombre_atributo": "Potencia de entrada", "tipo_dato": "numero", "unidad": "HP", "obligatorio": True},
            {"nombre_atributo": "Velocidad de entrada", "tipo_dato": "numero", "unidad": "RPM", "obligatorio": True},
            {"nombre_atributo": "Velocidad de salida", "tipo_dato": "numero", "unidad": "RPM", "obligatorio": True},
            {"nombre_atributo": "Tipo de reductor", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Par nominal de salida", "tipo_dato": "numero", "unidad": "Nm", "obligatorio": False},
            {"nombre_atributo": "Sentido de giro", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Tipo de lubricante", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Marca", "tipo_dato": "texto", "unidad": "", "obligatorio": True},
            {"nombre_atributo": "Modelo", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
        ]
    },
    {
        "nombre": "Polea",
        "familia": "Transmisión",
        "descripcion": "Poleas para transmisión por correas",
        "atributos": [
            {"nombre_atributo": "Diámetro exterior", "tipo_dato": "numero", "unidad": "mm", "obligatorio": True},
            {"nombre_atributo": "Ancho de canal", "tipo_dato": "numero", "unidad": "mm", "obligatorio": False},
            {"nombre_atributo": "Tipo de perfil", "tipo_dato": "texto", "unidad": "", "obligatorio": True},
            {"nombre_atributo": "Número de canales", "tipo_dato": "numero", "unidad": "", "obligatorio": True},
            {"nombre_atributo": "Número de fajas instaladas", "tipo_dato": "numero", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Material", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
            {"nombre_atributo": "Tipo de montaje", "tipo_dato": "texto", "unidad": "", "obligatorio": False},
        ]
    },
]


def inicializar_clases():
    print("🚀 Iniciando carga de clases de equipo y atributos...")
    
    for clase_data in CLASES_EQUIPOS:
        # Extraer atributos
        atributos = clase_data.pop("atributos")
        
        # Crear clase
        print(f"\n📦 Creando clase: {clase_data['nombre']}")
        try:
            response = requests.post(f"{API_BASE}/clases/", json=clase_data)
            response.raise_for_status()
            clase = response.json()
            clase_id = clase["id"]
            print(f"   ✅ Clase creada con ID: {clase_id}")
            
            # Crear atributos de esta clase
            print(f"   📋 Creando {len(atributos)} atributos...")
            for atributo in atributos:
                atributo["clase_id"] = clase_id
                try:
                    attr_response = requests.post(f"{API_BASE}/atributos/", json=atributo)
                    attr_response.raise_for_status()
                    print(f"      ✓ {atributo['nombre_atributo']}")
                except Exception as e:
                    print(f"      ✗ Error en {atributo['nombre_atributo']}: {e}")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                print(f"   ⚠️  Ya existe (saltando)")
            else:
                print(f"   ❌ Error: {e}")
        except Exception as e:
            print(f"   ❌ Error general: {e}")
    
    print("\n✨ Inicialización completada!")


if __name__ == "__main__":
    inicializar_clases()
