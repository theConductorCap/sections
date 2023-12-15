ConductorTinyS3
Joel Legassie
Dec 2023
- [1 Introduction](#1-introduction)
- [2 Getting Started](#2-getting-started)
  - [2-1 Hardware](#2-1-hardware)
  - [2-2 Software Libraries](#2-2-software-libraries)
  - [2-3 WiFi](#2-3-wifi)
  - [2-4 Startup](#2-4-startup)
- [3 Data Structures](#3-data-structures)
- [4 Functions](#4-functions)
- [5 Legal Disclamer](#5-legal-disclamer)



# 1 Introduction
This firmware collects and formats data from four MC3416 accelerometers and a VL53L1X laser time of flight sensor and sends the data to a PC client application over a TCP/IP socket using WiFi.

# 2 Getting Started

## 2-1 Hardware
This firmware has been designed and tested on an Unexpected Maker TinyS3 ESP32 Dev. board. 

I full hardware Bill of Materials as well as printed circuit board and 3-D printing files for enclosures can be found here.

See Unexpected Makers getting started instructions to get your dev board setup: https://esp32s3.com/getting-started.html

Install the ESP32 arduino code base using your favorite IDE:
	
  Arduino IDE: https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html
	
  PlatformIO: https://docs.platformio.org/en/latest/boards/espressif32/esp32s3box.html

## 2-2 Software Libraries
Ensure that the following Arduino libraries are installed:
	
  adafruit/Adafruit VL53L1X@^3.1.0   https://github.com/adafruit/Adafruit_VL53L1X
	
  unexpectedmaker/UMS3 Helper@^1.0.1 https://github.com/UnexpectedMaker/esp32s3-arduino-helper

## 2-3 WiFi
Create a secrets.h file in the code directory with you WiFi connection information. The ESP32 will its own WiFi network using `APNETWORK` and `APPASS`. You can also specify an external network to connect to using `NETWORK` and `PASS`. Your secrets.h file should look like this:

```
#define NETWORK "YourWiFiNetwork"
#define PASS "NetworkPassword"

#define APNETWORK "WhateverYouWant"
#define APPASS "NoneShallPass"
```

By default the ESP32 will start up by creating the network defined by APNETWORK. The PC client (link) will provide options for connecting to the ESP32 using different networks. 

You can choose to always connect to one of the networks in your secrets.h file by replacing commenting out these lines in main.cpp:

 ```
 CntInfo cntInfo = getNetworkSpiffs();
  Serial.println(cntInfo.cntMode);
  if (cntInfo.cntMode == 1) {
    //1 means reconnect to this network
    //convert infos to char arrays
    size_t ssidLen = cntInfo.ssid.length();
    char ssidArr[ssidLen-1];
    if (cntInfo.ssid[0] == 'T' && cntInfo.ssid[1] == 'h' && cntInfo.ssid[2] == 'e' && cntInfo.ssid[3] == 'C' && cntInfo.ssid[4] == 'o' && cntInfo.ssid[5] == 'n' && cntInfo.ssid[6] == 'd' && cntInfo.ssid[7] == 'u' && cntInfo.ssid[8] == 'c') {
      Serial.println("softAp enabled");
      cntInfo.cntMode = 0;
    }

    for (uint8_t h; h < ssidLen-1; h++) {
      ssidArr[h] = cntInfo.ssid[h];
      Serial.print(ssidArr[h]);
    } 
    Serial.println(' ');
    //cntInfo.ssid.getBytes(ssidArr, ssidLen);
    size_t pswdLen = cntInfo.pswd.length();
    char pswdArr[pswdLen-1]; 
    for (uint8_t g; g < pswdLen-1; g++) {
      pswdArr[g] = cntInfo.pswd[g];
      Serial.print(pswdArr[g]);
    } 
    Serial.println(' ');
    //cntInfo.ssid.getBytes(pswdArr, pswdLen);
    connectWiFi(cntInfo.cntMode, ssidArr, pswdArr);
  } else {
    //Connect in AP mode
    cntInfo.cntMode = 0;
    // cntInfo.pswd = APPSWD;
    // cntInfo.ssid = APSSID;
    connectWiFi(0, APSSID, APPSWD);
  }
   Serial.print("WiFi.SSID()");
   Serial.println(WiFi.SSID());
   Serial.println(APSSID);
 ```

To connect to the external network replace them with: 
	`connectWiFi(1, NETWORK, PASS);`
To connect to the ESP32's network use:
	`connectWiFi(0, APSSID, APPSWD);`

## 2-4 Startup
Upload the firmware to the board using the IDE

When the ESP32 starts up the onboard LED will be red. Once the sensors and WiFi network have been 

To see debug information in the console add `#define DEBUG` to basic.h


# 3 Data Structures

`struct accVector {
    int8_t XAcc;
    int8_t YAcc;
    int8_t ZAcc;
};`

`extern char bytes[SOCKPACKSIZE + 1];`

`extern accVector accVecArray[NUMSENSORS][MOVINGAVGSIZE];`

`struct CntInfo {
    uint8_t cntMode;
    String ssid;
    String pswd;
};`

# 4 Functions

 `void initACC()`

 `accVector getAccAxes(uint8_t Port)`

 `int8_t readAccReg(uint8_t Port, uint8_t r)`

 `uint8_t changeI2CPort(uint8_t I2CPort)`

 `int8_t getAxisAcc(int8_t axisHi, int8_t axisLo)`

 `int16_t getAxis12BitAcc(int16_t axisHi, int16_t axisLo)`

 `void vectortoBytes(accVector vector, uint8_t sensorIndex)`

 `accVector movingAvg(uint8_t sensorIndex)`

 `uint8_t newNetConnect(uint8_t rxStr[50])`

 `uint8_t connectWiFi(uint8_t mode, const char *ssid, const char *pswd)`

 `CntInfo getNetworkSpiffs()`

 `uint8_t writeNetworkSpiffs(CntInfo cntInfo)`

 `void testSensors()`

 # 5 Legal Disclamer
DISCLAIMER: The code in this repository is provided "as is" without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the code or the use or other dealings in the code.