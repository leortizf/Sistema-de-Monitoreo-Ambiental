#include <WiFi.h>
#include <DHT.h>

// Configuración del sensor DHT11
#define DHTPIN 2          // Pin donde está conectado el sensor
#define DHTTYPE DHT11     // Tipo de sensor

DHT dht(DHTPIN, DHTTYPE);

// Configuración WiFi
const char* ssid = "iPhone de Lilian";       
const char* password = "Kayuko2@24"; 

// Crear servidor en el puerto 80 (HTTP)
WiFiServer server(80);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  dht.begin();
  
  // Conectar a WiFi
  Serial.println();
  Serial.print("Conectando a red WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  // Esperar a que conecte
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi conectada");
  Serial.print("Dirección IP: ");
  Serial.println(WiFi.localIP());
  
  // Iniciar servidor
  server.begin();
  Serial.println("Servidor iniciado");
}

void loop() {
  WiFiClient client = server.available(); // Esperar cliente
  
  if (client) {
    Serial.println("Cliente conectado");
    String currentLine = "";
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        Serial.write(c);
        if (c == '\n') {
          // Línea en blanco indica fin de petición HTTP
          if (currentLine.length() == 0) {
            // Leer sensor
            float h = dht.readHumidity();
            float t = dht.readTemperature();

            // Crear respuesta JSON
            String json = "{";
            json += "\"temperatura\": " + String(t, 1) + ",";
            json += "\"humedad\": " + String(h, 1);
            json += "}";
            
            // Responder al cliente con datos HTTP y JSON
            client.println("HTTP/1.1 200 OK");
            client.println("Content-Type: application/json");
            client.println("Connection: close");
            client.println();
            client.println(json);
            break;
          } else {
            currentLine = "";
          }
        } else if (c != '\r') {
          currentLine += c;
        }
      }
    }
    delay(1);
    client.stop();
    Serial.println("Cliente desconectado");
  }
}