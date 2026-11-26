#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

const int TRIG_PIN = 5;
const int ECHO_PIN = 6;

const int N_MUESTRAS = 13;        // 13 puntos = 12 subintervalos (par para Simpson 1/3)
const unsigned long DT_MS = 250;  // Paso h = 0.25 s

float medirDistanciaCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duracion = pulseIn(ECHO_PIN, HIGH, 30000); // Timeout 30 ms
  if (duracion == 0) return -1.0;
  return (duracion * 0.0343) / 2.0;
}

void mostrarOLED(const __FlashStringHelper* estado, float dist, int muestra = -1) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("TELEMETRIA MET. NUM."));
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

  display.setCursor(0, 18);
  display.print(F("Estado: "));
  display.println(estado);

  display.setTextSize(2);
  display.setCursor(0, 34);
  if (dist > 0) {
    display.print(dist, 1);
    display.print(F(" cm"));
  } else {
    display.print(F("--- cm"));
  }

  if (muestra >= 0) {
    display.setTextSize(1);
    display.setCursor(0, 56);
    display.print(F("Muestra: "));
    display.print(muestra);
    display.print(F("/"));
    display.print(N_MUESTRAS);
  }
  display.display();
}

void capturarRafaga() {
  Serial.println(F("START"));
  float ultimaValida = 20.0;

  for (int i = 0; i < N_MUESTRAS; i++) {
    unsigned long tInicio = millis();
    float d = medirDistanciaCm();

    if (d >= 2.0 && d <= 400.0) {
      ultimaValida = d;
    } else {
      d = ultimaValida;
    }

    float tSeg = i * (DT_MS / 1000.0);
    Serial.print(tSeg, 3);
    Serial.print(F(","));
    Serial.println(d, 3);

    mostrarOLED(F("CAPTURANDO"), d, i + 1);

    unsigned long transcurrido = millis() - tInicio;
    if (transcurrido < DT_MS) {
      delay(DT_MS - transcurrido);
    }
  }
  Serial.println(F("END"));
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("Error OLED 0x3C"));
    while (true);
  }
  mostrarOLED(F("LISTO"), 0.0);
  delay(500);
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'S' || cmd == 's') {
      capturarRafaga();
      delay(500);
      return;
    }
  }

  float d = medirDistanciaCm();
  mostrarOLED(F("EN ESPERA"), d);
  Serial.print(F("LIVE,"));
  Serial.println(d, 2);
  delay(150);
}
