
// includes
#include <SoftwareSerial.h>
#include <Wire.h>
#include <string.h>


// constants
const long SERIAL_BAUD    = 19200;
const int  I2C_ADDR       = 8;
const char VERSION[]      = "0.01";
const char DESCRIPTION[]  = "VE.Direct Serial";

// globals
char g_i2cCmd[24] = {0};
char g_rxBuffer[128] = {0};

volatile long g_iVbty = 26500;          ///< Battery Voltage, [mV]
volatile long g_iVbtyNominal = 0;   ///< Battery Rated Voltage, [mV]
volatile long g_iVbtyLevel = 0;     ///< Battery Level [%]

volatile long g_iVpv = 81;           ///< Panel Voltage, [mV]
volatile long g_iIbty = 8700;          ///< Battery Current, [mA]
volatile long g_iIld = 2100;           ///< Load Current, [mA]
volatile long g_iPpv = 121;           ///< PV Power [W]
volatile long g_iPpvMax = 311;        ///< Max PV Power Today [W]
volatile long g_iChargeState = 3;   ///< current charger state


/// interrupt called when data is received via I2C
void receiveEvent(int _iRxBytes)
{
  int n = 0;
  while ( (Wire.available() > 0) &&
          (n < sizeof(g_i2cCmd)-1) )
  {
      g_i2cCmd[n] = Wire.read();
      n++;
  }

  g_i2cCmd[n] = '\0';
}

/// interrupt called when data is requested via I2C
void requestEvent()
{
  static char buf[24] = {0};
  
  if (strcmp(g_i2cCmd, "vbty") == 0)    // battery voltage
  {
      Wire.write(itoa(g_iVbty, buf, 10));
      Wire.write("mV");
  }
  else if (strcmp(g_i2cCmd, "vbty_nominal") == 0)    // battery voltage
  {
      Wire.write(itoa(g_iVbtyNominal, buf, 10));
      Wire.write("mV");
  }
  else if (strcmp(g_i2cCmd, "vbty_level") == 0)    // battery voltage
  {
      Wire.write(itoa(g_iVbtyLevel, buf, 10));
      Wire.write("%");
  }
  else if (strcmp(g_i2cCmd, "vpv") == 0)    // panel voltage
  {
      Wire.write(itoa(g_iVpv, buf, 10));
      Wire.write("mV");
  }
  else if (strcmp(g_i2cCmd, "ibty") == 0)   // battery current
  {
      Wire.write(itoa(g_iIbty, buf, 10));
      Wire.write("mA");
  }
  else if (strcmp(g_i2cCmd, "ild") == 0)   // load current
  {
      Wire.write(itoa(g_iIld, buf, 10));
      Wire.write("mA");
  }
  else if (strcmp(g_i2cCmd, "ppv") == 0)  // panel power
  {
      Wire.write(itoa(g_iPpv, buf, 10));
      Wire.write("W");
  }
  else if (strcmp(g_i2cCmd, "ppv_max") == 0)  // panel power max today
  {
      Wire.write(itoa(g_iPpvMax, buf, 10));
      Wire.write("W");
  }
  else if (strcmp(g_i2cCmd, "cs") == 0)  // panel power max today
  {
      if (g_iChargeState == 0) Wire.write("Off");
      else if (g_iChargeState == 2) Wire.write("Fault");
      else if (g_iChargeState == 3) Wire.write("Bulk");
      else if (g_iChargeState == 4) Wire.write("Absorption");
      else if (g_iChargeState == 5) Wire.write("Float");
      else Wire.write("-");
  }
  else if (strcmp(g_i2cCmd, "version") == 0)  // meter version
  {
      Wire.write(VERSION);
  }
  else if (strcmp(g_i2cCmd, "name") == 0)  // meter description
  {
      Wire.write(DESCRIPTION);
  }
  else if (strcmp(g_i2cCmd, "name") == 0)  // meter description
  {
      Wire.write(DESCRIPTION);
  }
  else
  {
      Wire.print("-");
  }
}

/// initialise peripherals
void setup() 
{
    // init serial
    Serial.begin(SERIAL_BAUD);
    Serial.setTimeout(10);

    // init I2C slave
    Wire.begin(I2C_ADDR);
    Wire.onReceive(receiveEvent);
    Wire.onRequest(requestEvent);
    Wire.setTimeout(10);
}

/// process typical battery/charge controller values
void processKeyValue(const char *_pszKey, const char *_pszValue)
{
    //Serial.print("[");
    //Serial.print(_pszKey);
    //Serial.print(" : ");
    //Serial.print(_pszValue);
    //Serial.print("]");
    
    if (strcmp(_pszKey, "V") == 0)  // battery voltage
    {
        g_iVbty = atol(_pszValue);
    }
    else if (strcmp(_pszKey, "VPV") == 0)  // panel voltage
    {
        g_iVpv = atol(_pszValue);
    }
    else if (strcmp(_pszKey, "I") == 0)  // battery current
    {
        g_iIbty = atol(_pszValue);
    }
    else if (strcmp(_pszKey, "IL") == 0)  // load current
    {
        g_iIld = atol(_pszValue);
    }
    else if (strcmp(_pszKey, "PPV") == 0)   // panel power
    {
        g_iPpv = atol(_pszValue);
    }
    else if (strcmp(_pszKey, "H21") == 0)  // max panel power today
    {
        g_iPpvMax = atol(_pszValue);       
    }
    else if (strcmp(_pszKey, "CS") == 0)  // regulator charge state
    {
        g_iChargeState = atol(_pszValue);
    }
}

/// try to read until line is idle for _uTimeOutMs, until buffer is full, or until NL or CR is received; returns immediately if no bytes available and _bCheckAvailable == true
int readln(Stream &_rSerial, char *_pBuf, unsigned int _uBufSize, unsigned long _uTimeOutMs, bool _bCheckAvailable)
{
  if ( (_bCheckAvailable == true) &&
       (_rSerial.available() == 0) )
  {
    return 0;
  }
  
  int n = 0;
  for (unsigned long t = millis(); millis() < t + _uTimeOutMs;)
  {
    if (_rSerial.available() > 0)
    {
      int ch = _rSerial.read();
          
      // stop if NL or CR characters are received
      if ( (ch == '\n') ||
           (ch == '\r') )
      {
          if (n > 0)  // ignores NL & CR if no other characters have been received
          {
            break;
          }
      }
      else
      {
        _pBuf[n] = ch;
        n++;
        
        if (n >= _uBufSize)
        {
          n--;    // wind back to make space for '\0'
          break;
        }
        else
        {
          t = millis();
        }
      }
    }
  }
  
  _pBuf[n] = '\0';
  return n;
}

/// split line into parts and process key/value pair
void processLine(const char *_pszLine, int _iLength)
{
    for (int i = 0; i < _iLength; i++)
    {
        // find label string and value
        if (g_rxBuffer[i] == '\t')
        {
            g_rxBuffer[i] = '\0';
            const char *pszLabel = g_rxBuffer;
            const char *pszValue = g_rxBuffer + i + 1;
      
            processKeyValue(pszLabel, pszValue);
            break;    
        }
    }
}


/// main loop
void loop()
{
  // read any serial data
  while (true)
  {
      int n = readln(Serial, g_rxBuffer, sizeof(g_rxBuffer), 10, true);
      if (n > 0)
      {
          //Serial.println(g_rxBuffer);
          processLine(g_rxBuffer, n);
          //Serial.println();
      }
      else
      {
          break;
      }
  }

  // process system data
  if (g_iVbty > 36000) g_iVbtyNominal = 48000;
  else if (g_iVbty > 18000) g_iVbtyNominal = 24000;
  else if (g_iVbty > 9000) g_iVbtyNominal = 12000;

  if (g_iVbtyNominal > 0)
  {
      g_iVbtyLevel = 100 * g_iVbty / g_iVbtyNominal;
  }
  else
  {
      g_iVbtyLevel = 0;
  }

  
  delay(10);
}



