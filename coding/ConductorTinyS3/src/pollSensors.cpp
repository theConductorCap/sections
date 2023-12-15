/*pollSensors.cpp

Created May 15, 2023 by Joel Legassie

Contains functions used to gather data from MXC4005XC-B Accelerometer

void getAccAxes(uint8_t Port)   -- Controls flow of the sensor reading 
    calls:
    int16_t readAccReg(uint8_t Port, uint8_t r)  --  gets raw bits from sensor  
        calls:
            void changeI2CPort(uint8_t I2CPort) -- sets I2C port on multiplexor     
    int16_t getAxisAcc(int16_t axisHi, int16_t axisLo)  --  Create acceleration vector from raw bits (incl time data)

accVector movingAvg(uint8_t vecIndex) -- Averages three samples to create a moving average vector
vectortoBytes(accVector vector, uint8_t sensorIndex) -- makes byte array for TX

*/
// #include <Arduino.h>
// #include <WiFi.h>
#include "basic.h"
// #include <Wire.h>
// #include <stdlib.h>
// #include "secrets.h"
// #include <math.h>
// #include "Adafruit_VL53L0X.h"


/************************
 * initACC()
*************************/
void initACC() {
  Serial.println("initACC()");
  uint8_t ACCStatusReg;
  uint8_t error;
  //Initilize the MC3416 sensors
  for (int i=0; i < NUMSENSORS; i++) { //NUMSENSORS
    uint8_t portNoShift = 0;
    switch (i) {   //I2C Mux ports are not consecutive, so have to do a switch case :(
      case 0:
        portNoShift = 6;
        break;
      case 1:  
        portNoShift = 0;
        break;
      case 2:
        portNoShift = 4;
        break;
      case 3:
        portNoShift = 5;
        break;
      default:
        portNoShift = 7;
        break;
    }
    Serial.println();
    Serial.print("Sensor ");
    Serial.println(i, DEC);
    portChanged = changeI2CPort(portNoShift);
    
    //Check the status register
    Serial.println("Checking the status register");

    Wire.beginTransmission(MC3416I2CADDR);    //Open TX with start address and stop
    Wire.write(0x05);                  //Send the register we want to read to the sensor and send a restart
    
    uint8_t error = Wire.endTransmission(0);  // Send the bytes with an restart
        if (error != 0) {

            Serial.print("I2C Error Requesting Status Register: ");
            Serial.println(error,HEX);
            #ifdef DEBUG
              
              Serial.print("I2C Error: ");
              Serial.println(error,HEX);
            #endif /*DEBUG*/
            //return -1;
        }
    //Must write device address with the read bit set (ie. LSB is 1)
    Wire.requestFrom(MC3416I2CADDR, 1, 0);   //Send read request
    while(Wire.available()) {
      ACCStatusReg = Wire.read();

      Serial.print("Register Output: ");
      Serial.println(ACCStatusReg, BIN);

      #ifdef DEBUG
        Serial.print("Register Output: ");
        Serial.println(regOut, HEX);
      #endif /*DEBUG*/
    }

     //Set mode
    Serial.println("Set mode to Wake");
    Wire.beginTransmission(MC3416I2CADDR);    //Open TX with start address and stop
    Wire.write(0x07);                  //mode register 0x07
    Wire.write(0x01);                  //Send 0x01 for watch dog and interrupt disabled, mode = WAKE

    error = Wire.endTransmission();  //Send a stop
      if (error != 0) {
          Serial.println("I2C Error writing to Mode Register on I2c port");
          Serial.print("I2C Error: ");
          Serial.println(error,HEX);
          #ifdef DEBUG
            
            Serial.print("I2C Error: ");
            Serial.println(error,HEX);
          #endif /*DEBUG*/
      }

      //Read Device Status again
      Serial.println("Checking the status register again");
      Wire.beginTransmission(MC3416I2CADDR);    //Open TX with start address and stop
      Wire.write(0x05);                  //Send the register we want to read to the sensor and send a restart
  
      error = Wire.endTransmission(0);  // Send the bytes with an restart
     if (error != 0) {

            Serial.print("I2C Error Requesting Status Register: ");
            Serial.println(error,HEX);
            #ifdef DEBUG
              
              Serial.print("I2C Error: ");
              Serial.println(error,HEX);
            #endif /*DEBUG*/
            //return -1;
        }
  //Must write device address with the read bit set (ie. LSB is 1)
    Wire.requestFrom(MC3416I2CADDR, 1, 0);   //Send read request
    while(Wire.available()) {
      ACCStatusReg = Wire.read();

      Serial.print("Register Output After: ");
      Serial.println(ACCStatusReg, BIN);

      #ifdef DEBUG
        Serial.print("Register Output: ");
        Serial.println(regOut, HEX);
      #endif /*DEBUG*/
    }

    //Test gettting data out of the sensor
    //Serial.println("Read X Axis data");
    int8_t ACCdatas;
    Wire.beginTransmission(MC3416I2CADDR);    //Open TX with start address and stop
      Wire.write(0x0E);                  //Send the register we want to read to the sensor and send a restart
  
      error = Wire.endTransmission(0);  // Send the bytes with an restart
      if (error != 0) {
          Serial.print("I2C Error reading from Register 0x0E (X MSB): ");
          Serial.println(error,HEX);
          #ifdef DEBUG
            
            Serial.print("I2C Error: ");
            Serial.println(error,HEX);
          #endif /*DEBUG*/
          //return -1;
      }
  //Must write device address with the read bit set (ie. LSB is 1)
    Wire.requestFrom(MC3416I2CADDR, 1, 0);   //Send read request
    while(Wire.available()) {
      ACCdatas = Wire.read();

      Serial.print("X Axis MSB 1: ");
      Serial.println(ACCdatas, DEC);

      #ifdef DEBUG
        Serial.print("Register Output: ");
        Serial.println(regOut, HEX);
      #endif /*DEBUG*/
    }
    }
  }

/************************
 * getAccAxes()
*************************/

accVector getAccAxes(uint8_t Port) {
 //Read Axes of Acc1
    Serial.print("accVector getAccAxes(), Port: ");
    Serial.println(Port, DEC);

  // Serial.println();
    
  #ifdef DEBUG
    Serial.println();
    Serial.print("accVector getAccAxes(), Port: ");
    Serial.println(Port, DEC);
  #endif /*DEBUG*/
    
    accVector accVector;

    //Get X register values
    //XHi
    int16_t XHi = readAccReg(Port, 0x0E);
    Serial.print("XHi: ");
    Serial.println(XHi, DEC);

    #ifdef DEBUG
      Serial.print("XHi: ");
      Serial.println(XHi, DEC);
    #endif /*DEBUG*/

    //XLo  
    int16_t XLo = -1; //readAccReg(Port, 0x0D);  //Just use the MSB for 1 byte
    // Serial.print("XLo: ");
    // Serial.println(XLo, DEC);

    #ifdef DEBUG
      Serial.print("XLo: ");
      Serial.println(XLo, DEC);
    #endif /*DEBUG*/

    //Combine Hi and Lo to get axis value
    //Serial.print("X: ");
    accVector.XAcc = getAxisAcc(XHi, XLo);

    #ifdef DEBUG
      Serial.print("accVector.XAcc: ");
      Serial.println(accVector.XAcc, DEC);
    #endif /*DEBUG*/

    //Get Y register values
    //YHi
    int16_t YHi = readAccReg(Port, 0x10);

     Serial.print("YHi: ");
     Serial.println(YHi, DEC);

    #ifdef DEBUG
      Serial.print("YHi: ");
      Serial.println(YHi, DEC);
    #endif /*DEBUG*/

    //YLo  
    int16_t YLo = -1; //readAccReg(Port, 0x0F);

    // Serial.print("YLo: ");
    // Serial.println(YLo, DEC);

    #ifdef DEBUG
      Serial.print("YLo: ");
      Serial.println(YLo, DEC);
    #endif /*DEBUG*/

    //Combine Hi and Lo to get axis value
    //Serial.print("Y: ");
    accVector.YAcc = getAxisAcc(YHi, YLo);

    #ifdef DEBUG
      Serial.print("accVector.YAcc: ");
      Serial.println(accVector.YAcc, DEC);
    #endif /*DEBUG*/

    //Get Z register values
    //Zi  
    int16_t ZHi = readAccReg(Port, 0x12);

      Serial.print("ZHi: ");
      Serial.println(ZHi, DEC);
    #ifdef DEBUG
      Serial.print("ZHi: ");
      Serial.println(ZHi, DEC);
    #endif /*DEBUG*/

    //ZLo  
    int16_t ZLo = -1; //readAccReg(Port, 0x11);

    // Serial.print("ZLo: ");
    // Serial.println(ZLo, DEC);

    #ifdef DEBUG
      Serial.print("ZLo: ");
      Serial.println(ZLo, DEC);
    #endif /*DEBUG*/
    //axisAccSerial.print("Z: ");
    //Combine Hi and Lo to get axis value
    accVector.ZAcc = getAxisAcc(ZHi, ZLo);

    #ifdef DEBUG
      Serial.print("accVector.ZAcc: ");
      Serial.println(accVector.ZAcc, DEC);
    #endif /*DEBUG*/

    return accVector;
}

/****************************************
 * readAccReg(uint8_t Port, uint8_t r)
****************************************/

int8_t readAccReg(uint8_t Port, uint8_t r) {

  #ifdef DEBUG
    Serial.println();
    Serial.println("readAccReg(uint8_t Port, int r)");
    Serial.println();
    Serial.print("readAccReg(uint8_t Port, int r), TxCount:");
    Serial.println(txCount, DEC);
    Serial.print("sensor:");
    Serial.println(Port, DEC);
    Serial.print("sampleCount:");
    Serial.println(sampleCount, DEC);
    Serial.print("register:");
    Serial.println(r, DEC);
  #endif /*DEBUG*/

  int8_t regOut = 0;
  Serial.print("Port: ");
  Serial.println(Port, DEC);
  if (Port != I2CPort) {
    I2CPort = Port;
    portChanged = changeI2CPort(Port);
  }

  Serial.print("Writing to ACC Register: ");
  Serial.println(r, DEC);
  
  // Serial.println("Multiplexor Port selected");
  // Serial.println("Send Device Address then register address (r)");

  #ifdef DEBUG
    Serial.println("Multiplexor Port selected");
    Serial.println("Send Device Address then register address (r)");
  #endif /*DEBUG*/

  //  Serial.print("r transmitted: ");
  // Serial.println(r, HEX);

  #ifdef DEBUG
    Serial.print("r transmitted: ");
    Serial.println(r, HEX);
  #endif /*DEBUG*/

  Wire.beginTransmission(MC3416I2CADDR);    //Open TX with start address and stop
  Wire.write(r);                  //Send the register we want to read to the sensor
  
  uint8_t error = Wire.endTransmission(0);  // Send the bytes with an restart
  if (error != 0) {

    Serial.print("I2C Error");
    Serial.print(r, DEC);
    Serial.println(" to device");
    //Serial.println(Port, DEC);
    #ifdef DEBUG
      Serial.print("I2C device found at address 0x15\n");
    #endif /*DEBUG*/

  } 

    Wire.requestFrom(MC3416I2CADDR, 1, 0);   //Send read request
    while(Wire.available()) {
      regOut = Wire.read();

      Serial.print("Register Output: ");
      Serial.println(regOut, DEC);

      #ifdef DEBUG
        Serial.print("Register Output: ");
        Serial.println(regOut, HEX);
      #endif /*DEBUG*/
    }
    
    #ifdef DEBUG
      Serial.println();
    #endif /*DEBUG*/

    return regOut;
}

/****************************************
 * changeI2CPort(uint8_t I2CPort)
****************************************/

uint8_t changeI2CPort(uint8_t I2CPort) {   //Change the port of the I2C multiplexor
  //Serial.println();
  Serial.println("changeI2CPort()");
  Serial.print("I2CPort: ");
  Serial.println((I2CPort), DEC);
  Serial.print("I2CPort Shifted: ");
  Serial.println((1 << I2CPort), DEC);
  Wire.beginTransmission(I2CADDR);
  Wire.write(1 << I2CPort);
  //Serial.println("Hi inside");
  uint8_t error = Wire.endTransmission();
  if (error != 0) {

            Serial.print("I2C Error Chaging I2C Mux port: ");
            Serial.println(error,HEX);
            #ifdef DEBUG
              
              Serial.print("I2C Error: ");
              Serial.println(error,HEX);
            #endif /*DEBUG*/
            return -1;
        }
  //Serial.println("Hi Outside");
  return 1;

}

/********************************************
 * getAxisAcc(int16_t axisHi, int16_t axisLo)
 * Use with MC3416 Accelerometer (current version)
*********************************************/

int8_t getAxisAcc(int8_t axisHi, int8_t axisLo) {

  // Serial.println("getAxisAcc(int16_t axisHi, int16_t axisLo)");
  //   Serial.print("axisAccHi First: ");
  //   Serial.println(axisHi, DEC);
  //   Serial.print("axisAccLo First: ");
  //   Serial.println(axisLo, DEC);
  #ifdef DEBUG
    Serial.println();
    Serial.println("getAxisAcc(int16_t axisHi, int16_t axisLo)");
    Serial.print("axisAccHi First: ");
    Serial.println(axisHi, HEX);
    Serial.print("axisAccLo First: ");
    Serial.println(axisLo, HEX);
  #endif /*DEBUG*/

    // Serial.print("axisAccHi: ");
    // Serial.println(axisHi, DEC);

    // Serial.print("axisAccLo: ");
    // Serial.println(axisLo, DEC);

    int8_t axisAcc = axisHi; // + axisLo;  //Just use the MSB

    #ifdef DEBUG
      Serial.print("axisAccHi Shift: ");
      Serial.println(axisAcc, HEX);
    #endif /*DEBUG*/
    
    //axisAcc = axisAcc + axisLo;
    
    //   Serial.print("axisAcc: ");
    //   Serial.println(axisAcc, HEX);
    //   Serial.println();
    #ifdef DEBUG
      Serial.print("axisAccLo: ");
      Serial.println((axisLo >> 4), HEX);
      Serial.print("axisAcc: ");
      Serial.println(axisAcc, HEX);
      Serial.println();
    #endif /*DEBUG*/

    // Serial.print("axisAcc (16bit): ");
    // Serial.println(axisAcc, HEX);
    
    //int8_t axisAccScaled = axisAcc / 16;   //Divide 16 to reduce 12 bit signed 12 bit int (+-2047) to a signed 8bit int (+-127)

    Serial.print("axisAcc (8bit): ");
    Serial.println(axisAcc, DEC);
    Serial.println();

    return axisAcc;                  //Return single byte value
  }


/********************************************
 * getAxis12BitAcc(int16_t axisHi, int16_t axisLo)
 * Use with MXC400 Accelerometer (depreciated)
*********************************************/

int16_t getAxis12BitAcc(int16_t axisHi, int16_t axisLo) {

  // Serial.println("getAxisAcc(int16_t axisHi, int16_t axisLo)");
  //   Serial.print("axisAccHi First: ");
  //   Serial.println(axisHi, DEC);
  //   Serial.print("axisAccLo First: ");
  //   Serial.println(axisLo, DEC);
  #ifdef DEBUG
    Serial.println();
    Serial.println("getAxisAcc(int16_t axisHi, int16_t axisLo)");
    Serial.print("axisAccHi First: ");
    Serial.println(axisHi, HEX);
    Serial.print("axisAccLo First: ");
    Serial.println(axisLo, HEX);
  #endif /*DEBUG*/

    int16_t axisAcc = 0;
    if (axisHi > 127) {                  //check for negative values
        // Serial.println("************************************************************");
        // Serial.println("************************************************************");
        // Serial.print("axisHi original: ");
        // Serial.println(axisHi);
        axisHi = axisHi - 0x80;          //subtract the sign bit (128)
        // Serial.print("axisHi modified: ");
        // Serial.println(axisHi);
        axisAcc = axisHi << 4;           //High value 
        // Serial.print("axisHi shifted: ");
        // Serial.println(axisAcc);
        axisAcc = axisAcc + (axisLo >> 4);   //Low value
        axisAcc = axisAcc -2048;          //subtract 2^12 to convert 12 bit 2's complement to 16 bit signed int
        // Serial.print("Negative number: ");
        // Serial.println(axisAcc);
        // Serial.println("************************************************************");
        // Serial.println("************************************************************");
    } else {
        axisAcc = axisHi << 4;           //High value 
        axisAcc = axisAcc + (axisLo >> 4);   //Low value
    }
    
    #ifdef DEBUG
      Serial.print("axisAccHi Shift: ");
      Serial.println(axisAcc, HEX);
    #endif /*DEBUG*/
    
    //axisAcc = axisAcc + (axisLo >> 4);
    
    // Serial.print("axisAccLo: ");
    //   Serial.println((axisLo >> 4), HEX);
    //   Serial.print("axisAcc: ");
    //   Serial.println(axisAcc, HEX);
    //   Serial.println();
    #ifdef DEBUG
      Serial.print("axisAccLo: ");
      Serial.println((axisLo >> 4), HEX);
      Serial.print("axisAcc: ");
      Serial.println(axisAcc, HEX);
      Serial.println();
    #endif /*DEBUG*/

    // Serial.print("axisAcc: ");
    // Serial.println(axisAcc, DEC);
    
    
    int8_t axisAccScaled = axisAcc / 16;   //Divide 16 to reduce 12 bit signed 12 bit int (+-2047) to a signed 8bit int (+-127)

    // Serial.print("axisAccScaled: ");
    // Serial.println(axisAccScaled, DEC);
    // Serial.println();

    return axisAccScaled;                  //Return single byte value
  }

/********************************************
 * vectortoBytes(accVector vector)
*********************************************/
void vectortoBytes(accVector vector, uint8_t sensorIndex) {
  // Serial.println();
  // Serial.println("VectortoBytes(accVector vector)");
  
  #ifdef DEBUG
    Serial.println();
    Serial.println("VectortoBytes(accVector vector)");
  #endif /*DEBUG*/

  //char bytes[18];
  
  // int16_t XAccTmp = vector.XAcc;
  // char* XAccBytes = (char*) &XAccTmp;

  // // Serial.print("sizeof XAccBytes: ");
  // //   Serial.println(sizeof(XAccBytes), DEC);
  // //   Serial.print(XAccBytes[0], DEC);
  // //   Serial.print(", ");
  // //   Serial.print(XAccBytes[1], DEC);
  // //   Serial.println();
  
  // #ifdef DEBUG
  //   Serial.print("sizeof XAccBytes: ");
  //   Serial.println(sizeof(XAccBytes), DEC);
  //   Serial.print(XAccBytes[0], HEX);
  //   Serial.print(", ");
  //   Serial.print(XAccBytes[1], HEX);
  //   Serial.println();
  // #endif /*DEBUG*/

  // int16_t YAccTmp = vector.YAcc;
  // char* YAccBytes = (char*) &YAccTmp;

  // #ifdef DEBUG
  //   Serial.print("sizeof YAccBytes: ");
  //   Serial.println(sizeof(YAccBytes), DEC);
  //   Serial.print(YAccBytes[0], HEX);
  //   Serial.print(", ");
  //   Serial.print(YAccBytes[1], HEX);
  //   Serial.println();
  // #endif /*DEBUG*/

  // int16_t ZAccTmp = vector.ZAcc;
  // char* ZAccBytes = (char*) &ZAccTmp;

  // #ifdef DEBUG
  //   Serial.print("sizeof ZAccBytes: ");
  //   Serial.println(sizeof(ZAccBytes), DEC);
  //   Serial.print(ZAccBytes[0], HEX);
  //   Serial.print(", ");
  //   Serial.print(ZAccBytes[1], HEX);
  //   Serial.println();
  // #endif /*DEBUG*/
  
  sensorIndex = sensorIndex*ACCPACKSIZE;
  bytes[0 + (sensorIndex)] = vector.XAcc;
  bytes[1 + (sensorIndex)] = vector.YAcc;
  bytes[2 + (sensorIndex)] = vector.ZAcc;


// Serial.println();
//   Serial.print("Bytes: ");
//   for (int i =0; i < sizeof(bytes); i++) {
//     Serial.println(bytes[i], HEX);
//   }
//   Serial.println();

#ifdef DEBUG
  Serial.println();
  Serial.print("Bytes: ");
  for (int i =0; i < sizeof(bytes); i++) {
    Serial.println(bytes[i], HEX);
  }
  Serial.println();
#endif /*DEBUG*/
}


/********************************************
 * movingAvg(uint8_t sensorIndex)
*********************************************/
accVector movingAvg(uint8_t sensorIndex) {
  
  Serial.println("movingAvg");
  //   Serial.print("TX number: ");
  //   Serial.println(txCount, DEC);
  Serial.println("Sensor: ");
  Serial.println(sensorIndex, DEC);
  #ifdef DEBUG
    Serial.println("movingAvg");
    Serial.print("TX number: ");
    Serial.println(txCount, DEC);
    Serial.println("Sensor: ");
    Serial.println(sensorIndex, DEC);
  #endif /*DEBUG*/
  //ACC Values
  accVector movingAvgVect;
  //Floats to hold intermediate values
  float Xholder = 0;
  float Yholder = 0;
  float Zholder = 0;
  //Loop through values to get total
  for (int i =0; i < MOVINGAVGSIZE; i++) {
    Xholder += (float)accVecArray[sensorIndex][i].XAcc;
    Yholder += (float)accVecArray[sensorIndex][i].YAcc; 
    Zholder += (float)accVecArray[sensorIndex][i].ZAcc;   
  }

    Serial.print("Xholder Sum: ");
    Serial.println(Xholder, DEC);
    Serial.print("Yholder Sum: ");
    Serial.println(Yholder, DEC);
    Serial.print("Zholder Sum: ");
    Serial.println(Zholder, DEC);

  #ifdef DEBUG
    Serial.print("Xholder Sum: ");
    Serial.println(Xholder, DEC);
    Serial.print("Yholder Sum: ");
    Serial.println(Yholder, DEC);
    Serial.print("Zholder Sum: ");
    Serial.println(Zholder, DEC);
  #endif /*DEBUG*/

  //divide by the number of items in the moving average
  Xholder = Xholder / MOVINGAVGSIZE;
  if (Xholder < ZEROTHRES && Xholder > -ZEROTHRES) {
    Xholder = 0.0;
  }
  Yholder = Yholder/ MOVINGAVGSIZE;
  if (Yholder < ZEROTHRES && Yholder > -ZEROTHRES) {
    Yholder = 0.0;
  }
  Zholder = Zholder/ MOVINGAVGSIZE;
  if (Zholder < ZEROTHRES && Zholder > -ZEROTHRES) {
    Zholder = 0.0;
  }

  Serial.print("Xholder Divided: ");
  Serial.println(Xholder, DEC);
  Serial.print("Yholder Divided: ");
  Serial.println(Yholder, DEC);
  Serial.print("Zholder Divided: ");
  Serial.println(Zholder, DEC);
  #ifdef DEBUG
    Serial.print("Xholder Divided: ");
    Serial.println(Xholder, DEC);
    Serial.print("Yholder Divided: ");
    Serial.println(Yholder, DEC);
    Serial.print("Zholder Divided: ");
    Serial.println(Zholder, DEC);
  #endif /*DEBUG*/

  movingAvgVect.XAcc = (int8_t)round(Xholder);
  movingAvgVect.YAcc = (int8_t)round(Yholder);
  movingAvgVect.ZAcc = (int8_t)round(Zholder);


  Serial.println(sensorIndex, DEC);
  Serial.print("movingAvgVect.XAcc: ");
  Serial.println(movingAvgVect.XAcc, DEC);
  Serial.print("movingAvgVect.YAcc: ");
  Serial.println(movingAvgVect.YAcc, DEC);
  Serial.print("movingAvgVect.ZAcc: ");
  Serial.println(movingAvgVect.ZAcc, DEC);
  
  #ifdef DEBUG
    Serial.println(sensorIndex, DEC);
    Serial.print("movingAvgVect.XAcc: ");
    Serial.println(movingAvgVect.XAcc, DEC);
    Serial.print("movingAvgVect.YAcc: ");
    Serial.println(movingAvgVect.YAcc, DEC);
    Serial.print("movingAvgVect.ZAcc: ");
    Serial.println(movingAvgVect.ZAcc, DEC);
  #endif /*DEBUG*/

  return movingAvgVect;
}

/********************************************
 * newNetConnect(uint8_t rxStr[50])
*********************************************/
uint8_t newNetConnect(uint8_t rxStr[50]) {
    
    Serial.println("newNetConnect()");
    #ifdef DEBUG
    Serial.println("newNetConnect()");
    #endif /*DEBUG*/

    if (rxStr[0] == 0x42) {
    // Serial.print("rxStr[0]: ");
    // Serial.println(rxStr[0], HEX);
    }
    uint8_t gotSSID = 0;
    uint8_t gotPSWD = 0;
    uint8_t SSIDLength = 0;
    uint8_t PSWDLength = 0;
    char tmpSSID[50];
    char tmpPSWD[50];
    for (int z = 0; z < 50; z++) {
      //Serial.print("rxStr[z]: ");
      //Serial.println(rxStr[z], HEX);
      if (gotSSID == 0) {
        // Serial.print("rxStr[z]: ");
        // Serial.println(rxStr[z], HEX);
        //Need better checking here...
        if (rxStr[z] == 0x5F && rxStr[z+1] == 0x5F && rxStr[z+2] == 0x2D && rxStr[z+3] == 0x2D && rxStr[z+4] == 0x5F && rxStr[z+5] == 0x5F) {
          Serial.println("Got SSID");
          gotSSID = 1;
          z = z + 5;
        } else {
          tmpSSID[SSIDLength] = rxStr[z];
          Serial.print("Found Character (SSID): ");
          Serial.println(rxStr[z], HEX);
          SSIDLength++;
        }
        //"__--__"
       
      } else if (gotPSWD == 0 and gotSSID == 1) {
        if (rxStr[z] == 0x5F && rxStr[z+1] == 0x5F && rxStr[z+2] == 0x2D && rxStr[z+3] == 0x2D && rxStr[z+4] == 0x5F && rxStr[z+5] == 0x5F) {
          Serial.println("Got PSWD");
          gotPSWD = 1;
          break;
        }
        else {
        tmpPSWD[PSWDLength] = rxStr[z];
        Serial.print("Found Character (PSWD)");
        Serial.println(rxStr[z], HEX);
        PSWDLength++;
        }
      }
    }
      Serial.print("SSIDLength: ");
      Serial.println(SSIDLength, DEC);
      Serial.print("PSWDLength: ");
      Serial.println(PSWDLength, DEC);
      char newSSID[SSIDLength + 1];
      char newPSWD[PSWDLength + 1];
      Serial.print("newSSID: ");

      CntInfo cntInfo;    //Structure for writing connection data to spiffs
      cntInfo.cntMode = 1;

      for (int i = 0; i < SSIDLength; i++) {
        newSSID[i] = tmpSSID[i];
        cntInfo.ssid = cntInfo.ssid + tmpSSID[i];
        Serial.print(newSSID[i]);
        //Serial.print(newSSID[i], CHAR);
      }
      Serial.println("");

      Serial.print("newPSWD: ");
      for (int j = 0; j < PSWDLength; j++) {
        newPSWD[j] = tmpPSWD[j];
        cntInfo.pswd = cntInfo.pswd + tmpPSWD[j];
        Serial.print(newPSWD[j]);
      }
      Serial.println("");

      Serial.println("Got new connection information. Reconnecting...");
      //write the new infos to spiffs sos we can connect after restart
      
      Serial.println("Write network info to Spiffs: ");
      Serial.println(cntInfo.cntMode, DEC);
      Serial.println(cntInfo.ssid);
      Serial.println(cntInfo.pswd);

      writeNetworkSpiffs(cntInfo);

      if (connectWiFi(1, newSSID, newPSWD) == 1) {
        Serial.println("Connection Successful");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
        return 1;
        
      } else {
        Serial.println("Connection Failed");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
        return -1;
      }
    }

/********************************************
 * connectWiFi(uint8_t mode, char ssid[], char pswd[])
*********************************************/
uint8_t connectWiFi(uint8_t mode, const char *ssid, const char *pswd) {
   Serial.println("");
   Serial.println("connectWiFi()");
   Serial.print("ssid: ");
   Serial.println(ssid);
   Serial.print("pswd: ");
   Serial.println(pswd);

    #ifdef DEBUG
    Serial.println("connectWiFi()");
   #endif /*DEBUG*/

  char ip[] = "0.0.0.0"; 

  if (mode == 0) {   //Ap mode (start up)
    Serial.println("Creating AP network");
    //WiFi.begin(NETWORK, PASS);
    //delay(1000);
    //Serial.print("IP: ");
    //Serial.println(WiFi.localIP());
    WiFi.softAP(ssid, pswd);
    Serial.println("Connected mode 0");
    
      // if (WiFi.getMode() == WIFI_MODE_AP) {
         
      //   Serial.println("Connected");
      Serial.println(WiFi.softAPIP());
      // } else {
      //     WiFi.mode(WIFI_AP);
      //     WiFi.softAP(ssid, pswd); 
      //     Serial.println("Connected");
      // }
  } else if (mode == 1) {
    if (WiFi.status() == WL_CONNECTED) {
      WiFi.disconnect();
      Serial.println("Disconnected");
    } 
        
        
    // } else {
    //   Serial.println("Disconnect from AP network");
    //   //WiFi.disconnect();
    //   WiFi.enableSTA(true);
      

    //   if (WiFi.getMode() == WIFI_MODE_STA) {
    //     Serial.println("Now in station mode.");
    //     WiFi.begin(NETWORK, PASS);
    //     WiFi.setAutoReconnect(true);
    //   }
    //}
    uint8_t wifiAttempts = 0;
    while(WiFi.status() != WL_CONNECTED)  {
      Serial.print("ssid: ");
      Serial.println(ssid);
      Serial.print("pswd: ");
      Serial.println(pswd);

      WiFi.begin(ssid, pswd); 

      //WiFi.begin(ssid, pswd);
      //WiFi.begin(NETWORK, PASS);
      delay(1000);
      
      wifiAttempts++; 
      //Serial.println(wifiAttempts, DEC);
        //Reset ESP32 after 12 failed connection attempts
          if (wifiAttempts > 5) {
              Serial.println("Unable to connect. Restarting");
              // if (connectWiFi(0, APssid, APpassword)) {
              //   return 1;
              //   // Serial.println("Restarting");   //Can't restart because we will loss connection info from client
              ESP.restart();
              // } else {
              return -1;
              //}
            }
      }
      Serial.println("Connected to network");
      Serial.print("IP: ");
      Serial.println(WiFi.localIP());
   }
  
  //tftWriteNetwork(ssid, mode);
  return 1;
}

/********************************************
 * tftSetup()
*********************************************/
// void tftSetup() {
//   Serial.println("tftSetup()");
//     #ifdef DEBUG
//     Serial.println("tftSetup()");
//    #endif /*DEBUG*/
//   tft.init();
//   tft.fillScreen(0xFFFF);
//   tft.setTextColor(TFT_BLACK, TFT_WHITE);
//   tft.setCursor(30,15,1);     //(Left, Top, font)
//   tft.setTextSize(2);
//   //tft.setTextFont(1);
//   tft.println("The Conductor");
//   tft.setCursor(30,30,1);
//   tft.println("-------------");
// }

// /********************************************
//  * tftWriteNetwork(char ssid[])
// *********************************************/
// void tftWriteNetwork(char ssid[], uint8_t mode) {
//   Serial.println("tftWriteNetwork()");
//     #ifdef DEBUG
//     Serial.println("tftWriteNetwork()");
//    #endif /*DEBUG*/
//   //Write the network connection data to the TFT
//   tft.setCursor(30,50,1);
//   tft.println(ssid);
//   tft.setCursor(30,75,1);
//   if (mode == 0) {  //AP Network
//     tft.println(WiFi.softAPIP());
//   } else {
//     tft.println(WiFi.localIP());
//   }
//   Serial.println("TFT written");
// }

CntInfo getNetworkSpiffs() {
  Serial.println("");
  Serial.println("getNetworkSpiffs()");
  CntInfo cntInfo;
  File file = SPIFFS.open("/cnt.txt");
  if(!file){
      Serial.println("Failed to open file for reading");
      cntInfo.cntMode = -1;
      return cntInfo;
   }  
  String modeStr;
  uint8_t county = 0;
  
  while(file.available()) {
    
    // Serial.print("Whole file: ");
    // Serial.println(file.read());
    if (county == 0) {
      modeStr = file.readStringUntil('\n');
      Serial.print("modeStr: ");
      Serial.println(modeStr);
      if (modeStr[0] == '0') {
        cntInfo.cntMode = 0;
      } else if (modeStr[0] == '1') {
        cntInfo.cntMode = 1;
      } 
      county++;
    }

    if (county == 1) {
    cntInfo.ssid = file.readStringUntil('\n');
    county++;
    } else {
      cntInfo.pswd = file.readStringUntil('\n');
    }
  }
    Serial.print("SSID: ");
    Serial.println(cntInfo.ssid);
    Serial.print("pswd: ");
    Serial.println(cntInfo.pswd);
  file.close();
  return cntInfo;
}

uint8_t writeNetworkSpiffs(CntInfo cntInfo) {
    //Get the existing info
    CntInfo oldCntInfo = getNetworkSpiffs();
    
    if (oldCntInfo.cntMode != -1) {
    File file = SPIFFS.open("/cnt.txt", FILE_WRITE);
    if(!file){
      Serial.println("Failed to open file for reading");
      return -1;
      }
    //String newInfo = cntInfo.cntMode + "/n" + cntInfo.ssid + "/n" + cntInfo.pswd + "\n";   

      file.println(cntInfo.cntMode);
      file.println(cntInfo.ssid);
      file.println(cntInfo.pswd);
      return 1; 
    } else {
      return -1;
    }
}

/********************************************
 * void testSensors()
*********************************************/
void testSensors() {
      Serial.println();
      Serial.println("****************");
      Serial.println("testSensors()");
      //Call this function in loop to see what data the sensors are producing
        uint32_t rollOver = timerRead(timer1);
        timerWrite(timer1, 0);
        //accVecArray[0][sampleCount] = getAccAxes(7); //Use when their is only one sensor. Reads the same sensor over and over
        for (uint8_t i = 0; i < NUMSENSORS; i++) {
              Serial.print("Sensor ");
              Serial.println(i, DEC);
              // Serial.print("Sensor: ");
              // Serial.println(i, DEC);
              uint8_t portNoShift = 0;
              switch (i) {   //I2C Mux ports are not consecutive, so have to do a switch case :(
                case 0:
                  portNoShift = 6;
                  break;
                case 1:
                  portNoShift = 0;
                  //portNoShift = 7;
                  break;
                case 2:
                  portNoShift = 4;
                  //portNoShift = 5;
                  break;
                case 3:
                  portNoShift = 5;
                  break;
                default:
                  portNoShift = 7;
                  break;
              }
              //For breadboard prototype - hit the sensor at port 7 NUMSENSORS times
              //portNoShift = 7;
              Serial.println("Call getAccAxes");
              
              accVecArray[i][sampleCount] = getAccAxes(portNoShift); //Cycle through each of the sensors and add their data to accVecArray an array of three bytes per sensor
             // accVecArray[1][sampleCount] = getAccAxes(2);  //Gets data from the accelerometer on I2C port 2 (SCL1 /SDA1)
              // accVecArray[2][sampleCount] = getAccAxes(1);  //Gets data from the accelerometer on I2C port 1 (SCL0 /SDA0)
              // accVecArray[3][sampleCount] = getAccAxes(2);  //Gets data from the accelerometer on I2C port 2 (SCL1 /SDA1)
            }

        if (changeI2CPort(7) == 1) {
        
            if (toF.dataReady()) {
              // new measurement for the taking!
              uint16_t dist16 = toF.distance();
            if (dist16 == -1) {
              // something went wrong!
              Serial.print(F("Couldn't get distance: "));
              Serial.println(toF.vl_status);
            } else {
            Serial.print("Distance: ");
            Serial.print(dist16);
            toF.clearInterrupt();
            }
        //       #ifdef DEBUG
        //         Serial.print("rollOver: ");
        //         Serial.println(rollOver);
        //       #endif /*DEBUG*/
          }
        }
   }
/*
MC3416 Acclerometer I2C requirements
To write to a register <ESP32>, {MC3416} 
<Start> - <7 bit device address> - <W> - {ACK} - <7 bit Register Address> - {ACK} - <Data to Write> - {ACK} - <STOP>

Write procedure is: 
Wire.beginTransmission(MC3416I2CADDR);    //Open TX with start address and stop
Wire.write(Write Register);                  //mode register 0x07
Wire.write(Write Data);                  //Send 0x01 for watch dog and interrupt disabled, mode = WAKE
Wire.endTransmission();


To Read from a register
<Start> - <7 bit device address> - <W> - {ACK} - <7 bit Register Address> - {ACK} - <Restart> <7 bit Device Address> <Read> - {ACK} - {Data to Read} <NACK> - <STOP>

Arduino wire library sends restart after a write if Wire.endTransmission(0)
So read procdedure is:
Wire.beginTransmission(MC3416I2CADDR);
Wire.write(Register);
Wire.endTransmission(0);
Wire.requestFrom(MC3416I2CADDR, 1, 1) //Sends address, waits from 1 byte and sends stop
while(Wire.available()) {
  uint8_t readData = Wire.read()
}

Data Registers:
X MSB: 0x0E
X LSB: 0x0D
Y MSB: 0x10
Y LSB: 0x0F
Z MSB: 0x12
Z LSB: 0x11




MXC4005XC-B Accelerometer I2C requirements:
The first byte transmitted by the master following a START is used to address the slave device. The first 7 bits
contain the address of the slave device, and the 8th bit is the R/W* bit (read = 1, write = 0; the asterisk indicates
active low, and is used instead of a bar). If the transmitted address matches up to that of the MXC400xXC, then the
MXC400xXC will acknowledge receipt of the address, and prepare to receive or send data.

If the master is writing to the MXC400xXC, then the next byte that the MXC400xXC receives, following the address
byte, is loaded into the address counter internal to the MXC400xXC. The contents of the address counter indicate
which register on the MXC400xXC is being accessed. If the master now wants to write data to the MXC400xXC, it
just continues to send 8-bit bytes. Each byte of data is latched into the register on the MXC400xXC that the address
counter points to. The address counter is incremented after the transmission of each byte.

If the master wants to read data from the MXC400xXC, it first needs to write the address of the register it wants to
begin reading data from to the MXC400xXC address counter. It does this by generating a START, followed by the
address byte containing the MXC400xXC address, with R/W* = 0. The next transmitted byte is then loaded into the
MXC400xXC address counter. Then, the master repeats the START condition and re-transmits the MXC400xXC
address, but this time with the R/W* bit set to 1. During the next transmission period, a byte of data from the
MXC400xXC register that is addressed by the contents of the address counter will be transmitted from the
MXC400xXC to the master. As in the case of the master writing to the MXC400xXC, the contents of the address
counter will be incremented after the transmission of each byte. 

I2C Address (7bit):
5 - 15H (0x0F)?

Addresses Register:
0x03 XOUT upper [0-7]
0x04 XOUT lower [4-7]

0x05 YOUT upper [0-7]
0x06 YOUT lower [4-7]

0x07 ZOUT upper [0-7]
0x08 ZOUT lower [4-7]

To do: debug  I2C
Get Orientation
Data design
*/