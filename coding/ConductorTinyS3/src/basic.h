//#include "Adafruit_VL53L0X.h"
//#include <TFT_eSPI.h>
//#include <AsyncElegantOTA.h>
//#include <ESPAsyncWebServer.h>
#include "secrets.h"
#include <SPIFFS.h>
#include "Adafruit_VL53L1X.h"
#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <stdlib.h>
#include <math.h>
#include <SPI.h>
#include <UMS3.h>

// ----------------------------------------------------------------------------
// Definition of macros
// ----------------------------------------------------------------------------

//#define DEBUG
#define HTTP_PORT 80
#define LOCALADDR 1
#define I2CADDR 0x70  //I2C Address for multiplexoryu6hii76ty7
#define I2C_SDA 8     //I2C pins
#define I2C_SCL 9
#define MXCI2CADDR 0x15   //I2C Address for MXC400 Accelerometer
#define MC3416I2CADDR 0x4C   //I2C Address for MC3416 Accelerometer ( 0x4C Assuming VPP is at GND on start up). ( 0x6C Assuming VPP is at VCC on start up)
#define VL53L0XADDR 0x29  //I2C Address for VL53L0X Time of flight sensor
// #define AccPort1 1        //Ports for Accelerometer 1 (for multiplexor)
// #define AccPort2 2
// #define AccPort3 3
// #define AccPort4 4
#define XOUTHI 0x03      //Registers on MXC400 Accelerometer for data output
#define XOUTLO 0x04 
#define YOUTHI 0x05 
#define YOUTLO 0x06 
#define ZOUTHI 0x07 
#define ZOUTLO 0x08 
//#define accPacketSize 500     //Size of a unit of acc samples
#define NUMSENSORS 4       //Number of sensors
#define ACCPACKSIZE 3     //Size in bytes to send a sample from 1 accelerometer
#define SOCKPACKSIZE  ACCPACKSIZE * NUMSENSORS //Total size of packet set to socket client (ACCPACKSIZE * number of sensors) 
#define MOVINGAVGSIZE 5   //Number samples to include in moving average [12.5ms * 8 = 100ms]
#define ZEROTHRES 10.0     //All sensor values between +- of this value are set to zero
#define RXMODE "byteRx"
#define TOFINTPIN 6 //Interupt pin for VL53L0X ToF sensor

///************************************
//          Data Globals
//*************************************

struct CntInfo {
    uint8_t cntMode;
    String ssid;
    String pswd;
};


// extern uint8_t state;
// extern uint8_t debug; 
struct accVector {
    int8_t XAcc;
    int8_t YAcc;
    int8_t ZAcc;
};

extern hw_timer_t * timer1;
extern uint8_t I2CPort;
extern char bytes[SOCKPACKSIZE + 1];
extern accVector accVecArray[NUMSENSORS][MOVINGAVGSIZE];
extern uint8_t txCount;
extern uint8_t sampleCount;
extern uint8_t dist;
extern uint8_t toFReady;
extern char APssid[];
extern char APpassword[];
//extern AsyncWebServer OTAserver(8080);
extern Adafruit_VL53L1X toF;  
//extern Adafruit_VL53L0X toF;
//extern VL53L0X_RangingMeasurementData_t measure;
//extern TFT_eSPI tft;
extern uint8_t byteCode;
extern uint8_t portChanged; //Used to say port has been changed successfully
extern const char *APSSID;
extern const char *APPSWD;
extern uint8_t ledColor;

///************************************
//          Global Functions
//*************************************
extern accVector getAccAxes(uint8_t Port);
extern int8_t readAccReg(uint8_t Port, uint8_t r);
extern uint8_t changeI2CPort(uint8_t I2CPort);
extern int8_t getAxisAcc(int8_t  axisHi, int8_t axisLo);
extern void vectortoBytes(accVector vector, uint8_t sensorIndex);
extern accVector movingAvg(uint8_t vecIndex);
//extern uint8_t getDist(Adafruit_VL53L0X toF);
extern uint8_t newNetConnect(uint8_t rxStr[50]);
extern uint8_t connectWiFi(uint8_t mode, const char ssid[], const char pswd[]);
//extern void tftWriteNetwork(char ssid[], uint8_t mode);
//extern void tftSetup();
extern uint8_t writeNetworkSpiffs(CntInfo cntInfo);
extern CntInfo getNetworkSpiffs();
extern void initACC();
extern void testSensors();
extern float getBatteryVoltage();
extern float getLightSensorVoltage();
extern bool getVbusPresent();
// extern void numFun();
// extern void testMC3416();


//**********************************
//           WiFI Server Globals
//**********************************
//extern AsyncWebServer server;
//extern AsyncWebSocket ws;

//extern uint8_t socketRXArr[24];
extern uint8_t socketDataIn;
