import serial
from DataBase.DataBase import DataBase
from sqlalchemy import select, update
from Models.Location import LocationModel
from Models.Equipment import EquipmentModel

# Simulate the equipment
equipment_id = 5

# Initialize the database
db = DataBase()
# print(f"Conectado a la base de datos: {db}")

try:
    # Open the serial port
    ser = serial.Serial("COM7", 115200, timeout=1)
    print("Conexión exitosa. Leyendo datos:")

    # Set default values
    current_lat = None
    current_lng = None

    while True:
        # Read data from the serial port
        data = ser.readline().decode("utf-8").strip()
        if data:
            # print(f"Datos recibidos del puerto serial: {data}")

            if "LAT:" in data:
                try:
                    current_lat = float(data.split(":")[1].strip())
                except ValueError:
                    print("Error procesando latitud, ignorando esta lectura.")
                    continue

            elif "LONG:" in data:
                try:
                    current_lng = float(data.split(":")[1].strip())
                except ValueError:
                    print("Error procesando longitud, ignorando esta lectura.")
                    continue

            if current_lat is not None and current_lng is not None:
                print(
                    f"Coordenadas completas: "
                    f"Latitud={current_lat}, "
                    f"Longitud={current_lng}"
                )

                # Get stored locations
                location_data = db.query(select(LocationModel)).as_dict()
                # print(f"Localizaciones obtenidas: {location_data}")

                location_found = False
                for location in location_data:
                    location_id = location["location_id"]
                    tolerance = 0.00005

                    # Validate stored location with received coordinates
                    if (
                        location["lat_min"] - tolerance
                    ) <= current_lat <= (
                        location["lat_max"] + tolerance
                    ) and (
                        location["long_min"] - tolerance
                    ) <= current_lng <= (
                        location["long_max"] + tolerance
                    ):
                        # print(
                        #     f"Localización encontrada: "
                        #     f"{location['zone_name']}"
                        # )
                        location_found = True
                        # Update stored location for the equipment
                        db.update(
                            update(EquipmentModel)
                            .where(EquipmentModel.equipment_id == equipment_id)
                            .values(location_id=location["location_id"])
                        )
                        print(
                            f"Ubicación actualizada: "
                            f"{location['location_id']}"
                        )
                        break

                if not location_found:
                    print("No se encontró una localización correspondiente.")

                current_lat = None
                current_lng = None

except serial.SerialException as e:
    print(f"Error al abrir el puerto: {e}")
except KeyboardInterrupt:
    print("Finalizando lectura.")
    ser.close()
